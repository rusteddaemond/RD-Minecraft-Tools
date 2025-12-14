#!/usr/bin/env python3
"""
Output Management
Saves all scan outputs to the scan_output directory.
"""

import logging
from pathlib import Path
from collections import defaultdict
from core.utils.item import extract_namespace, is_tag_reference, sanitize_filename

logger = logging.getLogger(__name__)


def _prepare_namespace_mapping(mods, namespace_to_mod):
    """Build complete namespace to mod mapping."""
    namespace_to_mod_map = namespace_to_mod.copy()
    # Also add mod_id as namespace if not already mapped
    for mod_id in mods.keys():
        if mod_id not in namespace_to_mod_map:
            namespace_to_mod_map[mod_id] = mod_id
    return namespace_to_mod_map


def _collect_referenced_items_by_namespace(all_tags, recipe_data):
    """Find all referenced items (from tags and recipes) by namespace."""
    all_referenced_items_by_ns = defaultdict(set)
    for tag_type, tag_dict in all_tags.items():
        for tag_items in tag_dict.values():
            for item in tag_items:
                if not is_tag_reference(item):
                    ns = extract_namespace(item)
                    if ns:
                        all_referenced_items_by_ns[ns].add(item)
    for item in recipe_data['all_recipe_items']:
        if not is_tag_reference(item):
            ns = extract_namespace(item)
            if ns:
                all_referenced_items_by_ns[ns].add(item)
    return all_referenced_items_by_ns


def _write_items_section(f, items, item_type):
    """Write a section of items to a file."""
    if items:
        f.write(f"{item_type} ({len(items)}):\n")
        for item in sorted(items):
            f.write(f"  {item}\n")
        f.write("\n")


