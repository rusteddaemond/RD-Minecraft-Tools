#!/usr/bin/env python3
"""
Tag Discovery
Scans tags and writes them to disk immediately to reduce memory usage.
"""

import logging
from pathlib import Path
from collections import defaultdict
from core.utils.jar import open_jar_safe
from core.utils.json import load_json_from_jar
from core.utils.item import sanitize_filename

logger = logging.getLogger(__name__)

# Batch size for processing mods to prevent too many open files
BATCH_SIZE = 64


def extract_tag_value(val):
    """Recursively extract values from tag entries."""
    if isinstance(val, str):
        return [val]
    elif isinstance(val, dict):
        result = []
        if 'id' in val:
            result.append(val['id'])
        if 'item' in val:
            result.append(val['item'])
        if 'tag' in val:
            result.append(f"#{val['tag']}")  # Mark as tag reference
        if 'values' in val:
            for nested_val in val['values']:
                result.extend(extract_tag_value(nested_val))
        return result
    elif isinstance(val, list):
        result = []
        for item in val:
            result.extend(extract_tag_value(item))
        return result
    return []


def _is_namespace_installed(namespace, mods, namespace_to_mod_map):
    """
    Check if a namespace belongs to an installed mod.
    
    Returns True if:
    - The namespace itself is a mod_id that's in the mods dict (installed mod)
    - OR the namespace is mapped to a mod_id that matches the namespace AND is in mods
    
    Returns False if:
    - The namespace is not mapped to any mod (unknown/referenced only)
    - The namespace is mapped to a different mod_id (referenced but not installed)
    - The namespace is mapped to a mod_id that's not in mods (referenced but not installed)
    """
    # First check: is the namespace itself an installed mod?
    if namespace in mods:
        return True
    
    # Second check: is the namespace mapped to itself as a mod_id that's installed?
    mod_id = namespace_to_mod_map.get(namespace)
    if mod_id:
        # Only consider it installed if the mod_id matches the namespace
        # (meaning the namespace IS the mod, not just referenced by another mod)
        return mod_id == namespace and mod_id in mods
    
    return False


def _extract_namespace_from_item(item):
    """Extract namespace from an item identifier (e.g., 'minecraft:oak_door' -> 'minecraft')."""
    if ':' in item:
        return item.split(':', 1)[0]
    return None


