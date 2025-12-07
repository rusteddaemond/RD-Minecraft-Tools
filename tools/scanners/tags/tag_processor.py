"""Tag processing functionality for tag scanning.

This module provides classes for extracting tags from JAR files and resolving
tag references to actual items.
"""

from __future__ import annotations
import json
import re
import zipfile
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class TagData:
    """Manages tag data structures."""
    tags_data: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    tag_references: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    tag_file_map: Dict[str, str] = field(default_factory=dict)


class TagExtractor:
    """Extracts tags from JAR files."""
    
    def extract_from_tag_file(self, content: str) -> Tuple[Set[str], Set[str]]:
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
    
    def extract_from_recipe(self, content: str) -> Set[str]:
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


class TagReferenceResolver:
    """Resolves tag references to actual items."""
    
    def resolve_references(self, jar_path: Path, tag_data: TagData, max_iterations: int = 10) -> None:
        """Resolve tag references: follow #tag references to get actual items.
        
        This requires multiple passes until no new items are found.
        
        Args:
            jar_path: Path to the JAR file
            tag_data: TagData instance to resolve
            max_iterations: Maximum number of resolution iterations (prevents infinite loops)
        """
        changed = True
        iteration = 0
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            # Reopen JAR for resolving references
            with zipfile.ZipFile(jar_path, "r") as zf:
                # For each tag that has references, try to resolve them
                for tag_id, refs in list(tag_data.tag_references.items()):
                    for ref in refs:
                        # Check if we have the referenced tag in our data
                        if ref in tag_data.tags_data:
                            # Add items from referenced tag
                            new_items = tag_data.tags_data[ref] - tag_data.tags_data[tag_id]
                            if new_items:
                                tag_data.tags_data[tag_id].update(new_items)
                                changed = True
                        else:
                            # Try to find the referenced tag file in the JAR
                            # ref format: namespace:category/material or namespace:category
                            if ":" in ref:
                                ref_ns, ref_path = ref.split(":", 1)
                            else:
                                continue
                            
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
                                        extractor = TagExtractor()
                                        ref_items, ref_tag_refs = extractor.extract_from_tag_file(content)
                                        tag_data.tags_data[ref].update(ref_items)
                                        tag_data.tag_references[ref].update(ref_tag_refs)
                                        tag_data.tag_file_map[ref] = ref_tag_file
                                        # Add items to the original tag
                                        new_items = ref_items - tag_data.tags_data[tag_id]
                                        if new_items:
                                            tag_data.tags_data[tag_id].update(new_items)
                                            changed = True
                                    except Exception:
                                        pass
