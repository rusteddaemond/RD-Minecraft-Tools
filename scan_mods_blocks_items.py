#!/usr/bin/env python3
"""
Simple script to scan all blocks and items from Minecraft mod JAR files in /mods directory.
This script is standalone and doesn't use any code from the codebase.
"""

import os
import json
import zipfile
from pathlib import Path


def extract_blocks_and_items_from_jar(jar_path):
    """Extract blocks and items from a single mod JAR file."""
    blocks = set()
    items = set()
    mod_name = os.path.basename(jar_path)
    
    try:
        with zipfile.ZipFile(jar_path, 'r') as jar:
            # Get all file names in the JAR
            file_list = jar.namelist()
            
            # Method 1: Look for block definitions in data/<namespace>/minecraft/block/
            for file_path in file_list:
                if '/minecraft/block/' in file_path and file_path.endswith('.json'):
                    # Extract namespace and block name
                    parts = file_path.split('/')
                    if len(parts) >= 4:
                        namespace = parts[1]  # data/<namespace>/minecraft/block/<name>.json
                        block_name = parts[-1].replace('.json', '')
                        blocks.add(f"{namespace}:{block_name}")
            
            # Method 2: Look for item definitions in data/<namespace>/minecraft/item/
            for file_path in file_list:
                if '/minecraft/item/' in file_path and file_path.endswith('.json'):
                    parts = file_path.split('/')
                    if len(parts) >= 4:
                        namespace = parts[1]  # data/<namespace>/minecraft/item/<name>.json
                        item_name = parts[-1].replace('.json', '')
                        items.add(f"{namespace}:{item_name}")
            
            # Method 3: Look for blockstate files (assets/<namespace>/blockstates/)
            for file_path in file_list:
                if '/blockstates/' in file_path and file_path.endswith('.json'):
                    parts = file_path.split('/')
                    if len(parts) >= 3:
                        namespace = parts[1]  # assets/<namespace>/blockstates/<name>.json
                        block_name = parts[-1].replace('.json', '')
                        blocks.add(f"{namespace}:{block_name}")
            
            # Method 4: Look for item model files (assets/<namespace>/models/item/)
            for file_path in file_list:
                if '/models/item/' in file_path and file_path.endswith('.json'):
                    parts = file_path.split('/')
                    if len(parts) >= 4:
                        namespace = parts[1]  # assets/<namespace>/models/item/<name>.json
                        item_name = parts[-1].replace('.json', '')
                        items.add(f"{namespace}:{item_name}")
            
            # Method 5: Try to read block/item JSON files to get more info
            for file_path in file_list:
                if ('/minecraft/block/' in file_path or '/minecraft/item/' in file_path) and file_path.endswith('.json'):
                    try:
                        with jar.open(file_path) as f:
                            content = f.read().decode('utf-8')
                            data = json.loads(content)
                            
                            # Some mods define blocks/items in JSON with "type" field
                            if isinstance(data, dict):
                                if 'type' in data:
                                    parts = file_path.split('/')
                                    if len(parts) >= 4:
                                        namespace = parts[1]
                                        name = parts[-1].replace('.json', '')
                                        if '/block/' in file_path:
                                            blocks.add(f"{namespace}:{name}")
                                        elif '/item/' in file_path:
                                            items.add(f"{namespace}:{name}")
                    except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
                        pass  # Skip invalid JSON files
            
    except (zipfile.BadZipFile, OSError) as e:
        print(f"Error reading {mod_name}: {e}")
        return blocks, items
    
    return blocks, items


def scan_mods_directory(mods_dir='mods'):
    """Scan all JAR files in the mods directory."""
    mods_path = Path(mods_dir)
    
    if not mods_path.exists():
        print(f"Error: Directory '{mods_dir}' does not exist!")
        return
    
    all_blocks = set()  # All unique blocks across all mods
    all_items = set()   # All unique items across all mods
    
    jar_files = list(mods_path.glob('*.jar'))
    
    if not jar_files:
        print(f"No JAR files found in '{mods_dir}' directory!")
        return
    
    print(f"Found {len(jar_files)} JAR file(s) to scan...")
    print("-" * 60)
    
    for jar_file in jar_files:
        mod_name = jar_file.name
        print(f"Scanning: {mod_name}...", end=' ', flush=True)
        
        blocks, items = extract_blocks_and_items_from_jar(jar_file)
        all_blocks.update(blocks)
        all_items.update(items)
        
        print(f"Found {len(blocks)} blocks, {len(items)} items")
    
    print("-" * 60)
    print(f"\nScan complete!")
    print(f"Total mods scanned: {len(jar_files)}")
    print(f"Total unique blocks found: {len(all_blocks)}")
    print(f"Total unique items found: {len(all_items)}")
    
    # Save results to files - one entry per line in format "namespace:name"
    output_dir = Path('scan_output')
    output_dir.mkdir(exist_ok=True)
    
    # Organize blocks and items by namespace
    blocks_by_namespace = {}
    items_by_namespace = {}
    
    for block in all_blocks:
        namespace = block.split(':', 1)[0]
        if namespace not in blocks_by_namespace:
            blocks_by_namespace[namespace] = []
        blocks_by_namespace[namespace].append(block)
    
    for item in all_items:
        namespace = item.split(':', 1)[0]
        if namespace not in items_by_namespace:
            items_by_namespace[namespace] = []
        items_by_namespace[namespace].append(item)
    
    # Save complete catalogues
    with open(output_dir / 'blocks.txt', 'w', encoding='utf-8') as f:
        for block in sorted(all_blocks):
            f.write(f"{block}\n")
    
    with open(output_dir / 'items.txt', 'w', encoding='utf-8') as f:
        for item in sorted(all_items):
            f.write(f"{item}\n")
    
    # Create subdirectories for namespace-specific files
    blocks_dir = output_dir / 'blocks'
    items_dir = output_dir / 'items'
    blocks_dir.mkdir(exist_ok=True)
    items_dir.mkdir(exist_ok=True)
    
    # Save blocks by namespace
    for namespace in sorted(blocks_by_namespace.keys()):
        namespace_file = blocks_dir / f"{namespace}.txt"
        with open(namespace_file, 'w', encoding='utf-8') as f:
            for block in sorted(blocks_by_namespace[namespace]):
                f.write(f"{block}\n")
    
    # Save items by namespace
    for namespace in sorted(items_by_namespace.keys()):
        namespace_file = items_dir / f"{namespace}.txt"
        with open(namespace_file, 'w', encoding='utf-8') as f:
            for item in sorted(items_by_namespace[namespace]):
                f.write(f"{item}\n")
    
    print(f"\nResults saved to '{output_dir}/' directory:")
    print(f"  - blocks.txt ({len(all_blocks)} entries) - complete catalogue")
    print(f"  - items.txt ({len(all_items)} entries) - complete catalogue")
    print(f"  - blocks/ ({len(blocks_by_namespace)} namespace files)")
    print(f"  - items/ ({len(items_by_namespace)} namespace files)")


if __name__ == '__main__':
    import sys
    
    mods_dir = 'mods'
    if len(sys.argv) > 1:
        mods_dir = sys.argv[1]
    
    scan_mods_directory(mods_dir)

