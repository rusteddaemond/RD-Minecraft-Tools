#!/usr/bin/env python3
"""
Tag Scanner for Minecraft Mods
--------------------------------

Scans JAR files for item and block tags to discover all tag categories and materials.
This reveals all craftable/taggable item classes, including uncommon ones.

Scans:
- data/<namespace>/tags/items/<category>/<file>.json
- data/<namespace>/tags/blocks/<category>/<file>.json
- Optionally: recipes for tag references to find hidden categories

Usage:
    python -m tools.scanners.tag_scanner [options]
"""

from __future__ import annotations
import argparse
import sys
import zipfile
import json
import traceback
import re
import struct
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils import log
from src.file_operations import append_text_lines
from src.config_loader import load_paths_from_config, get_default_paths
from src.scanner_common import run_scanner, clean_results_simple
from src.file_operations import read_text_lines_stripped, write_text_lines
from tools.interfaces.scanner_args import add_scanner_input_args

# Common tag patterns to search for
COMMON_TAG_PATTERNS = [
    "c:dusts/{material}",
    "c:gears/{material}",
    "c:gems/{material}",
    "c:ingots/{material}",
    "c:nuggets/{material}",
    "c:ores/{material}",
    "c:plates/{material}",
    "c:raw_materials/{material}",
    "c:rods/{material}",
    "c:storage_blocks/raw_{material}",
    "c:storage_blocks/{material}",
    "c:wires/{material}",
    # Sapling-related patterns
    "minecraft:saplings",
    "forge:saplings",
    "c:saplings",
    "c:saplings/{material}",
    # Armor-related patterns
    "minecraft:armor",
    "forge:armor",
    "c:armor/{material}",
    "minecraft:head_armor",
    "minecraft:chest_armor",
    "minecraft:legs_armor",
    "minecraft:feet_armor",
    # Wearable/equippable patterns
    "minecraft:wearable",
    "forge:wearable",
    "c:wearable/{material}",
    "minecraft:equippable",
    "forge:equippable",
    "c:equippable/{material}",
    "minecraft:equipment",
    "forge:equipment",
    # Slot-specific patterns
    "minecraft:head",
    "minecraft:chest",
    "minecraft:legs",
    "minecraft:feet",
    "forge:head",
    "forge:chest",
    "forge:legs",
    "forge:feet",
]


def extract_items_from_tag_json(content: str) -> tuple[Set[str], Set[str]]:
    """Extract items and tag references from tag JSON content.
    
    Tag JSON files have a "values" array that can contain:
    - Item IDs: "minecraft:iron_ingot" (these are the actual items)
    - Tag references: "#c:ingots/iron" (with # prefix, these reference other tags)
    
    Args:
        content: JSON string content
        
    Returns:
        Tuple of (items, tag_references) where:
        - items: Set of item IDs found (e.g., "minecraft:iron_ingot")
        - tag_references: Set of tag references found (e.g., "c:ingots/iron", without #)
    """
    items: Set[str] = set()
    tag_refs: Set[str] = set()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Try regex fallback for malformed JSON
        # Look for item IDs (not starting with #)
        item_pattern = r'"([^#][^"]+)"'
        matches = re.findall(item_pattern, content)
        for match in matches:
            if ":" in match:  # Items have namespace:item format
                items.add(match)
        # Look for tag references (starting with #)
        tag_pattern = r'"#([^"]+)"'
        tag_matches = re.findall(tag_pattern, content)
        for match in tag_matches:
            if "/" in match:  # Tags typically have category/material format
                tag_refs.add(match)
        return items, tag_refs
    
    # Tag JSON structure: {"values": ["item:id", "#tag:ref", ...]}
    if isinstance(data, dict) and "values" in data:
        values = data["values"]
        if isinstance(values, list):
            for value in values:
                if isinstance(value, str):
                    if value.startswith("#"):
                        # Tag reference - remove # prefix
                        tag_ref = value[1:]
                        if "/" in tag_ref:  # Tags typically have category/material format
                            tag_refs.add(tag_ref)
                    elif ":" in value:
                        # Direct item
                        items.add(value)
    
    return items, tag_refs


# All possible equipment slots in Minecraft
ALL_EQUIPMENT_SLOTS = {
    # Armor slots
    "head", "chest", "legs", "feet",
    # Hand slots
    "mainhand", "offhand",
    # Body slot (some mods use this)
    "body",
    # Mod-specific slots (common ones)
    "back", "backpack", "belt", "necklace", "ring", "ring1", "ring2",
    "charm", "curio", "curios", "trinket", "trinkets",
    "shoulder", "shoulders", "cape", "cloak",
    "gloves", "hands", "wrist",
    "ankle", "ankles",
    # Slot aliases
    "helmet", "chestplate", "leggings", "boots",
    "hand", "left_hand", "right_hand"
}