def discover_and_save_tags_incremental(mods, output_dir, namespace_to_mod_map=None):
    """
    Discover tags incrementally and write to disk immediately.
    Returns minimal metadata needed for categorization.
    
    Args:
        mods: Dict of mod_id -> jar_path for installed mods
        output_dir: Directory to save scan results
        namespace_to_mod_map: Optional dict mapping namespace -> mod_id
    """
    if namespace_to_mod_map is None:
        namespace_to_mod_map = {}
    
    from core.utils.format import print_separator
    print(f"\nPHASE 2: Tag Discovery (Primary Truth) - Incremental")
    print_separator()
    
    output_path = Path(output_dir)
    tags_dir = output_path / 'tags'
    tag_to_items_dir = output_path / 'tag_to_items'
    item_to_tags_dir = output_path / 'item_to_tags'
    
    # Create subdirectories for installed/not_installed
    tag_to_items_installed_dir = tag_to_items_dir / 'installed'
    tag_to_items_not_installed_dir = tag_to_items_dir / 'not_installed'
    item_to_tags_installed_dir = item_to_tags_dir / 'installed'
    item_to_tags_not_installed_dir = item_to_tags_dir / 'not_installed'
    
    tags_dir.mkdir(parents=True, exist_ok=True)
    tag_to_items_installed_dir.mkdir(parents=True, exist_ok=True)
    tag_to_items_not_installed_dir.mkdir(parents=True, exist_ok=True)
    item_to_tags_installed_dir.mkdir(parents=True, exist_ok=True)
    item_to_tags_not_installed_dir.mkdir(parents=True, exist_ok=True)
    
    # Track minimal metadata in memory (just counts and structure)
    tag_type_dirs = {}  # tag_type -> Path
    tag_counts = defaultdict(int)  # tag_type -> count
    all_tag_names = set()  # Just tag names for later processing
    item_to_tags_files = {}  # item -> file handle (kept open for current batch)
    item_to_tags_written = defaultdict(set)  # safe_item_name -> set of written tag strings (for deduplication)
    
    # Process mods in batches to prevent too many open files
    mods_list = list(mods.items())
    total_mods = len(mods_list)
    
    for batch_start in range(0, total_mods, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_mods)
        batch_mods = mods_list[batch_start:batch_end]
        batch_num = (batch_start // BATCH_SIZE) + 1
        total_batches = (total_mods + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch_mods)} mods)...")
        
        for mod_id, jar_path in batch_mods:
            print(f"Scanning tags: {mod_id}...", end=' ', flush=True)
            
            mod_tag_count = 0
            with open_jar_safe(jar_path) as jar:
                file_list = jar.namelist()
                
                for file_path in file_list:
                    if '/tags/' in file_path and file_path.endswith('.json'):
                        parts = file_path.split('/')
                        
                        try:
                            tags_index = parts.index('tags')
                            if tags_index + 2 < len(parts):
                                namespace = parts[tags_index - 1]
                                tag_type = parts[tags_index + 1]
                                tag_name = parts[-1].replace('.json', '')
                                full_tag_name = f"{namespace}:{tag_name}"
                                
                                # Create tag type directory if needed
                                if tag_type not in tag_type_dirs:
                                    tag_type_dir = tags_dir / tag_type
                                    tag_type_dir.mkdir(exist_ok=True)
                                    tag_type_dirs[tag_type] = tag_type_dir
                                
                                tag_data = load_json_from_jar(jar, file_path)
                                if tag_data:
                                    values = []
                                    if 'values' in tag_data:
                                        values = tag_data['values']
                                    elif isinstance(tag_data, list):
                                        values = tag_data
                                    
                                    # Write tag file immediately
                                    safe_tag_name = sanitize_filename(full_tag_name)
                                    tag_file = tag_type_dirs[tag_type] / f"{safe_tag_name}.txt"
                                    
                                    tag_items = set()
                                    with open(tag_file, 'w', encoding='utf-8') as f:
                                        for value in values:
                                            extracted = extract_tag_value(value)
                                            for item in extracted:
                                                if item:
                                                    f.write(f"{item}\n")
                                                    tag_items.add(item)
                                    
                                    # Write tag_to_items file immediately (separated by installed/not_installed)
                                    safe_tag_name_items = sanitize_filename(full_tag_name)
                                    # Determine if tag namespace is installed
                                    tag_is_installed = _is_namespace_installed(namespace, mods, namespace_to_mod_map)
                                    tag_items_dir = tag_to_items_installed_dir if tag_is_installed else tag_to_items_not_installed_dir
                                    tag_items_file = tag_items_dir / f"{safe_tag_name_items}.txt"
                                    with open(tag_items_file, 'w', encoding='utf-8') as f:
                                        # Write tag name as first line for reference
                                        f.write(f"#TAG:{full_tag_name}\n")
                                        for item in sorted(tag_items):
                                            f.write(f"{item}\n")
                                    
                                    # Track item_to_tags (write incrementally with cached file handles)
                                    # Separated by installed/not_installed based on item namespace
                                    tag_entry = f"{tag_type}: {full_tag_name}"
                                    for item in tag_items:
                                        clean_item = item.lstrip('#')
                                        if clean_item:
                                            safe_item_name = sanitize_filename(clean_item)
                                            
                                            # Extract namespace from item to determine if installed
                                            item_namespace = _extract_namespace_from_item(clean_item)
                                            item_is_installed = _is_namespace_installed(item_namespace, mods, namespace_to_mod_map) if item_namespace else False
                                            
                                            # Use a composite key that includes installed status
                                            item_key = (safe_item_name, item_is_installed)
                                            
                                            # Deduplication: check if this tag was already written for this item
                                            if tag_entry not in item_to_tags_written[item_key]:
                                                # Get or create file handle (reopen in append mode if needed)
                                                if item_key not in item_to_tags_files:
                                                    item_tags_dir = item_to_tags_installed_dir if item_is_installed else item_to_tags_not_installed_dir
                                                    item_file_path = item_tags_dir / f"{safe_item_name}.txt"
                                                    item_to_tags_files[item_key] = open(item_file_path, 'a', encoding='utf-8')
                                                
                                                item_to_tags_files[item_key].write(f"{tag_entry}\n")
                                                item_to_tags_written[item_key].add(tag_entry)
                                
                                all_tag_names.add(full_tag_name)
                                mod_tag_count += 1
                                tag_counts[tag_type] += 1
                        except (ValueError, IndexError) as e:
                            logger.debug(f"Failed to parse tag path {file_path}: {e}")
            
            print(f"Found {mod_tag_count} tag groups")
        
        # After each batch: flush and close all file handles
        logger.info(f"Flushing and closing all tag files after batch {batch_num}...")
        for f in item_to_tags_files.values():
            f.flush()
            f.close()
        
        # Clear file handles (will be reopened in append mode if needed in next batch)
        item_to_tags_files.clear()
        # Note: Keep item_to_tags_written to prevent duplicates across batches
    
    # Final flush and close (in case any files are still open)
    logger.info("Final flush and close of all tag files...")
    for f in item_to_tags_files.values():
        f.flush()
        f.close()
    item_to_tags_files.clear()
    
    total_tag_groups = sum(tag_counts.values())
    from core.utils.format import print_subseparator
    print_subseparator()
    print(f"Total tag groups discovered: {total_tag_groups}")
    print(f"Total unique tags: {len(all_tag_names)}")
    
    # Return minimal metadata for categorization
    return {
        'tag_types': list(tag_type_dirs.keys()),
        'tag_counts': dict(tag_counts),
        'total_tags': total_tag_groups
    }

