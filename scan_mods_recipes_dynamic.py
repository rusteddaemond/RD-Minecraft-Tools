#!/usr/bin/env python3
"""
Dynamic recipe and tag scanner for Minecraft mods.
Discovers ALL recipe types and tag groups dynamically from mod JAR files.
This script is standalone and doesn't use any code from the codebase.
"""

import os
import json
import zipfile
from pathlib import Path
from collections import defaultdict


def extract_item_from_ingredient(ingredient):
    """Extract item identifier from an ingredient (item, tag, or list)."""
    items = set()
    
    if isinstance(ingredient, dict):
        if 'item' in ingredient:
            items.add(ingredient['item'])
        elif 'tag' in ingredient:
            # Tags are marked with # prefix
            items.add(f"#{ingredient['tag']}")
        elif 'items' in ingredient:
            # List of items
            for item in ingredient['items']:
                items.update(extract_item_from_ingredient(item))
    elif isinstance(ingredient, list):
        for item in ingredient:
            items.update(extract_item_from_ingredient(item))
    
    return items


def extract_result(result):
    """Extract item identifier from a result."""
    if isinstance(result, dict):
        if 'id' in result:
            return result['id']
        elif 'item' in result:
            return result['item']
    elif isinstance(result, str):
        return result
    return None


def parse_recipe(recipe_data, recipe_id):
    """Parse a recipe JSON and extract information."""
    recipe_info = {
        'id': recipe_id,
        'type': None,
        'inputs': set(),
        'outputs': set(),
        'category': None,
        'raw_data': recipe_data,  # Keep raw data for analysis
    }
    
    # Extract recipe type
    recipe_type = recipe_data.get('type', '')
    recipe_info['type'] = recipe_type
    
    # Extract category if present
    recipe_info['category'] = recipe_data.get('category')
    
    # Extract inputs based on recipe type
    if 'crafting_shaped' in recipe_type or 'crafting_shapeless' in recipe_type:
        # Shaped crafting
        if 'key' in recipe_data:
            for key, ingredient in recipe_data['key'].items():
                recipe_info['inputs'].update(extract_item_from_ingredient(ingredient))
        # Shapeless crafting
        if 'ingredients' in recipe_data:
            for ingredient in recipe_data['ingredients']:
                recipe_info['inputs'].update(extract_item_from_ingredient(ingredient))
        # Ingredient (single)
        if 'ingredient' in recipe_data:
            recipe_info['inputs'].update(extract_item_from_ingredient(recipe_data['ingredient']))
    
    elif 'smelting' in recipe_type or 'blasting' in recipe_type or 'smoking' in recipe_type or 'campfire_cooking' in recipe_type:
        # Furnace-like recipes
        if 'ingredient' in recipe_data:
            recipe_info['inputs'].update(extract_item_from_ingredient(recipe_data['ingredient']))
    
    elif 'stonecutting' in recipe_type:
        # Stonecutter
        if 'ingredient' in recipe_data:
            recipe_info['inputs'].update(extract_item_from_ingredient(recipe_data['ingredient']))
    
    elif 'smithing' in recipe_type:
        # Smithing table
        if 'base' in recipe_data:
            recipe_info['inputs'].update(extract_item_from_ingredient(recipe_data['base']))
        if 'addition' in recipe_data:
            recipe_info['inputs'].update(extract_item_from_ingredient(recipe_data['addition']))
        if 'template' in recipe_data:
            recipe_info['inputs'].update(extract_item_from_ingredient(recipe_data['template']))
    else:
        # Unknown recipe type - try to extract any ingredient-like fields
        for key in ['ingredient', 'ingredients', 'input', 'inputs', 'base', 'addition', 'template']:
            if key in recipe_data:
                recipe_info['inputs'].update(extract_item_from_ingredient(recipe_data[key]))
    
    # Extract outputs
    if 'result' in recipe_data:
        result = extract_result(recipe_data['result'])
        if result:
            recipe_info['outputs'].add(result)
    
    if 'results' in recipe_data:
        for result in recipe_data['results']:
            result_item = extract_result(result)
            if result_item:
                recipe_info['outputs'].add(result_item)
    
    return recipe_info