def detect_equipment_slot_from_item_json(content: str, item_id: str) -> Optional[str]:
    """Detect equipment slot from item JSON model.
    
    Looks for:
    - "equipment_slot": any valid slot name
    - "overrides" with slot predicates
    - Equipment-related parent models
    
    Args:
        content: JSON string content of item model
        item_id: Item ID (namespace:item) for logging
        
    Returns:
        Slot name if equipment detected, None otherwise
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return None
    
    # Check for equipment_slot field (newer Forge/Fabric)
    if isinstance(data, dict):
        if "equipment_slot" in data:
            slot = data["equipment_slot"]
            if isinstance(slot, str) and slot.lower() in ALL_EQUIPMENT_SLOTS:
                return slot.lower()
        
        # Check for overrides with slot predicates
        if "overrides" in data and isinstance(data["overrides"], list):
            for override in data["overrides"]:
                if isinstance(override, dict) and "predicate" in override:
                    predicate = override["predicate"]
                    if isinstance(predicate, dict) and "slot" in predicate:
                        slot = predicate["slot"]
                        if isinstance(slot, str):
                            slot_lower = slot.lower()
                            # Normalize common slot names
                            slot_mapping = {
                                "helmet": "head",
                                "chestplate": "chest",
                                "leggings": "legs",
                                "boots": "feet",
                                "hand": "mainhand",
                                "left_hand": "mainhand",
                                "right_hand": "mainhand"
                            }
                            if slot_lower in slot_mapping:
                                return slot_mapping[slot_lower]
                            elif slot_lower in ALL_EQUIPMENT_SLOTS:
                                return slot_lower
        
        # Check for equipment-related parent models and infer slot
        if "parent" in data:
            parent = data["parent"]
            if isinstance(parent, str):
                parent_lower = parent.lower()
                # Armor slots
                if "helmet" in parent_lower or ("head" in parent_lower and "hand" not in parent_lower):
                    return "head"
                elif "chestplate" in parent_lower or ("chest" in parent_lower and "hand" not in parent_lower):
                    return "chest"
                elif "leggings" in parent_lower or ("legs" in parent_lower and "hand" not in parent_lower):
                    return "legs"
                elif "boots" in parent_lower or ("feet" in parent_lower or "foot" in parent_lower):
                    return "feet"
                # Hand slots
                elif "mainhand" in parent_lower or ("hand" in parent_lower and "off" not in parent_lower):
                    return "mainhand"
                elif "offhand" in parent_lower:
                    return "offhand"
                # Other equipment
                elif "backpack" in parent_lower or "back" in parent_lower:
                    return "back"
                elif "belt" in parent_lower:
                    return "belt"
                elif "ring" in parent_lower:
                    return "ring"
                elif "necklace" in parent_lower:
                    return "necklace"
                elif "curio" in parent_lower or "trinket" in parent_lower:
                    return "curio"
                elif "cape" in parent_lower or "cloak" in parent_lower:
                    return "cape"
                elif "gloves" in parent_lower or "hands" in parent_lower:
                    return "gloves"
                elif "armor" in parent_lower or "equipment" in parent_lower or "wearable" in parent_lower:
                    # Generic equipment - try to infer from item name
                    return detect_equipment_slot_from_item_name(item_id)
    
    return None


def is_trim_item(item_id: str) -> bool:
    """Check if an item is an armor trim (not actual equipment).
    
    Args:
        item_id: Item ID (namespace:item)
        
    Returns:
        True if item is a trim variant, False otherwise
    """
    item_name_lower = item_id.lower()
    # Trim items end with patterns like: _amethyst_trim, _copper_trim, etc.
    trim_patterns = ["_trim", "_armor_trim"]
    return any(item_name_lower.endswith(pattern) for pattern in trim_patterns)


def detect_equipment_slot_from_item_name(item_id: str) -> Optional[str]:
    """Detect equipment slot from item name patterns.
    
    Args:
        item_id: Item ID (namespace:item)
        
    Returns:
        Slot name if detected, None otherwise
    """
    # Skip trim items - they're not actual equipment
    if is_trim_item(item_id):
        return None
    
    item_name_lower = item_id.lower()
    
    # Head slot patterns
    if any(suffix in item_name_lower for suffix in ["_helmet", "_helm", "_head", "_cap", "_crown", "_mask", "_hat", "_tiara"]):
        return "head"
    # Chest slot patterns
    elif any(suffix in item_name_lower for suffix in ["_chestplate", "_chest", "_torso", "_body", "_plate", "_armor_chest", "_cuirass"]):
        return "chest"
    # Legs slot patterns
    elif any(suffix in item_name_lower for suffix in ["_leggings", "_legs", "_pants", "_armor_legs", "_greaves"]):
        return "legs"
    # Feet slot patterns
    elif any(suffix in item_name_lower for suffix in ["_boots", "_feet", "_shoes", "_foot", "_armor_feet", "_sabaton"]):
        return "feet"
    # Hand slots
    elif any(suffix in item_name_lower for suffix in ["_mainhand", "_main_hand", "_right_hand"]):
        return "mainhand"
    elif any(suffix in item_name_lower for suffix in ["_offhand", "_off_hand", "_left_hand", "_shield"]):
        return "offhand"
    # Other equipment slots
    elif any(suffix in item_name_lower for suffix in ["_backpack", "_back", "_bag"]):
        return "back"
    elif any(suffix in item_name_lower for suffix in ["_belt", "_waist"]):
        return "belt"
    elif any(suffix in item_name_lower for suffix in ["_ring", "_band"]):
        return "ring"
    elif any(suffix in item_name_lower for suffix in ["_necklace", "_amulet", "_pendant"]):
        return "necklace"
    elif any(suffix in item_name_lower for suffix in ["_curio", "_trinket", "_charm"]):
        return "curio"
    elif any(suffix in item_name_lower for suffix in ["_cape", "_cloak", "_mantle"]):
        return "cape"
    elif any(suffix in item_name_lower for suffix in ["_gloves", "_gauntlets", "_hands"]):
        return "gloves"
    elif any(suffix in item_name_lower for suffix in ["_shoulder", "_shoulders", "_pauldrons"]):
        return "shoulder"
    elif any(suffix in item_name_lower for suffix in ["_ankle", "_ankles"]):
        return "ankle"
    
    return None


def detect_equipment_slot_from_tag_category(category: str) -> Optional[str]:
    """Detect equipment slot from tag category name.
    
    Args:
        category: Tag category name
        
    Returns:
        Slot name if detected, None otherwise
    """
    category_lower = category.lower()
    
    # Armor slots
    if "head" in category_lower or "helmet" in category_lower:
        return "head"
    elif "chest" in category_lower or "chestplate" in category_lower:
        return "chest"
    elif "legs" in category_lower or "leggings" in category_lower:
        return "legs"
    elif "feet" in category_lower or "boots" in category_lower or "boot" in category_lower:
        return "feet"
    # Hand slots
    elif "mainhand" in category_lower or ("hand" in category_lower and "off" not in category_lower):
        return "mainhand"
    elif "offhand" in category_lower:
        return "offhand"
    # Other equipment
    elif "backpack" in category_lower or "back" in category_lower:
        return "back"
    elif "belt" in category_lower:
        return "belt"
    elif "ring" in category_lower:
        return "ring"
    elif "necklace" in category_lower or "amulet" in category_lower:
        return "necklace"
    elif "curio" in category_lower or "trinket" in category_lower:
        return "curio"
    elif "cape" in category_lower or "cloak" in category_lower:
        return "cape"
    elif "gloves" in category_lower:
        return "gloves"
    elif "shoulder" in category_lower:
        return "shoulder"
    elif "ankle" in category_lower:
        return "ankle"
    elif "body" in category_lower:
        return "body"
    
    return None


def detect_armor_from_class_file(content: bytes, class_name: str) -> bool:
    """Detect if a class extends ArmorItem by parsing .class file.
    
    Checks the superclass chain for:
    - net.minecraft.world.item.ArmorItem (Forge 1.16-1.20)
    - ItemArmor (Forge 1.12)
    - net.minecraft.item.ArmorItem (Fabric/Yarn)
    
    Args:
        content: Binary content of .class file
        class_name: Class name for reference
        
    Returns:
        True if class extends ArmorItem, False otherwise
    """
    try:
        # Check magic number (0xCAFEBABE)
        if len(content) < 8 or content[0:4] != b'\xca\xfe\xba\xbe':
            return False
        
        # Parse class file structure (simplified)
        # Skip magic, version (4 bytes), constant pool
        pos = 8
        
        # Read constant pool count (2 bytes)
        if len(content) < pos + 2:
            return False
        cp_count = struct.unpack('>H', content[pos:pos+2])[0]
        pos += 2
        
        # Skip access flags, this_class, super_class (6 bytes)
        pos += 6
        
        # Read super_class index (2 bytes)
        if len(content) < pos + 2:
            return False
        super_class_idx = struct.unpack('>H', content[pos:pos+2])[0]
        
        # Check if super_class_idx points to ArmorItem in constant pool
        # This is a simplified check - full parsing would require walking the constant pool
        # For now, search for ArmorItem strings in the class file
        content_str = content.decode('utf-8', errors='ignore')
        armor_patterns = [
            b'ArmorItem',
            b'ItemArmor',
            b'net/minecraft/world/item/ArmorItem',
            b'net/minecraft/item/ArmorItem',
        ]
        
        for pattern in armor_patterns:
            if pattern in content:
                return True
        
        return False
    except Exception:
        # If parsing fails, try simple string search
        try:
            content_str = content.decode('utf-8', errors='ignore')
            armor_patterns = [
                'ArmorItem',
                'ItemArmor',
                'net/minecraft/world/item/ArmorItem',
                'net/minecraft/item/ArmorItem',
            ]
            for pattern in armor_patterns:
                if pattern in content_str:
                    return True
        except Exception:
            pass
        return False


def extract_tags_from_recipe_json(content: str) -> Set[str]:
    """Extract tag references from recipe JSON content.
    
    Searches for patterns like "tag": "<namespace>:<category>/<material>"
    to discover hidden or rare tag categories.
    
    Args:
        content: JSON string content
        
    Returns:
        Set of tag references found (e.g., "c:dusts/iron")
    """
    tags: Set[str] = set()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Try regex fallback for malformed JSON
        tag_pattern = r'"tag"\s*:\s*"([^"]+)"'
        matches = re.findall(tag_pattern, content)
        for match in matches:
            if "/" in match:  # Tags typically have category/material format
                tags.add(match)
        return tags
    
    def find_tags_recursive(obj: any) -> None:
        """Recursively search for tag references in JSON structure."""
        if isinstance(obj, dict):
            # Check for direct "tag" field
            if "tag" in obj and isinstance(obj["tag"], str):
                tag = obj["tag"]
                if "/" in tag:  # Tags typically have category/material format
                    tags.add(tag)
            # Check for "item" field that might be a tag
            if "item" in obj and isinstance(obj["item"], str) and "/" in obj["item"]:
                # Could be a tag reference (some mods use item field for tags)
                potential_tag = obj["item"]
                if ":" in potential_tag and "/" in potential_tag.split(":")[-1]:
                    tags.add(potential_tag)
            # Recursively search all values
            for value in obj.values():
                find_tags_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                find_tags_recursive(item)
    
    find_tags_recursive(data)
    return tags


def clean_tag_results(
    raw_dir: Path,
    cleaned_dir: Path,
    suffix: str,
    skip_raw: bool = False
) -> None:
    """Clean tag results by collecting items per tag category.
    
    Groups items by tag category and writes separate files like:
    - mineable.txt
    - ores.txt
    - dusts.txt
    etc.
    
    Args:
        raw_dir: Directory containing raw files (logs)
        cleaned_dir: Directory for cleaned output files (output)
        suffix: Suffix pattern to match (e.g., "_tags")
        skip_raw: If True, delete raw files after cleaning
    """
    # Structure: category -> Set[items]
    category_items: Dict[str, Set[str]] = defaultdict(set)
    
    # Collect all items from category-specific raw files
    # Files are named like: {category}_raw.txt
    for raw_file in raw_dir.glob("*_raw.txt"):
        if not raw_file.exists():
            continue
        
        # Extract category from filename: {category}_raw.txt
        category = raw_file.stem.replace("_raw", "")
        if category == "all_tags":
            continue  # Skip the old consolidated file if it exists
        
        try:
            lines = read_text_lines_stripped(raw_file)
            # Lines are in format: namespace:item
            for line in lines:
                line = line.strip()
                if line and ":" in line:
                    category_items[category].add(line)
        
        except Exception as e:
            log(f"{raw_file.name}: {e}", "ERROR CLEAN")
    
    # Write separate files for each category
    for category, items in sorted(category_items.items()):
        if not items:
            continue
        
        category_file = cleaned_dir / f"{category}.txt"
        entries = [item + "\n" for item in sorted(items)]
        write_text_lines(category_file, entries)
        log(f"{category}.txt: {len(items)} items", "CLEAN")
    
    # Write equipment items split by slot
    # Find all equipment slot files
    for raw_file in raw_dir.glob("equipment_*_raw.txt"):
        try:
            slot = raw_file.stem.replace("equipment_", "").replace("_raw", "")
            lines = read_text_lines_stripped(raw_file)
            items = set()
            for line in lines:
                line = line.strip()
                if line and ":" in line:
                    items.add(line)
            
            if items:
                slot_file = cleaned_dir / f"equipment_{slot}.txt"
                entries = [item + "\n" for item in sorted(items)]
                write_text_lines(slot_file, entries)
                log(f"equipment_{slot}.txt: {len(items)} items", "CLEAN")
        except Exception as e:
            log(f"{raw_file.name}: {e}", "ERROR CLEAN")
    
    if skip_raw:
        for raw_file in raw_dir.glob("*_raw.txt"):
            try:
                raw_file.unlink()
            except Exception:
                pass


def process_tag_jar(
    jar_path: Path,
    raw_tags_dir: Path,
    args: argparse.Namespace
) -> None:
    """Process a single JAR file and extract tag categories and materials.
    
    Args:
        jar_path: Path to the JAR file
        raw_tags_dir: Directory for raw tag outputs (logs/tags)
        args: Parsed arguments (includes scan_recipes, namespace)
    """
    try:
        # Structure: tag_id -> Set[items]
        # tag_id format: namespace:category/material
        tags_data: Dict[str, Set[str]] = defaultdict(set)
        # Structure: tag_id -> Set[tag_references]
        tag_references: Dict[str, Set[str]] = defaultdict(set)
        # Map of all tag files we've seen: tag_id -> zip_entry_name
        tag_file_map: Dict[str, str] = {}
        # Equipment items detected from JSON and class files, grouped by slot
        # Structure: slot -> Set[item_ids]
        equipment_items_by_slot: Dict[str, Set[str]] = defaultdict(set)
        
        with zipfile.ZipFile(jar_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith("/"):
                    continue
                    
                parts = name.split("/")
                
                # Must be in data namespace
                if len(parts) < 5 or parts[0] != "data":
                    continue
                
                ns = parts[1]
                
                # Apply namespace filter if specified
                namespace_filter = getattr(args, 'namespace', None)
                if namespace_filter and ns.lower() != namespace_filter.lower():
                    continue
                
                # Check for item tags: data/<namespace>/tags/items/<category>/<file>.json
                # Also check for nested categories like: data/<namespace>/tags/items/armors/<file>.json
                # Path structure: data, namespace, tags, items, category, file.json (6 parts minimum)
                # Or: data, namespace, tags, items, category, subcategory, file.json (7 parts)
                if len(parts) >= 6 and parts[2] == "tags" and parts[3] == "items" and name.endswith(".json"):
                    category = parts[4]
                    material = Path(name).stem
                    
                    # Handle nested categories (e.g., data/modid/tags/items/armors/iron.json)
                    if len(parts) >= 7:
                        # Format: category/subcategory/material
                        subcategory = parts[5]
                        full_category = f"{category}/{subcategory}"
                        tag_id = f"{ns}:{full_category}/{material}"
                    # Handle both category/material and just category (like minecraft:armor)
                    elif material and material != category:
                        tag_id = f"{ns}:{category}/{material}"
                    else:
                        # Tag file name is the same as category (e.g., data/minecraft/tags/items/armor.json)
                        tag_id = f"{ns}:{category}"
                    
                    # Read the tag JSON to extract items and tag references
                    try:
                        with zf.open(name) as f:
                            content = f.read().decode("utf-8", errors="ignore")
                        # Extract items and tag references from tag JSON structure
                        items, tag_refs = extract_items_from_tag_json(content)
                        tags_data[tag_id].update(items)
                        tag_references[tag_id].update(tag_refs)
                        tag_file_map[tag_id] = name
                    except Exception:
                        pass  # Continue if we can't read the JSON
                
                # Check for block tags: data/<namespace>/tags/blocks/<category>/<file>.json
                # Path structure: data, namespace, tags, blocks, category, file.json (6 parts minimum)
                elif len(parts) >= 6 and parts[2] == "tags" and parts[3] == "blocks" and name.endswith(".json"):
                    category = parts[4]
                    material = Path(name).stem
                    # Handle both category/material and just category
                    if material and material != category:
                        tag_id = f"{ns}:blocks/{category}/{material}"
                    else:
                        tag_id = f"{ns}:blocks/{category}"
                    
                    # Read the tag JSON to extract items and tag references
                    try:
                        with zf.open(name) as f:
                            content = f.read().decode("utf-8", errors="ignore")
                        # Extract items and tag references from tag JSON structure
                        items, tag_refs = extract_items_from_tag_json(content)
                        # For block tags, the items are block IDs, but many blocks are also items
                        # (e.g., saplings, flowers, etc.). We'll include them as-is since
                        # block IDs and item IDs are often the same in Minecraft.
                        tags_data[tag_id].update(items)
                        tag_references[tag_id].update(tag_refs)
                        tag_file_map[tag_id] = name
                    except Exception:
                        pass  # Continue if we can't read the JSON
        
        # Optionally scan recipes for tag references
        scan_recipes = getattr(args, 'scan_recipes', False)
        if scan_recipes:
            with zipfile.ZipFile(jar_path, "r") as zf:
                for name in zf.namelist():
                    if not name.endswith(".json"):
                        continue
                    
                    parts = name.split("/")
                    if len(parts) < 4 or parts[0] != "data":
                        continue
                    
                    ns = parts[1]
                    
                    # Check if it's a recipe file
                    if not parts[2].startswith("recipe"):
                        continue
                    
                    # Apply namespace filter if specified (filter by recipe namespace)
                    namespace_filter = getattr(args, 'namespace', None)
                    if namespace_filter and ns.lower() != namespace_filter.lower():
                        continue
                    
                    try:
                        with zf.open(name) as f:
                            content = f.read().decode("utf-8", errors="ignore")
                        recipe_tags = extract_tags_from_recipe_json(content)
                        
                        for tag_ref in recipe_tags:
                            # Parse tag reference: <namespace>:<category>/<material>
                            if ":" in tag_ref and "/" in tag_ref:
                                # Apply namespace filter to tag namespace if specified
                                if namespace_filter:
                                    tag_ns = tag_ref.split(":", 1)[0]
                                    if tag_ns.lower() != namespace_filter.lower():
                                        continue
                                # Note: We can't extract items from recipe tag references,
                                # we just record that this tag exists
                                if tag_ref not in tags_data:
                                    tags_data[tag_ref] = set()
                    except Exception:
                        continue
        
        # Method 1: JSON-based armor detection
        # Scan assets/<modid>/models/item/*.json for equipment_slot
        with zipfile.ZipFile(jar_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith("/") or not name.endswith(".json"):
                    continue
                
                parts = name.split("/")
                # Check for item model JSON: assets/<namespace>/models/item/<item>.json
                if len(parts) >= 5 and parts[0] == "assets" and parts[2] == "models" and parts[3] == "item":
                    ns = parts[1]
                    item_name = Path(name).stem
                    item_id = f"{ns}:{item_name}"
                    
                    # Apply namespace filter if specified
                    namespace_filter = getattr(args, 'namespace', None)
                    if namespace_filter and ns.lower() != namespace_filter.lower():
                        continue
                    
                    try:
                        with zf.open(name) as f:
                            content = f.read().decode("utf-8", errors="ignore")
                        # Skip trim items
                        if is_trim_item(item_id):
                            continue
                        
                        slot = detect_equipment_slot_from_item_json(content, item_id)
                        if slot:
                            equipment_items_by_slot[slot].add(item_id)
                        # Also try name-based detection as fallback
                        else:
                            slot = detect_equipment_slot_from_item_name(item_id)
                            if slot:
                                equipment_items_by_slot[slot].add(item_id)
                    except Exception:
                        pass
        
        # Method 2: Class-based armor detection
        # Scan .class files for ArmorItem extensions
        # Note: This is a simplified approach - full detection would require parsing class files properly
        # For now, we'll search for ArmorItem references in class files and try to extract item IDs
        with zipfile.ZipFile(jar_path, "r") as zf:
            # First, collect all item IDs from assets to match against class names
            item_ids_from_assets: Set[str] = set()
            for name in zf.namelist():
                if name.endswith("/"):
                    continue
                parts = name.split("/")
                # Get item IDs from assets/models/item/
                if len(parts) >= 5 and parts[0] == "assets" and parts[2] == "models" and parts[3] == "item":
                    ns = parts[1]
                    item_name = Path(name).stem
                    item_ids_from_assets.add(f"{ns}:{item_name}")
            
            # Now scan class files
            for name in zf.namelist():
                if not name.endswith(".class"):
                    continue
                
                parts = name.split("/")
                class_name = Path(name).stem
                
                try:
                    with zf.open(name) as f:
                        content = f.read()
                    if detect_armor_from_class_file(content, class_name):
                        # Try to match class name to item IDs from assets
                        # Many mods use naming like: IronArmorItem -> iron_armor
                        # Or: MyModArmor -> mymod:armor
                        matched = False
                        for item_id in item_ids_from_assets:
                            # Skip trim items
                            if is_trim_item(item_id):
                                continue
                            
                            # Try various matching strategies
                            item_name = item_id.split(":")[1]
                            # Check if class name contains item name or vice versa
                            if (class_name.lower().replace("item", "").replace("armor", "").replace("class", "") in item_name.lower() or
                                item_name.lower() in class_name.lower()):
                                # Try to detect slot from item name
                                slot = detect_equipment_slot_from_item_name(item_id)
                                if slot:
                                    equipment_items_by_slot[slot].add(item_id)
                                # Don't add to all slots if we can't determine - skip it
                                matched = True
                                break
                        
                        # If no match found, try to extract namespace from package
                        if not matched:
                            ns = "unknown"
                            for i, part in enumerate(parts):
                                if part in ("items", "item", "armor", "armors", "equipment"):
                                    if i > 0:
                                        for j in range(i):
                                            if parts[j] not in ("net", "com", "org", "java", "minecraft"):
                                                ns = parts[j]
                                                break
                                    break
                            
                            if ns != "unknown":
                                # Convert class name to item name (simplified)
                                item_name = class_name.lower().replace("item", "").replace("armor", "").replace("class", "")
                                if item_name:
                                    item_id = f"{ns}:{item_name}"
                                    # Try to detect slot from item name
                                    slot = detect_equipment_slot_from_item_name(item_id)
                                    if slot:
                                        equipment_items_by_slot[slot].add(item_id)
                                    # Don't add to all slots if we can't determine - skip it
                except Exception:
                    pass
        
        # Method 3: Enhanced tag-based detection
        # Also search for common tag patterns in tag files
        # Look for tags matching common patterns like "c:dusts/{material}"
        with zipfile.ZipFile(jar_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith("/") or not name.endswith(".json"):
                    continue
                    
                parts = name.split("/")
                
                # Must be in data namespace
                if len(parts) < 5 or parts[0] != "data":
                    continue
                
                # Check if it's a tag file
                if len(parts) >= 6 and parts[2] == "tags":
                    ns = parts[1]
                    tag_type = parts[3]  # "items" or "blocks"
                    category = parts[4]
                    material = Path(name).stem
                    
                    # Build tag ID
                    # Handle both category/material and just category (like minecraft:armor)
                    if tag_type == "blocks":
                        if material and material != category:
                            tag_id = f"{ns}:blocks/{category}/{material}"
                        else:
                            tag_id = f"{ns}:blocks/{category}"
                    else:
                        if material and material != category:
                            tag_id = f"{ns}:{category}/{material}"
                        else:
                            # Tag file name is the same as category (e.g., data/minecraft/tags/items/armor.json)
                            tag_id = f"{ns}:{category}"
                    
                    # Check if this tag matches any common pattern
                    matches_pattern = False
                    for pattern in COMMON_TAG_PATTERNS:
                        # Convert pattern to regex: "c:dusts/{material}" -> "^c:dusts/.+$"
                        pattern_regex = "^" + pattern.replace("{material}", ".+") + "$"
                        if re.match(pattern_regex, tag_id):
                            matches_pattern = True
                            break
                    
                    # Always process tags that match patterns (even if already processed, to ensure we get all items)
                    # Also process tags we haven't seen yet
                    # Also check if category name contains equipment/wearable keywords
                    equipment_keywords_check = [
                        "armor", "armors", "armour", "armours",
                        "wearable", "wearables", "equippable", "equippables",
                        "equipment", "equipments",
                        "head_armor", "chest_armor", "legs_armor", "feet_armor",
                        "helmet", "helmets", "chestplate", "chestplates",
                        "leggings", "boots", "boot",
                        "mainhand", "offhand", "hand", "hands",
                        "backpack", "back", "belt", "ring", "necklace",
                        "curio", "curios", "trinket", "trinkets",
                        "cape", "cloak", "gloves", "shoulder", "ankle", "body"
                    ]
                    matches_equipment_keyword = any(keyword in category.lower() for keyword in equipment_keywords_check)
                    
                    if matches_pattern or tag_id not in tags_data or matches_equipment_keyword:
                        try:
                            with zf.open(name) as f:
                                content = f.read().decode("utf-8", errors="ignore")
                            items, tag_refs = extract_items_from_tag_json(content)
                            tags_data[tag_id].update(items)
                            tag_references[tag_id].update(tag_refs)
                            tag_file_map[tag_id] = name
                        except Exception:
                            pass
        
        # Resolve tag references: follow #tag references to get actual items
        # This requires multiple passes until no new items are found
        changed = True
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            # Reopen JAR for resolving references
            with zipfile.ZipFile(jar_path, "r") as zf:
                # For each tag that has references, try to resolve them
                for tag_id, refs in list(tag_references.items()):
                    for ref in refs:
                        # Check if we have the referenced tag in our data
                        if ref in tags_data:
                            # Add items from referenced tag
                            new_items = tags_data[ref] - tags_data[tag_id]
                            if new_items:
                                tags_data[tag_id].update(new_items)
                                changed = True
                        else:
                            # Try to find the referenced tag file in the JAR
                            # ref format: namespace:category/material or namespace:category
                            if ":" in ref:
                                ref_ns, ref_path = ref.split(":", 1)
                            # Try both formats: with material and without
                            ref_tag_files = []
                            if "/" in ref_path:
                                # Format: category/material
                                ref_category, ref_material = ref_path.split("/", 1)
                                ref_tag_files.append(f"data/{ref_ns}/tags/items/{ref_category}/{ref_material}.json")
                            else:
                                # Format: category (no material, like "minecraft:armor")
                                ref_category = ref_path
                                ref_tag_files.append(f"data/{ref_ns}/tags/items/{ref_category}.json")
                            
                            # Also try block tags if item tags don't exist
                            if "/" in ref_path:
                                ref_category, ref_material = ref_path.split("/", 1)
                                ref_tag_files.append(f"data/{ref_ns}/tags/blocks/{ref_category}/{ref_material}.json")
                            else:
                                ref_category = ref_path
                                ref_tag_files.append(f"data/{ref_ns}/tags/blocks/{ref_category}.json")
                            
                            for ref_tag_file in ref_tag_files:
                                if ref_tag_file in zf.namelist():
                                    try:
                                        with zf.open(ref_tag_file) as f:
                                            content = f.read().decode("utf-8", errors="ignore")
                                        ref_items, ref_tag_refs = extract_items_from_tag_json(content)
                                        tags_data[ref].update(ref_items)
                                        tag_references[ref].update(ref_tag_refs)
                                        tag_file_map[ref] = ref_tag_file
                                        # Add items to the original tag
                                        new_items = ref_items - tags_data[tag_id]
                                        if new_items:
                                            tags_data[tag_id].update(new_items)
                                            changed = True
                                    except Exception:
                                        pass
        
        
        # Group items by category
        # Structure: category -> Set[items]
        category_items: Dict[str, Set[str]] = defaultdict(set)
        # Structure: slot -> Set[items] for equipment items
        equipment_by_slot: Dict[str, Set[str]] = defaultdict(set)
        
        # Equipment-related category names that should be split by slot
        equipment_keywords = [
            "armor", "armors", "armour", "armours",
            "wearable", "wearables", "equippable", "equippables",
            "equipment", "equipments",
            "head_armor", "chest_armor", "legs_armor", "feet_armor",
            "head_armour", "chest_armour", "legs_armour", "feet_armour",
            "head", "chest", "legs", "feet",
            "helmet", "helmets", "chestplate", "chestplates",
            "leggings", "boots", "boot",
            "head_slot", "chest_slot", "legs_slot", "feet_slot",
            "mainhand", "offhand", "hand", "hands",
            "backpack", "back", "belt", "ring", "necklace",
            "curio", "curios", "trinket", "trinkets",
            "cape", "cloak", "gloves", "shoulder", "ankle", "body"
        ]
        
        for tag_id, items in tags_data.items():
            # Extract category from tag_id
            # Format: namespace:category/material or namespace:blocks/category/material
            # Also handle tags without material: namespace:category
            if ":" in tag_id:
                tag_part = tag_id.split(":", 1)[1]  # Get part after namespace
                if "/" in tag_part:
                    if tag_part.startswith("blocks/"):
                        # Format: blocks/category/material
                        parts = tag_part.split("/", 2)
                        if len(parts) >= 2:
                            category = parts[1]  # Get category (e.g., "saplings")
                        else:
                            category = "blocks"
                    else:
                        # Format: category/material
                        category = tag_part.split("/", 1)[0]
                else:
                    # Format: category (no material, like "minecraft:armor")
                    category = tag_part
                
                # Special handling: if category is "saplings" from block tags, 
                # ensure items are added to saplings category (blocks can be items too)
                if category == "saplings" and tag_part.startswith("blocks/"):
                    # Items from block tags are already block IDs, which are often the same as item IDs
                    # Just ensure they're categorized as saplings
                    pass  # The category is already "saplings", so items will be added correctly below
                
                # Special handling: Check if any items in this tag are saplings by name
                # Some mods put saplings in other categories (like "mineable", "plants", etc.)
                for item in items:
                    if "sapling" in item.lower():
                        category_items["saplings"].add(item)
                
                # Check if this is an equipment-related category
                is_equipment_category = any(keyword in category.lower() for keyword in equipment_keywords)
                
                if is_equipment_category:
                    # Try to detect slot from category name
                    slot_from_category = detect_equipment_slot_from_tag_category(category)
                    
                    # Distribute items by slot, filtering out trim items
                    for item in items:
                        # Skip trim items - they're not actual equipment
                        if is_trim_item(item):
                            # Add trim items to a separate category
                            category_items["trims"].add(item)
                            continue
                        
                        # Try to detect slot from item name if category doesn't specify
                        slot = slot_from_category or detect_equipment_slot_from_item_name(item)
                        if slot:
                            equipment_by_slot[slot].add(item)
                        # If we can't determine slot, skip it (don't add to all slots)
                else:
                    category_items[category].update(items)
        
        # Add equipment items detected from JSON and classes (already have slots)
        # Filter out trim items here too
        for slot, items in equipment_items_by_slot.items():
            for item in items:
                if not is_trim_item(item):
                    equipment_by_slot[slot].add(item)
                else:
                    # Add trim items to trims category
                    category_items["trims"].add(item)
        
        # Fallback: Detect saplings by item/block name pattern
        # Many mods don't tag saplings properly, so we scan for items/blocks with "sapling" in the name
        # This catches saplings from vanilla Minecraft, regions unexplored, and other mods
        sapling_items: Set[str] = set()
        with zipfile.ZipFile(jar_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith("/"):
                    continue
                
                parts = name.split("/")
                # Check for item model JSON: assets/<namespace>/models/item/<item>.json
                # Also check block models: assets/<namespace>/models/block/<block>.json
                # And item textures: assets/<namespace>/textures/item/<item>.png
                # And block textures: assets/<namespace>/textures/block/<block>.png
                if len(parts) >= 5 and parts[0] == "assets":
                    ns = parts[1]
                    item_name = Path(name).stem
                    item_id = f"{ns}:{item_name}"
                    
                    # Apply namespace filter if specified
                    namespace_filter = getattr(args, 'namespace', None)
                    if namespace_filter and ns.lower() != namespace_filter.lower():
                        continue
                    
                    # Check if item/block name contains "sapling"
                    # This will catch: oak_sapling, spruce_sapling, etc.
                    if "sapling" in item_name.lower():
                        sapling_items.add(item_id)
        
        # Add detected saplings to category (they may already be there from tags, but set() handles duplicates)
        if sapling_items:
            category_items["saplings"].update(sapling_items)
        
        # Write items grouped by category to raw files
        for category, items in category_items.items():
            raw_file = raw_tags_dir / f"{category}_raw.txt"
            lines = [item + "\n" for item in sorted(items)]
            append_text_lines(raw_file, lines)
        
        # Write equipment items grouped by slot to raw files
        for slot, items in equipment_by_slot.items():
            raw_file = raw_tags_dir / f"equipment_{slot}_raw.txt"
            lines = [item + "\n" for item in sorted(items)]
            append_text_lines(raw_file, lines)
        
        # Log summary
        total_tags = len(tags_data)
        total_items = sum(len(items) for items in category_items.values())
        total_categories = len(category_items)
        total_equipment = sum(len(items) for items in equipment_by_slot.values())
        if total_tags > 0:
            log_msg = f"{jar_path.name}: {total_tags} tags, {total_categories} categories, {total_items} unique items"
            if total_equipment > 0:
                slot_counts = ", ".join([f"{slot}:{len(equipment_by_slot[slot])}" for slot in sorted(equipment_by_slot.keys()) if equipment_by_slot[slot]])
                log_msg += f", {total_equipment} equipment items ({slot_counts})"
            log(log_msg, "OK")
        else:
            log(f"{jar_path.name}: No tags found", "WARN")
        
    except zipfile.BadZipFile:
        log(f"Bad zip: {jar_path.name}", "WARN")
    except Exception as e:
        log(f"{jar_path.name}: {e}", "ERROR")
        traceback.print_exc()


def main() -> None:
    """Main entry point for tag scanner."""
    parser = argparse.ArgumentParser(
        description="Scan JAR files for item and block tags to discover all tag categories and materials",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan JARs using default paths (tags only)
  python -m tools.scanners.tag_scanner
  
  # Also scan recipes for tag references (finds hidden categories)
  python -m tools.scanners.tag_scanner --scan-recipes
  
  # Use config file for paths
  python -m tools.scanners.tag_scanner --config paths.json
  
  # Filter by namespace
  python -m tools.scanners.tag_scanner --namespace c

The scanner discovers tag categories by scanning:
- data/<namespace>/tags/items/<category>/<file>.json
- data/<namespace>/tags/blocks/<category>/<file>.json
- (optional) Recipe files for tag references

Output format: namespace:item (one per line in tag.txt)
        """
    )
    
    # Add shared scanner arguments
    add_scanner_input_args(parser)
    
    parser.add_argument(
        "--scan-recipes",
        action="store_true",
        help="Also scan recipe files for tag references to find hidden categories"
    )
    
    args = parser.parse_args()
    
    # Load paths from config
    paths = load_paths_from_config(args.config) if args.config else get_default_paths()
    
    # Run scanner with custom processing function
    run_scanner(
        category="tags",
        category_suffix="_tags",
        entry_filter=None,  # Not used for tags (custom process_jar_func handles it)
        description="tag categories and materials",
        args=args,
        paths=paths,
        clean_func=clean_tag_results,
        process_jar_func=process_tag_jar
    )


if __name__ == "__main__":
    main()