def save_mods(output_path, mods, namespace_to_mod_map, blocks_by_ns, items_by_ns, fluids_by_ns):
    """
    Save mod information files.
    
    If a mod JAR exists, the mod is installed. All installed mods go in 'installed/' directory.
    The file shows:
    - Items from the mod's namespace(s) (actual mod items)
    - Items referenced in the mod's tags/recipes but from other namespaces (referenced items)
    """
    from core.utils.file import read_item_lines
    from core.utils.item import extract_namespace
    
    def _is_namespace_installed(namespace):
        """Check if a namespace belongs to an installed mod."""
        if namespace in mods:
            return True
        mod_id = namespace_to_mod_map.get(namespace)
        if mod_id:
            return mod_id == namespace and mod_id in mods
        return False
    
    installed_mods_dir = output_path / 'mods' / 'installed'
    installed_mods_dir.mkdir(parents=True, exist_ok=True)
    
    tag_to_items_dir = output_path / 'tag_to_items'
    
    for mod_id in sorted(mods.keys()):
        # Find all namespaces for this mod
        mod_namespaces = {ns for ns, m_id in namespace_to_mod_map.items() if m_id == mod_id}
        if mod_id not in mod_namespaces:
            mod_namespaces.add(mod_id)  # Add mod_id itself as namespace
        
        # Collect items from this mod's PRIMARY namespace only (actual mod items)
        # Use mod_id as the primary namespace
        mod_blocks = set(blocks_by_ns.get(mod_id, set()))
        mod_items = set(items_by_ns.get(mod_id, set()))
        mod_fluids = set(fluids_by_ns.get(mod_id, set()))
        
        # Collect items from other namespaces mapped to this mod (secondary namespaces)
        # These will go in referenced items section
        secondary_blocks_installed = set()
        secondary_blocks_not_installed = set()
        secondary_items_installed = set()
        secondary_items_not_installed = set()
        secondary_fluids_installed = set()
        secondary_fluids_not_installed = set()
        
        for ns in mod_namespaces:
            if ns != mod_id:  # Skip primary namespace
                for item in blocks_by_ns.get(ns, set()):
                    if _is_namespace_installed(ns):
                        secondary_blocks_installed.add(item)
                    else:
                        secondary_blocks_not_installed.add(item)
                for item in items_by_ns.get(ns, set()):
                    if _is_namespace_installed(ns):
                        secondary_items_installed.add(item)
                    else:
                        secondary_items_not_installed.add(item)
                for item in fluids_by_ns.get(ns, set()):
                    if _is_namespace_installed(ns):
                        secondary_fluids_installed.add(item)
                    else:
                        secondary_fluids_not_installed.add(item)
        
        # Collect all items referenced in this mod's tags/recipes
        referenced_blocks_installed = set()
        referenced_blocks_not_installed = set()
        referenced_items_installed = set()
        referenced_items_not_installed = set()
        referenced_fluids_installed = set()
        referenced_fluids_not_installed = set()
        
        # Read tag_to_items files from this mod's namespaces to find referenced items
        # Tag files are named like: namespace_tag_name.txt (sanitized)
        for ns in mod_namespaces:
            ns_prefix = ns.replace(':', '_') + '_'
            for tag_file in tag_to_items_dir.glob('*.txt'):
                tag_name = tag_file.stem
                # Check if this tag belongs to this namespace (starts with namespace_)
                if tag_name.startswith(ns_prefix):
                    # Read items from this tag file
                    for item in read_item_lines(tag_file, skip_comments=True, skip_tag_refs=True):
                        item_ns = extract_namespace(item)
                        if item_ns and item_ns not in mod_namespaces:
                            # This is a referenced item from another namespace
                            if item in blocks_by_ns.get(item_ns, set()):
                                if _is_namespace_installed(item_ns):
                                    referenced_blocks_installed.add(item)
                                else:
                                    referenced_blocks_not_installed.add(item)
                            elif item in items_by_ns.get(item_ns, set()):
                                if _is_namespace_installed(item_ns):
                                    referenced_items_installed.add(item)
                                else:
                                    referenced_items_not_installed.add(item)
                            elif item in fluids_by_ns.get(item_ns, set()):
                                if _is_namespace_installed(item_ns):
                                    referenced_fluids_installed.add(item)
                                else:
                                    referenced_fluids_not_installed.add(item)
        
        # If mod JAR exists, mod is installed - always put in installed/ directory
        # Write mod file
        with open(installed_mods_dir / f"{mod_id}.txt", 'w', encoding='utf-8') as f:
            f.write(f"JAR: {mods[mod_id]}\n")
            f.write(f"Namespaces: {', '.join(sorted(mod_namespaces))}\n")
            from core.utils.format import format_separator
            separator = format_separator()
            f.write(f"\n{separator}\n")
            f.write("ITEMS FROM THIS MOD\n")
            f.write(f"{separator}\n")
            f.write("Items from this mod's namespace(s):\n\n")
            
            _write_items_section(f, mod_blocks, "Blocks")
            _write_items_section(f, mod_items, "Items")
            _write_items_section(f, mod_fluids, "Fluids")
            
            if not mod_blocks and not mod_items and not mod_fluids:
                f.write("(No items found from this mod's namespace(s))\n\n")
            
            # Write referenced items section at the end
            has_referenced = (referenced_blocks_installed or referenced_blocks_not_installed or
                            referenced_items_installed or referenced_items_not_installed or
                            referenced_fluids_installed or referenced_fluids_not_installed)
            
            has_secondary = (secondary_blocks_installed or secondary_blocks_not_installed or
                           secondary_items_installed or secondary_items_not_installed or
                           secondary_fluids_installed or secondary_fluids_not_installed)
            
            if has_referenced or has_secondary:
                from core.utils.format import format_separator
                separator = format_separator()
                f.write(f"\n{separator}\n")
                f.write("REFERENCED ITEMS (from other namespaces)\n")
                f.write(f"{separator}\n")
                f.write("Items referenced in this mod's tags/recipes but from other namespaces:\n\n")
                
                # Write secondary namespaces first (if any)
                if has_secondary:
                    if secondary_blocks_installed or secondary_blocks_not_installed:
                        f.write("Blocks (from secondary namespaces):\n")
                        if secondary_blocks_installed:
                            f.write("  Installed:\n")
                            for item in sorted(secondary_blocks_installed):
                                f.write(f"    {item}\n")
                        if secondary_blocks_not_installed:
                            f.write("  Not Installed:\n")
                            for item in sorted(secondary_blocks_not_installed):
                                f.write(f"    {item}\n")
                        f.write("\n")
                    
                    if secondary_items_installed or secondary_items_not_installed:
                        f.write("Items (from secondary namespaces):\n")
                        if secondary_items_installed:
                            f.write("  Installed:\n")
                            for item in sorted(secondary_items_installed):
                                f.write(f"    {item}\n")
                        if secondary_items_not_installed:
                            f.write("  Not Installed:\n")
                            for item in sorted(secondary_items_not_installed):
                                f.write(f"    {item}\n")
                        f.write("\n")
                    
                    if secondary_fluids_installed or secondary_fluids_not_installed:
                        f.write("Fluids (from secondary namespaces):\n")
                        if secondary_fluids_installed:
                            f.write("  Installed:\n")
                            for item in sorted(secondary_fluids_installed):
                                f.write(f"    {item}\n")
                        if secondary_fluids_not_installed:
                            f.write("  Not Installed:\n")
                            for item in sorted(secondary_fluids_not_installed):
                                f.write(f"    {item}\n")
                        f.write("\n")
                
                # Write referenced items from tags/recipes
                if referenced_blocks_installed or referenced_blocks_not_installed:
                    f.write("Blocks:\n")
                    if referenced_blocks_installed:
                        f.write("  Installed:\n")
                        for item in sorted(referenced_blocks_installed):
                            f.write(f"    {item}\n")
                    if referenced_blocks_not_installed:
                        f.write("  Not Installed:\n")
                        for item in sorted(referenced_blocks_not_installed):
                            f.write(f"    {item}\n")
                    f.write("\n")
                
                if referenced_items_installed or referenced_items_not_installed:
                    f.write("Items:\n")
                    if referenced_items_installed:
                        f.write("  Installed:\n")
                        for item in sorted(referenced_items_installed):
                            f.write(f"    {item}\n")
                    if referenced_items_not_installed:
                        f.write("  Not Installed:\n")
                        for item in sorted(referenced_items_not_installed):
                            f.write(f"    {item}\n")
                    f.write("\n")
                
                if referenced_fluids_installed or referenced_fluids_not_installed:
                    f.write("Fluids:\n")
                    if referenced_fluids_installed:
                        f.write("  Installed:\n")
                        for item in sorted(referenced_fluids_installed):
                            f.write(f"    {item}\n")
                    if referenced_fluids_not_installed:
                        f.write("  Not Installed:\n")
                        for item in sorted(referenced_fluids_not_installed):
                            f.write(f"    {item}\n")
                    f.write("\n")