def extract_all_tags_from_jar(jar_path):
    """Extract ALL tags from a mod JAR file, dynamically discovering all tag types."""
    all_tags = defaultdict(lambda: defaultdict(set))  # tag_type -> tag_name -> items
    
    try:
        with zipfile.ZipFile(jar_path, 'r') as jar:
            file_list = jar.namelist()
            
            # Dynamically discover all tag files by looking for /tags/ in path
            # Pattern: data/<namespace>/tags/<tag_type>/<tag_name>.json
            for file_path in file_list:
                if '/tags/' in file_path and file_path.endswith('.json'):
                    parts = file_path.split('/')
                    
                    # Find the tags directory index
                    try:
                        tags_index = parts.index('tags')
                        if tags_index + 2 < len(parts):
                            namespace = parts[tags_index - 1]  # data/<namespace>/tags/...
                            tag_type = parts[tags_index + 1]  # .../tags/<tag_type>/...
                            tag_name = parts[-1].replace('.json', '')
                            full_tag_name = f"{namespace}:{tag_name}"
                            
                            try:
                                with jar.open(file_path) as f:
                                    content = f.read().decode('utf-8')
                                    tag_data = json.loads(content)
                                    
                                    # Handle different tag data formats
                                    values = []
                                    if 'values' in tag_data:
                                        values = tag_data['values']
                                    elif isinstance(tag_data, list):
                                        values = tag_data
                                    
                                    def extract_tag_value(val):
                                        """Recursively extract values from tag entries."""
                                        if isinstance(val, str):
                                            return [val]
                                        elif isinstance(val, dict):
                                            result = []
                                            # Handle tag references like {"id": "namespace:tag", "required": false}
                                            if 'id' in val:
                                                result.append(val['id'])
                                            # Handle item references like {"item": "namespace:item"}
                                            if 'item' in val:
                                                result.append(val['item'])
                                            # Handle tag references like {"tag": "namespace:tag"}
                                            if 'tag' in val:
                                                result.append(f"#{val['tag']}")  # Mark as tag reference
                                            # Handle nested structures
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
                                    
                                    for value in values:
                                        extracted = extract_tag_value(value)
                                        for item in extracted:
                                            if item:
                                                all_tags[tag_type][full_tag_name].add(item)
                            except (json.JSONDecodeError, UnicodeDecodeError, KeyError, IndexError) as e:
                                # Skip invalid tag files - uncomment for debugging
                                # print(f"  Warning: Could not parse tag {file_path}: {e}")
                                pass
                    except (ValueError, IndexError):
                        # Skip if path structure is unexpected
                        pass
            
    except (zipfile.BadZipFile, OSError):
        pass
    
    return all_tags


def extract_recipes_from_jar(jar_path):
    """Extract recipes from a single mod JAR file."""
    recipes = []
    mod_name = os.path.basename(jar_path)
    
    try:
        with zipfile.ZipFile(jar_path, 'r') as jar:
            file_list = jar.namelist()
            
            # Look for recipe files in data/<namespace>/recipes/
            for file_path in file_list:
                if '/recipes/' in file_path and file_path.endswith('.json'):
                    # Extract namespace and recipe name
                    parts = file_path.split('/')
                    if len(parts) >= 4:
                        namespace = parts[1]  # data/<namespace>/recipes/<name>.json
                        recipe_name = parts[-1].replace('.json', '')
                        recipe_id = f"{namespace}:{recipe_name}"
                        
                        try:
                            with jar.open(file_path) as f:
                                content = f.read().decode('utf-8')
                                recipe_data = json.loads(content)
                                recipe_info = parse_recipe(recipe_data, recipe_id)
                                recipes.append(recipe_info)
                        except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
                            # Skip invalid recipe files
                            pass
            
    except (zipfile.BadZipFile, OSError) as e:
        print(f"Error reading {mod_name}: {e}")
        return recipes
    
    return recipes


