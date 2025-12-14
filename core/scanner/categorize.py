#!/usr/bin/env python3
"""
Categorize from Disk
Reads tag files from disk and generates categories without loading everything into memory.
"""

import logging
from pathlib import Path
from collections import defaultdict
from core.utils.item import is_tag_reference
from core.utils.file import read_item_lines

logger = logging.getLogger(__name__)


def categorize_from_disk_tags(output_dir):
    """
    Generate categories by reading tag files from disk incrementally.
    Much more memory-efficient than loading all tags into memory.
    """
    print(f"\nPHASE 4: Dynamic Categorization (Derived from Tags) - From Disk")
    from core.utils.format import print_separator
    print_separator()
    
    output_path = Path(output_dir)
    tags_dir = output_path / 'tags'
    categories_dir = output_path / 'categories'
    by_tag_dir = categories_dir / 'by_tag'
    by_tag_dir.mkdir(parents=True, exist_ok=True)
    
    # Category rules based on tag patterns
    category_rules = {
        'c_tags': lambda tag: tag.startswith('c:'),
        'forge_ores': lambda tag: 'forge:ores' in tag or tag.startswith('forge:ores/'),
        'forge_ingots': lambda tag: 'forge:ingots' in tag or tag.startswith('forge:ingots/'),
        'minecraft_mineable': lambda tag: tag.startswith('minecraft:mineable/'),
        'forge_storage_blocks': lambda tag: 'forge:storage_blocks' in tag or tag.startswith('forge:storage_blocks/'),
        'forge_nuggets': lambda tag: 'forge:nuggets' in tag or tag.startswith('forge:nuggets/'),
        'forge_dusts': lambda tag: 'forge:dusts' in tag or tag.startswith('forge:dusts/'),
        'forge_gems': lambda tag: 'forge:gems' in tag or tag.startswith('forge:gems/'),
    }
    
    # Process tags incrementally - read one tag file at a time
    category_items = defaultdict(set)  # category -> items
    
    for tag_type_dir in sorted(tags_dir.iterdir()):
        if not tag_type_dir.is_dir():
            continue
        
        for tag_file in sorted(tag_type_dir.glob('*.txt')):
            # Extract tag name from filename
            tag_name = tag_file.stem.replace('tag_', '#').replace('_', ':')
            # Try to reconstruct full tag name (namespace:tag)
            # The file might have been sanitized, so we read the actual tag name from the directory structure
            # For now, we'll use the filename as a proxy
            
            # Read items from this tag file
            with open(tag_file, 'r', encoding='utf-8') as f:
                for line in f:
                    item = line.strip()
                    if item and not is_tag_reference(item):
                        # Apply category rules based on tag name
                        # We need to get the actual tag name - let's try to reconstruct it
                        # Actually, we can't easily get the full tag name from the sanitized filename
                        # So we'll process by reading the tag structure differently
                        pass
    
    # Read tag_to_items files and categorize based on tag names
    # Tag files have the tag name as the first line: #TAG:namespace:tag_name
    tag_to_items_dir = output_path / 'tag_to_items'
    if tag_to_items_dir.exists():
        for tag_file in sorted(tag_to_items_dir.glob('*.txt')):
            tag_name = None
            items_in_tag = []
            
            # Read first line to get tag name
            try:
                with open(tag_file, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('#TAG:'):
                        tag_name = first_line[5:]  # Remove '#TAG:' prefix
                    else:
                        # Fallback: try to reconstruct from filename
                        tag_name = tag_file.stem.replace('tag_', '#').replace('_', ':')
            except (IOError, OSError):
                continue
            
            # Read items from the file (skip the #TAG: line if present)
            # Use read_item_lines but we need to handle the special #TAG: format
            for item in read_item_lines(tag_file, skip_comments=False, skip_tag_refs=False):
                # Skip the #TAG: line itself (already processed above)
                if item.startswith('#TAG:'):
                    continue
                items_in_tag.append(item)
            
            # Apply category rules
            if tag_name:
                for category, rule in category_rules.items():
                    if rule(tag_name):
                        # Add all items from this tag to the category
                        for item in items_in_tag:
                            if not is_tag_reference(item):
                                category_items[category].add(item)
    
    # Write category files
    for category in sorted(category_items.keys()):
        category_file = by_tag_dir / f"{category}.txt"
        with open(category_file, 'w', encoding='utf-8') as f:
            for item in sorted(category_items[category]):
                f.write(f"{item}\n")
    
    print(f"Categories generated: {len(category_items)}")
    for category in sorted(category_items.keys()):
        count = len(category_items[category])
        print(f"  {category:30s}: {count:5d} items")
    
    return {'by_tag': category_items}