def save_installed_mods_summary(output_path, mods, namespace_to_mod):
    """
    Save an early summary of installed mods (only installed, not referenced).
    This is created right after mod discovery (Phase 1).
    Format: Simple list of mod IDs, with minecraft always first.
    """
    mods_dir = output_path / 'mods'
    mods_dir.mkdir(parents=True, exist_ok=True)
    
    summary_file = mods_dir / 'installed_mods_summary.txt'
    
    # Separate minecraft from other mods
    installed_mod_ids = sorted(mods.keys())
    minecraft_first = []
    other_mods = []
    
    for mod_id in installed_mod_ids:
        if mod_id == 'minecraft':
            minecraft_first.append(mod_id)
        else:
            other_mods.append(mod_id)
    
    # Combine: minecraft first, then others
    sorted_mods = minecraft_first + sorted(other_mods)
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        for mod_id in sorted_mods:
            f.write(f"{mod_id}\n")


def save_namespaces(output_path, namespaces):
    """Save namespaces list."""
    with open(output_path / 'namespaces.txt', 'w', encoding='utf-8') as f:
        for namespace in sorted(namespaces):
            f.write(f"{namespace}\n")


def save_items_by_namespace(output_path, blocks_by_namespace, items_by_namespace, fluids_by_namespace,
                           mods, namespace_to_mod_map):
    """
    Save blocks, items, and fluids organized by namespace.
    Splits into installed/ and not_installed/ based on whether the mod is installed.
    
    - installed/ = items from mods that are actually installed (JAR exists)
    - not_installed/ = items from mods that are referenced but not installed (no JAR)
    """
    def _is_namespace_installed(namespace):
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
    
    def _save_by_namespace(base_dir, items_by_ns, item_type_name):
        """Save items by namespace, split into installed/not_installed."""
        installed_dir = base_dir / 'installed'
        not_installed_dir = base_dir / 'not_installed'
        installed_dir.mkdir(parents=True, exist_ok=True)
        not_installed_dir.mkdir(parents=True, exist_ok=True)
        
        for namespace in sorted(items_by_ns.keys()):
            is_installed = _is_namespace_installed(namespace)
            target_dir = installed_dir if is_installed else not_installed_dir
            
            namespace_file = target_dir / f"{namespace}.txt"
            with open(namespace_file, 'w', encoding='utf-8') as f:
                for item in sorted(items_by_ns[namespace]):
                    f.write(f"{item}\n")
    
    # Save blocks by namespace
    blocks_namespace_dir = output_path / 'blocks'
    _save_by_namespace(blocks_namespace_dir, blocks_by_namespace, "blocks")
    
    # Save items by namespace
    items_namespace_dir = output_path / 'items'
    _save_by_namespace(items_namespace_dir, items_by_namespace, "items")
    
    # Save fluids by namespace
    fluids_namespace_dir = output_path / 'fluids'
    _save_by_namespace(fluids_namespace_dir, fluids_by_namespace, "fluids")


