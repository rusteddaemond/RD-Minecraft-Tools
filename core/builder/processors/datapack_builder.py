"""
Datapack builder for creating One Enough datapack files.

This module provides functionality to create Minecraft datapacks for the
One Enough mod series (One Enough Item, One Enough Block, One Enough Fluid).
"""

import json
from pathlib import Path
from typing import Set

from core.builder.models import DatapackConfig
from core.builder.processors.item_grouper import ItemGrouper


class DatapackBuilder:
    """Builder for creating datapack files with replacement rules."""
    
    def __init__(self, item_grouper: ItemGrouper):
        """
        Initialize DatapackBuilder.
        
        Args:
            item_grouper: ItemGrouper instance for grouping items
        """
        self.item_grouper = item_grouper
    
    def create_datapack(
        self,
        items: Set[str],
        result_namespace: str,
        output_dir: Path,
        datapack_name: str,
        config: DatapackConfig
    ) -> None:
        """
        Create datapack with replacement rules.
        
        Args:
            items: Set of all namespace:id entries. Must not be empty.
            result_namespace: Namespace to use as result (target namespace).
                Must exist in the items set.
            output_dir: Directory to create datapack in. Will be created if it doesn't exist.
            datapack_name: Name of the datapack directory. Should be a valid directory name.
            config: DatapackConfig with type-specific settings
            
        Raises:
            ValueError: If items is empty or result_namespace not found in items
            OSError: If output directory cannot be created or files cannot be written
        """
        if not items:
            raise ValueError("Cannot create datapack from empty items set")
        
        # Validate result_namespace exists in items
        from core.utils.item import extract_namespace
        namespaces = {extract_namespace(item) for item in items}
        namespaces.discard(None)  # Remove None values from invalid items
        if result_namespace not in namespaces:
            raise ValueError(
                f"Result namespace '{result_namespace}' not found in items. "
                f"Available namespaces: {', '.join(sorted(namespaces))}"
            )
        # Group items by base name
        by_base_name = self.item_grouper.group_by_base_name(items, is_fluid=config.is_fluid)
        
        # Create datapack structure
        datapack_dir = output_dir / datapack_name
        replacements_dir = datapack_dir / 'data' / config.type.value / 'replacements'
        try:
            replacements_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"Failed to create datapack directory {replacements_dir}: {e}") from e
        
        # Create replacement rules - match similar items to similar items
        replacements = []
        matched_count = 0
        unmatched_count = 0
        
        for base_name, namespace_items in sorted(by_base_name.items()):
            # Check if result namespace has an item with this base name
            result_items = namespace_items.get(result_namespace, set())
            
            if not result_items:
                # No matching item in result namespace, skip this base name
                unmatched_count += sum(len(items) for ns, items in namespace_items.items() if ns != result_namespace)
                continue
            
            # Get the result item (prefer non-flowing for fluids)
            result_item = self.item_grouper.get_result_item(result_items, is_fluid=config.is_fluid)
            
            # Collect all items from other namespaces with this base name
            match_items = []
            for namespace, namespace_item_set in namespace_items.items():
                if namespace != result_namespace:
                    match_items.extend(sorted(namespace_item_set))
            
            if match_items:
                replacements.append({
                    config.match_key: match_items,
                    config.result_key: result_item
                })
                matched_count += len(match_items)
        
        from core.utils.logging import log_warning
        if not replacements:
            log_warning("No matching items found to create replacement rules")
            print(f"  (No items from other namespaces match base names in '{result_namespace}')")
            return
        
        # Write replacement file (named after result namespace)
        replacement_file = replacements_dir / f'{result_namespace}.json'
        try:
            with open(replacement_file, 'w', encoding='utf-8') as f:
                json.dump(replacements, f, indent=2)
        except (IOError, OSError) as e:
            raise OSError(f"Failed to write replacement file {replacement_file}: {e}") from e
        
        # Create pack.mcmeta
        pack_mcmeta = datapack_dir / 'pack.mcmeta'
        try:
            with open(pack_mcmeta, 'w', encoding='utf-8') as f:
                json.dump({
                    "pack": {
                        "pack_format": 15,
                        "description": f"{config.description} replacements - {datapack_name}"
                    }
                }, f, indent=2)
        except (IOError, OSError) as e:
            raise OSError(f"Failed to write pack.mcmeta {pack_mcmeta}: {e}") from e
        
        print(f"\nCreated {config.type.value.upper()} datapack at: {datapack_dir}")
        print(f"  Replacement rules: {len(replacements)}")
        print(f"  Matched items: {matched_count}")
        if unmatched_count > 0:
            print(f"  Unmatched items (no equivalent in result namespace): {unmatched_count}")
        print(f"  Result namespace: {result_namespace}")

