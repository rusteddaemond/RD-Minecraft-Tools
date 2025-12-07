"""Equipment detection functionality for tag scanning.

This module provides classes and functions for detecting equipment items
and their slots from various sources (JSON models, class files, names, categories).
"""

from __future__ import annotations
import json
import struct
from typing import Optional

from .constants import ALL_EQUIPMENT_SLOTS


class EquipmentDetector:
    """Detects equipment items and their slots from various sources."""
    
    def is_trim_item(self, item_id: str) -> bool:
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
    
    def detect_from_json(self, content: str, item_id: str) -> Optional[str]:
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
                        return self.detect_from_name(item_id)
        
        return None
    
    def detect_from_name(self, item_id: str) -> Optional[str]:
        """Detect equipment slot from item name patterns.
        
        Args:
            item_id: Item ID (namespace:item)
            
        Returns:
            Slot name if detected, None otherwise
        """
        # Skip trim items - they're not actual equipment
        if self.is_trim_item(item_id):
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
    
    def detect_from_category(self, category: str) -> Optional[str]:
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
    
    def detect_from_class_file(self, content: bytes, class_name: str) -> bool:
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
