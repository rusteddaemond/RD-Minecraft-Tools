#!/usr/bin/env python3
"""
Recipe Discovery
Scans recipes and writes them to disk immediately to reduce memory usage.
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


def extract_item_from_ingredient(ingredient):
    """Extract item identifier from an ingredient (item, tag, or list)."""
    items = set()
    
    if isinstance(ingredient, dict):
        if 'item' in ingredient:
            items.add(ingredient['item'])
        elif 'tag' in ingredient:
            items.add(f"#{ingredient['tag']}")
        elif 'items' in ingredient:
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
    }
    
    recipe_type = recipe_data.get('type', '')
    recipe_info['type'] = recipe_type
    recipe_info['category'] = recipe_data.get('category')
    
    # Extract inputs based on recipe type
    if 'crafting_shaped' in recipe_type or 'crafting_shapeless' in recipe_type:
        if 'key' in recipe_data:
            for key, ingredient in recipe_data['key'].items():
                recipe_info['inputs'].update(extract_item_from_ingredient(ingredient))
        if 'ingredients' in recipe_data:
            for ingredient in recipe_data['ingredients']:
                recipe_info['inputs'].update(extract_item_from_ingredient(ingredient))
        if 'ingredient' in recipe_data:
            recipe_info['inputs'].update(extract_item_from_ingredient(recipe_data['ingredient']))
    
    elif 'smelting' in recipe_type or 'blasting' in recipe_type or 'smoking' in recipe_type or 'campfire_cooking' in recipe_type:
        if 'ingredient' in recipe_data:
            recipe_info['inputs'].update(extract_item_from_ingredient(recipe_data['ingredient']))
    
    elif 'stonecutting' in recipe_type:
        if 'ingredient' in recipe_data:
            recipe_info['inputs'].update(extract_item_from_ingredient(recipe_data['ingredient']))
    
    elif 'smithing' in recipe_type:
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


def discover_and_save_recipes_incremental(mods, output_dir):
    """
    Discover recipes incrementally and write to disk immediately.
    Returns minimal metadata needed for later processing.
    """
    print(f"\nPHASE 3: Recipe Discovery (Behavioral Layer) - Incremental")
    from core.utils.format import print_separator
    print_separator()
    
    output_path = Path(output_dir)
    recipes_dir = output_path / 'recipes'
    by_type_dir = recipes_dir / 'by_type'
    by_mod_dir = recipes_dir / 'by_mod'
    item_inputs_dir = recipes_dir / 'item_inputs'
    item_outputs_dir = recipes_dir / 'item_outputs'
    
    recipes_dir.mkdir(parents=True, exist_ok=True)
    by_type_dir.mkdir(exist_ok=True)
    by_mod_dir.mkdir(exist_ok=True)
    item_inputs_dir.mkdir(exist_ok=True)
    item_outputs_dir.mkdir(exist_ok=True)
    
    # Track minimal metadata
    recipe_types_found = set()
    recipe_counts_by_type = defaultdict(int)
    recipe_counts_by_mod = defaultdict(int)
    total_recipes = 0
    
    # File handles for item inputs/outputs (append mode, cached for efficiency)
    # Note: Recipe types are limited, so we don't need a cache limit here
    item_inputs_files = {}  # recipe_type -> file handle
    item_outputs_files = {}  # recipe_type -> file handle
    by_type_files = {}  # recipe_type -> file handle
    
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
            print(f"Scanning recipes: {mod_id}...", end=' ', flush=True)
            
            mod_recipe_count = 0
            mod_recipes = []
            
            with open_jar_safe(jar_path) as jar:
                file_list = jar.namelist()
                
                for file_path in file_list:
                    if '/recipes/' in file_path and file_path.endswith('.json'):
                        parts = file_path.split('/')
                        if len(parts) >= 4:
                            namespace = parts[1]
                            recipe_name = parts[-1].replace('.json', '')
                            recipe_id = f"{namespace}:{recipe_name}"
                            
                            recipe_data = load_json_from_jar(jar, file_path)
                            if recipe_data:
                                recipe_info = parse_recipe(recipe_data, recipe_id)
                                mod_recipes.append(recipe_info)
                                mod_recipe_count += 1
                                
                                # Track recipe type
                                if recipe_info['type']:
                                    recipe_type = recipe_info['type']
                                    recipe_types_found.add(recipe_type)
                                    recipe_counts_by_type[recipe_type] += 1
                                    
                                    safe_type_name = sanitize_filename(recipe_type)
                                    
                                    # Get or create file handle for by_type (reopen in append mode if needed)
                                    if safe_type_name not in by_type_files:
                                        type_file = by_type_dir / f"{safe_type_name}.txt"
                                        by_type_files[safe_type_name] = open(type_file, 'a', encoding='utf-8')
                                    
                                    by_type_files[safe_type_name].write(f"{recipe_info['id']}\n")
                                    if recipe_info['inputs']:
                                        by_type_files[safe_type_name].write(f"  Inputs: {', '.join(sorted(recipe_info['inputs']))}\n")
                                    if recipe_info['outputs']:
                                        by_type_files[safe_type_name].write(f"  Outputs: {', '.join(sorted(recipe_info['outputs']))}\n")
                                    by_type_files[safe_type_name].write("\n")
                                    
                                    # Get or create file handles for item inputs/outputs (reopen in append mode if needed)
                                    if safe_type_name not in item_inputs_files:
                                        inputs_file = item_inputs_dir / f"{safe_type_name}.txt"
                                        item_inputs_files[safe_type_name] = open(inputs_file, 'a', encoding='utf-8')
                                    
                                    if safe_type_name not in item_outputs_files:
                                        outputs_file = item_outputs_dir / f"{safe_type_name}.txt"
                                        item_outputs_files[safe_type_name] = open(outputs_file, 'a', encoding='utf-8')
                                    
                                    # Write item inputs
                                    for item in sorted(recipe_info['inputs']):
                                        item_inputs_files[safe_type_name].write(f"{item}\n")
                                    
                                    # Write item outputs
                                    for item in sorted(recipe_info['outputs']):
                                        item_outputs_files[safe_type_name].write(f"{item}\n")
                
                # Write mod recipes file
                if mod_recipes:
                    mod_file = by_mod_dir / f"{mod_id}.txt"
                    with open(mod_file, 'w', encoding='utf-8') as f:
                        for recipe in sorted(mod_recipes, key=lambda x: x['id']):
                            f.write(f"{recipe['id']}\n")
                    
                    recipe_counts_by_mod[mod_id] = len(mod_recipes)
                    total_recipes += len(mod_recipes)
            
            print(f"Found {mod_recipe_count} recipes")
        
        # After each batch: flush and close all file handles
        logger.info(f"Flushing and closing all recipe files after batch {batch_num}...")
        for f in by_type_files.values():
            f.flush()
            f.close()
        for f in item_inputs_files.values():
            f.flush()
            f.close()
        for f in item_outputs_files.values():
            f.flush()
            f.close()
        
        # Clear file handles (will be reopened in append mode if needed in next batch)
        by_type_files.clear()
        item_inputs_files.clear()
        item_outputs_files.clear()
    
    # Final flush and close (in case any files are still open)
    logger.info("Final flush and close of all recipe files...")
    for f in by_type_files.values():
        f.flush()
        f.close()
    for f in item_inputs_files.values():
        f.flush()
        f.close()
    for f in item_outputs_files.values():
        f.flush()
        f.close()
    by_type_files.clear()
    item_inputs_files.clear()
    item_outputs_files.clear()
    
    from core.utils.format import print_subseparator
    print_subseparator()
    print(f"Total recipes found: {total_recipes}")
    print(f"Total recipe types discovered: {len(recipe_types_found)}")
    
    # Return minimal metadata
    return {
        'recipe_types': recipe_types_found,
        'recipe_counts_by_type': dict(recipe_counts_by_type),
        'recipe_counts_by_mod': dict(recipe_counts_by_mod),
        'total_recipes': total_recipes
    }