def save_mods_from_disk(output_path, mods, namespace_to_mod_map, blocks_by_ns, items_by_ns, 
                         fluids_by_ns):
    """Save mod files."""
    save_mods(output_path, mods, namespace_to_mod_map, blocks_by_ns, items_by_ns, fluids_by_ns)


def save_summary_from_disk(output_path, mods, namespaces, tag_metadata, recipe_metadata, 
                            categories, blocks_by_ns, items_by_ns, fluids_by_ns):
    """Save summary file using metadata from disk processing."""
    from core.utils.format import format_separator
    summary_file = output_path / 'summary.txt'
    separator = format_separator()
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("Dynamic Mod Scanning Summary\n")
        f.write(f"{separator}\n\n")
        f.write(f"Total mods discovered: {len(mods)}\n")
        f.write(f"Total namespaces discovered: {len(namespaces)}\n")
        f.write(f"Total tag groups discovered: {tag_metadata.get('total_tags', 0)}\n")
        f.write(f"Total recipes found: {recipe_metadata.get('total_recipes', 0)}\n")
        f.write(f"Total recipe types discovered: {len(recipe_metadata.get('recipe_types', set()))}\n")
        f.write(f"Total categories generated: {len(categories.get('by_tag', {}))}\n\n")
        
        f.write("\nTag Groups by Type:\n")
        for tag_type, count in sorted(tag_metadata.get('tag_counts', {}).items()):
            f.write(f"  {tag_type:15s}: {count:4d} tag groups\n")
        
        f.write("\nRecipe Types:\n")
        for recipe_type, count in sorted(recipe_metadata.get('recipe_counts_by_type', {}).items()):
            f.write(f"  {recipe_type:50s}: {count:5d} recipes\n")
        
        f.write("\nCategories:\n")
        for category in sorted(categories.get('by_tag', {}).keys()):
            count = len(categories['by_tag'][category])
            f.write(f"  {category:30s}: {count:5d} items\n")
        
        f.write("\nBlocks by Namespace (top 20):\n")
        for namespace in sorted(blocks_by_ns.keys(), key=lambda x: len(blocks_by_ns[x]), reverse=True)[:20]:
            count = len(blocks_by_ns[namespace])
            f.write(f"  {namespace:30s}: {count:5d} blocks\n")
        
        f.write("\nItems by Namespace (top 20):\n")
        for namespace in sorted(items_by_ns.keys(), key=lambda x: len(items_by_ns[x]), reverse=True)[:20]:
            count = len(items_by_ns[namespace])
            f.write(f"  {namespace:30s}: {count:5d} items\n")
        
        f.write("\nFluids by Namespace:\n")
        for namespace in sorted(fluids_by_ns.keys()):
            count = len(fluids_by_ns[namespace])
            f.write(f"  {namespace:30s}: {count:5d} fluids\n")