def scan_mods_directory(mods_dir='mods'):
    """Scan all JAR files in the mods directory for recipes and tags."""
    mods_path = Path(mods_dir)
    
    if not mods_path.exists():
        print(f"Error: Directory '{mods_dir}' does not exist!")
        return
    
    all_recipes = []
    recipes_by_type = defaultdict(list)
    all_tags_combined = defaultdict(lambda: defaultdict(set))  # tag_type -> tag_name -> items
    recipe_types_found = set()
    
    jar_files = list(mods_path.glob('*.jar'))
    
    if not jar_files:
        print(f"No JAR files found in '{mods_dir}' directory!")
        return
    
    print(f"Found {len(jar_files)} JAR file(s) to scan...")
    print("=" * 60)
    
    # PASS 1: Collect ALL tags from all mods first
    print("\nPASS 1: Scanning for ALL tags...")
    print("-" * 60)
    
    for jar_file in jar_files:
        mod_name = jar_file.name
        print(f"Scanning tags: {mod_name}...", end=' ', flush=True)
        
        # Extract all tags from this mod
        tags = extract_all_tags_from_jar(jar_file)
        tag_count = sum(len(tag_dict) for tag_dict in tags.values())
        for tag_type, tag_dict in tags.items():
            for tag_name, tag_items in tag_dict.items():
                all_tags_combined[tag_type][tag_name].update(tag_items)
        
        print(f"Found {tag_count} tag groups")
    
    total_tag_groups = sum(len(tags) for tags in all_tags_combined.values())
    print(f"\nTotal tag groups collected: {total_tag_groups}")
    
    # Build reverse lookup: item -> list of tags it belongs to
    # This allows us to find which tags any item belongs to
    item_to_tags = defaultdict(lambda: defaultdict(set))  # item -> tag_type -> set of tag_names
    for tag_type, tag_dict in all_tags_combined.items():
        for tag_name, tag_items in tag_dict.items():
            for item in tag_items:
                # Remove # prefix if present (tag references)
                clean_item = item.replace('#', '')
                item_to_tags[clean_item][tag_type].add(tag_name)
    
    print(f"Total unique items found in tags: {len(item_to_tags)}")
    
    # PASS 2: Scan recipes and categorize using collected tags
    print("\nPASS 2: Scanning recipes and categorizing with collected tags...")
    print("-" * 60)
    
    for jar_file in jar_files:
        mod_name = jar_file.name
        print(f"Scanning recipes: {mod_name}...", end=' ', flush=True)
        
        recipes = extract_recipes_from_jar(jar_file)
        all_recipes.extend(recipes)
        
        # Track recipe types
        for recipe in recipes:
            if recipe['type']:
                recipe_types_found.add(recipe['type'])
                recipes_by_type[recipe['type']].append(recipe)
        
        print(f"Found {len(recipes)} recipes")
    
    print("=" * 60)
    print(f"\nScan complete!")
    print(f"Total mods scanned: {len(jar_files)}")
    print(f"Total recipes found: {len(all_recipes)}")
    print(f"Total recipe types discovered: {len(recipe_types_found)}")
    print(f"Total tag groups discovered: {sum(len(tags) for tags in all_tags_combined.values())}")
    print(f"Total unique items in tags: {len(item_to_tags)}")
    
    # Print recipe type summary
    print("\nRecipe types discovered:")
    for recipe_type in sorted(recipe_types_found):
        count = len(recipes_by_type[recipe_type])
        print(f"  {recipe_type:50s}: {count:5d} recipes")
    
    # Print tag type summary
    print("\nTag groups by type:")
    for tag_type in sorted(all_tags_combined.keys()):
        count = len(all_tags_combined[tag_type])
        total_items = sum(len(items) for items in all_tags_combined[tag_type].values())
        print(f"  {tag_type:15s}: {count:4d} tag groups, {total_items:6d} total items")
    
    # Create output directory
    output_dir = Path('scan_output')
    dynamic_dir = output_dir / 'dynamic'
    dynamic_dir.mkdir(parents=True, exist_ok=True)
    
    # Save all recipe types
    recipe_types_dir = dynamic_dir / 'recipe_types'
    recipe_types_dir.mkdir(exist_ok=True)
    
    with open(recipe_types_dir / 'all_recipe_types.txt', 'w', encoding='utf-8') as f:
        f.write("All Recipe Types Discovered\n")
        f.write("=" * 60 + "\n\n")
        for recipe_type in sorted(recipe_types_found):
            count = len(recipes_by_type[recipe_type])
            f.write(f"{recipe_type:50s}: {count:5d} recipes\n")
    
    # Save recipes by type
    recipes_by_type_dir = recipe_types_dir / 'recipes'
    recipes_by_type_dir.mkdir(exist_ok=True)
    
    for recipe_type in sorted(recipes_by_type.keys()):
        # Sanitize filename
        safe_type_name = recipe_type.replace(':', '_').replace('/', '_')
        type_file = recipes_by_type_dir / f"{safe_type_name}.txt"
        with open(type_file, 'w', encoding='utf-8') as f:
            f.write(f"Recipe Type: {recipe_type}\n")
            f.write(f"Total Recipes: {len(recipes_by_type[recipe_type])}\n")
            f.write("=" * 60 + "\n\n")
            for recipe in sorted(recipes_by_type[recipe_type], key=lambda x: x['id']):
                f.write(f"{recipe['id']}\n")
                if recipe['inputs']:
                    f.write(f"  Inputs: {', '.join(sorted(recipe['inputs']))}\n")
                if recipe['outputs']:
                    f.write(f"  Outputs: {', '.join(sorted(recipe['outputs']))}\n")
                f.write("\n")
    
    # Save all tags
    tags_dir = dynamic_dir / 'tags'
    tags_dir.mkdir(exist_ok=True)
    
    # Common c: tags to check for (reference list)
    common_c_tags = {
        'items': [
            'c:ores', 'c:ropes', 'c:ingots', 'c:nuggets', 'c:dusts', 'c:gems', 'c:rods',
            'c:storage_blocks', 'c:dyed', 'c:barrels', 'c:bookshelves', 'c:chains',
            'c:chests', 'c:cobblestones', 'c:concretes', 'c:logs', 'c:planks', 'c:wool',
            'c:seeds', 'c:grapes', 'c:milk', 'c:stripped_logs', 'c:stripped_wood',
        ],
        'blocks': [
            'c:ores', 'c:ropes', 'c:storage_blocks', 'c:dyed', 'c:barrels',
            'c:bookshelves', 'c:chains', 'c:chests', 'c:cobblestones', 'c:concretes',
            'c:logs', 'c:planks', 'c:wool', 'c:stripped_logs', 'c:stripped_wood',
        ],
    }
    
    # Save tag summary
    with open(tags_dir / 'all_tags_summary.txt', 'w', encoding='utf-8') as f:
        f.write("All Tag Groups Discovered\n")
        f.write("=" * 60 + "\n\n")
        
        # Check for common c: tags
        found_c_tags = defaultdict(set)
        missing_c_tags = defaultdict(set)
        
        for tag_type in ['items', 'blocks']:
            if tag_type in all_tags_combined:
                for common_tag in common_c_tags.get(tag_type, []):
                    if common_tag in all_tags_combined[tag_type]:
                        found_c_tags[tag_type].add(common_tag)
                    else:
                        missing_c_tags[tag_type].add(common_tag)
        
        # Write found common tags
        if found_c_tags:
            f.write("Common c: Tags Found:\n")
            f.write("-" * 60 + "\n")
            for tag_type in sorted(found_c_tags.keys()):
                for tag_name in sorted(found_c_tags[tag_type]):
                    count = len(all_tags_combined[tag_type][tag_name])
                    f.write(f"  ✓ {tag_type}/{tag_name:40s}: {count:5d} items\n")
            f.write("\n")
        
        # Write missing common tags
        if missing_c_tags:
            f.write("Common c: Tags NOT Found (may not exist in scanned mods):\n")
            f.write("-" * 60 + "\n")
            for tag_type in sorted(missing_c_tags.keys()):
                for tag_name in sorted(missing_c_tags[tag_type]):
                    f.write(f"  ✗ {tag_type}/{tag_name}\n")
            f.write("\n")
        
        # Write all discovered tags
        f.write("\nAll Tag Groups by Type:\n")
        f.write("=" * 60 + "\n\n")
        for tag_type in sorted(all_tags_combined.keys()):
            f.write(f"\n[{tag_type.upper()} TAGS]\n")
            f.write("-" * 60 + "\n")
            # Sort to show c: tags first
            sorted_tags = sorted(all_tags_combined[tag_type].keys(), 
                               key=lambda x: (not x.startswith('c:'), x))
            for tag_name in sorted_tags:
                count = len(all_tags_combined[tag_type][tag_name])
                f.write(f"  {tag_name:50s}: {count:5d} items\n")
    
    # Save tags by type
    for tag_type in sorted(all_tags_combined.keys()):
        tag_type_dir = tags_dir / tag_type
        tag_type_dir.mkdir(exist_ok=True)
        
        for tag_name in sorted(all_tags_combined[tag_type].keys()):
            # Sanitize filename
            safe_tag_name = tag_name.replace(':', '_').replace('/', '_')
            tag_file = tag_type_dir / f"{safe_tag_name}.txt"
            with open(tag_file, 'w', encoding='utf-8') as f:
                for item in sorted(all_tags_combined[tag_type][tag_name]):
                    f.write(f"{item}\n")
    
    # Create categorized items by recipe type
    categories_dir = dynamic_dir / 'categories'
    categories_dir.mkdir(exist_ok=True)
    
    # Organize items by recipe type (inputs and outputs)
    recipe_inputs = defaultdict(set)
    recipe_outputs = defaultdict(set)
    
    # Collect all items from recipes
    all_recipe_items = set()
    
    for recipe in all_recipes:
        if recipe['type']:
            recipe_type = recipe['type']
            recipe_inputs[recipe_type].update(recipe['inputs'])
            recipe_outputs[recipe_type].update(recipe['outputs'])
            all_recipe_items.update(recipe['inputs'])
            all_recipe_items.update(recipe['outputs'])
    
    # Save recipe inputs by type
    inputs_dir = categories_dir / 'recipe_inputs'
    inputs_dir.mkdir(exist_ok=True)
    
    for recipe_type in sorted(recipe_inputs.keys()):
        safe_type_name = recipe_type.replace(':', '_').replace('/', '_')
        type_file = inputs_dir / f"{safe_type_name}.txt"
        with open(type_file, 'w', encoding='utf-8') as f:
            for item in sorted(recipe_inputs[recipe_type]):
                f.write(f"{item}\n")
    
    # Save recipe outputs by type
    outputs_dir = categories_dir / 'recipe_outputs'
    outputs_dir.mkdir(exist_ok=True)
    
    for recipe_type in sorted(recipe_outputs.keys()):
        safe_type_name = recipe_type.replace(':', '_').replace('/', '_')
        type_file = outputs_dir / f"{safe_type_name}.txt"
        with open(type_file, 'w', encoding='utf-8') as f:
            for item in sorted(recipe_outputs[recipe_type]):
                f.write(f"{item}\n")
    
    # Create reverse lookup: items categorized by tags
    print("\nCategorizing items by tags...")
    items_by_tag = defaultdict(lambda: defaultdict(set))  # tag_type -> tag_name -> items
    
    # For each item found in recipes, find which tags it belongs to
    for item in all_recipe_items:
        clean_item = item.replace('#', '')
        if clean_item in item_to_tags:
            for tag_type, tag_names in item_to_tags[clean_item].items():
                for tag_name in tag_names:
                    items_by_tag[tag_type][tag_name].add(item)
    
    # Also categorize all items from tags themselves
    for tag_type, tag_dict in all_tags_combined.items():
        for tag_name, tag_items in tag_dict.items():
            for item in tag_items:
                clean_item = item.replace('#', '')
                items_by_tag[tag_type][tag_name].add(clean_item)
    
    # Save items categorized by tags
    items_by_tag_dir = categories_dir / 'items_by_tag'
    items_by_tag_dir.mkdir(exist_ok=True)
    
    for tag_type in sorted(items_by_tag.keys()):
        tag_type_dir = items_by_tag_dir / tag_type
        tag_type_dir.mkdir(exist_ok=True)
        
        for tag_name in sorted(items_by_tag[tag_type].keys()):
            safe_tag_name = tag_name.replace(':', '_').replace('/', '_')
            tag_file = tag_type_dir / f"{safe_tag_name}.txt"
            with open(tag_file, 'w', encoding='utf-8') as f:
                for item in sorted(items_by_tag[tag_type][tag_name]):
                    f.write(f"{item}\n")
    
    # Save reverse lookup: item -> tags
    item_tags_lookup_dir = categories_dir / 'item_to_tags'
    item_tags_lookup_dir.mkdir(exist_ok=True)
    
    with open(item_tags_lookup_dir / 'all_items_with_tags.txt', 'w', encoding='utf-8') as f:
        for item in sorted(item_to_tags.keys()):
            f.write(f"{item}\n")
            for tag_type in sorted(item_to_tags[item].keys()):
                tag_names = sorted(item_to_tags[item][tag_type])
                f.write(f"  {tag_type}: {', '.join(tag_names)}\n")
            f.write("\n")
    
    # Save comprehensive summary
    summary_file = dynamic_dir / 'summary.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("Dynamic Recipe and Tag Scanning Summary\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total mods scanned: {len(jar_files)}\n")
        f.write(f"Total recipes found: {len(all_recipes)}\n")
        f.write(f"Total recipe types discovered: {len(recipe_types_found)}\n")
        f.write(f"Total tag groups discovered: {sum(len(tags) for tags in all_tags_combined.values())}\n\n")
        
        f.write("\nRecipe Types:\n")
        for recipe_type in sorted(recipe_types_found):
            count = len(recipes_by_type[recipe_type])
            f.write(f"  {recipe_type:50s}: {count:5d} recipes\n")
        
        f.write("\nTag Groups by Type:\n")
        for tag_type in sorted(all_tags_combined.keys()):
            count = len(all_tags_combined[tag_type])
            total_items = sum(len(items) for items in all_tags_combined[tag_type].values())
            f.write(f"  {tag_type:15s}: {count:4d} tag groups, {total_items:6d} total items\n")
            for tag_name in sorted(all_tags_combined[tag_type].keys())[:10]:  # Show first 10
                item_count = len(all_tags_combined[tag_type][tag_name])
                f.write(f"    - {tag_name:48s}: {item_count:5d} items\n")
            if len(all_tags_combined[tag_type]) > 10:
                f.write(f"    ... and {len(all_tags_combined[tag_type]) - 10} more tag groups\n")
    
    print(f"\nResults saved to '{dynamic_dir}/' directory:")
    print(f"  - recipe_types/ (all discovered recipe types)")
    print(f"  - tags/ (all discovered tag groups)")
    print(f"  - categories/ (items organized by recipe type and tags)")
    print(f"    - recipe_inputs/ (items used as inputs per recipe type)")
    print(f"    - recipe_outputs/ (items produced per recipe type)")
    print(f"    - items_by_tag/ (items categorized by all found tags)")
    print(f"    - item_to_tags/ (reverse lookup: which tags each item belongs to)")
    print(f"  - summary.txt (comprehensive summary)")


if __name__ == '__main__':
    import sys
    
    mods_dir = 'mods'
    if len(sys.argv) > 1:
        mods_dir = sys.argv[1]
    
    scan_mods_directory(mods_dir)

