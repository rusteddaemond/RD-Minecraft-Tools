#!/usr/bin/env python3
"""
Minecraft Mod Scanner Module
Unified dynamic scanner for Minecraft mods with a single entry point.

The scanner pipeline consists of 4 phases:
1. Mod & namespace discovery (foundation)
2. Tag discovery (primary truth)
3. Recipe discovery (behavioral layer)
4. Dynamic categorization (derived from tags)

Tags are the central truth - everything else is derived from them.
"""

import logging

from core.scanner.mods import discover_mods_and_namespaces
from core.scanner.tags import discover_and_save_tags_incremental
from core.scanner.recipes import discover_and_save_recipes_incremental
from core.scanner.categorize import categorize_from_disk_tags
from core.scanner.process import collect_namespaces_from_disk
from core.scanner.output import save_mods, save_namespaces, save_items_by_namespace
from core.constants import DefaultDirs
from core.utils.format import print_separator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def scan(mods_dir=None, output_dir=None):
    """
    Main entry point for the mod scanning pipeline.
    Uses incremental scanning (writes to disk as we scan) for memory efficiency.
    
    Args:
        mods_dir: Directory containing mod JAR files (default: DefaultDirs.MODS)
        output_dir: Directory to save scan results (default: DefaultDirs.SCAN_OUTPUT)
    
    Returns:
        None (results are saved to output_dir)
    """
    if mods_dir is None:
        mods_dir = str(DefaultDirs.MODS)
    if output_dir is None:
        output_dir = str(DefaultDirs.SCAN_OUTPUT)
    
    print_separator()
    print("UNIFIED DYNAMIC MOD SCANNER")
    print("Tags are the primary truth - everything else is derived")
    print("Using INCREMENTAL mode (memory-efficient)")
    print_separator()
    
    # Phase 1: Mod & namespace discovery
    mods, namespaces, namespace_to_mod = discover_mods_and_namespaces(mods_dir)
    if not mods:
        return
    
    # Save early summary of installed mods and namespaces
    from pathlib import Path
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    from core.scanner.output import save_installed_mods_summary
    save_installed_mods_summary(output_path, mods, namespace_to_mod)
    logger.info("Saved installed mods summary")
    
    # Phase 2: Tag discovery - write immediately to disk
    # Prepare namespace mapping for installed/not_installed separation
    from core.scanner.output import _prepare_namespace_mapping
    namespace_to_mod_map = _prepare_namespace_mapping(mods, namespace_to_mod)
    tag_metadata = discover_and_save_tags_incremental(mods, output_dir, namespace_to_mod_map)
    
    # Phase 3: Recipe discovery - write immediately to disk
    recipe_metadata = discover_and_save_recipes_incremental(mods, output_dir)
    
    # Phase 4: Categorization - read from disk files
    categories = categorize_from_disk_tags(output_dir)
    
    # Now process from disk to build namespace collections
    logger.info("Building namespace collections from disk files...")
    blocks_by_ns, items_by_ns, fluids_by_ns, all_referenced_items_by_ns = collect_namespaces_from_disk(output_dir)
    
    # Save remaining outputs (mods, namespaces, items by namespace, summary)
    logger.info("Saving categorized outputs...")
    from core.scanner.output import save_mods_from_disk, save_summary_from_disk
    # namespace_to_mod_map already prepared above
    
    save_namespaces(output_path, namespaces)
    save_items_by_namespace(output_path, blocks_by_ns, items_by_ns, fluids_by_ns, mods, namespace_to_mod_map)
    
    # Save mod summaries
    logger.info("Building mod summaries from disk files...")
    save_mods_from_disk(output_path, mods, namespace_to_mod_map, blocks_by_ns, items_by_ns, 
                         fluids_by_ns)
    
    # Save summary (needs to read metadata from disk)
    logger.info("Generating summary...")
    save_summary_from_disk(output_path, mods, namespaces, tag_metadata, recipe_metadata, 
                           categories, blocks_by_ns, items_by_ns, fluids_by_ns)
    
    print()
    print_separator()
    print("SCAN COMPLETE!")
    print_separator()
    print(f"\nResults saved to '{output_dir}/' directory")


__all__ = ['scan', 'discover_mods_and_namespaces']

