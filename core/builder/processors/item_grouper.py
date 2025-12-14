"""
Item grouping utilities for organizing items by namespace and base name.

This module provides functionality to group Minecraft item/block/fluid identifiers
by namespace or by base name (the part after the colon), with special handling
for fluid normalization (flowing_* variants).
"""

from collections import defaultdict
from typing import Set, Dict
from core.utils.item import extract_namespace, get_base_name


class ItemGrouper:
    """Utilities for grouping items by namespace and base name."""
    
    @staticmethod
    def group_by_namespace(items: Set[str]) -> Dict[str, Set[str]]:
        """
        Group items by namespace.
        
        Args:
            items: Set of namespace:id entries. Empty set returns empty dict.
            
        Returns:
            Dictionary mapping namespace to set of items in that namespace.
            Items without a colon (invalid format) are skipped.
        """
        if not items:
            return {}
        
        by_namespace = defaultdict(set)
        
        for item in items:
            namespace = extract_namespace(item)
            if namespace:  # Skip empty/invalid namespaces
                by_namespace[namespace].add(item)
        
        return dict(by_namespace)  # Convert to regular dict for immutability
    
    @staticmethod
    def get_base_name(item_id: str, is_fluid: bool = False) -> str:
        """
        Extract the base name from an item ID (the part after namespace:).
        
        Args:
            item_id: Item ID in format namespace:id
            is_fluid: Whether to normalize flowing_* fluids
        
        Returns:
            Base name (id part) of the item
        
        Note:
            This method delegates to core.common.item_utils.get_base_name() for consistency.
        """
        return get_base_name(item_id, is_fluid)
    
    @staticmethod
    def group_by_base_name(items: Set[str], is_fluid: bool = False) -> Dict[str, Dict[str, Set[str]]]:
        """
        Group items by base name, then by namespace.
        
        Args:
            items: Set of namespace:id entries
            is_fluid: Whether to use fluid normalization
            
        Returns:
            Dictionary mapping base_name to namespace to set of items
            Format: {base_name: {namespace: {items}}}
        """
        by_base_name = defaultdict(lambda: defaultdict(set))
        
        for item in items:
            if ':' not in item:
                continue
            
            base_name = ItemGrouper.get_base_name(item, is_fluid)
            namespace = extract_namespace(item)
            if namespace:  # Only add if namespace is valid
                by_base_name[base_name][namespace].add(item)
        
        return by_base_name
    
    @staticmethod
    def get_result_item(items: Set[str], is_fluid: bool = False) -> str:
        """
        Get the best result item from a set, filtering out flowing fluids if needed.
        
        Args:
            items: Set of item IDs. Must not be empty.
            is_fluid: Whether to prefer non-flowing fluids
            
        Returns:
            Best item ID from the set. For fluids, prefers non-flowing variants.
            For non-fluids or when no non-flowing variant exists, returns
            lexicographically first item.
            
        Raises:
            ValueError: If items set is empty
        """
        if not items:
            raise ValueError("Cannot get result item from empty set")
        
        sorted_items = sorted(items)
        
        if is_fluid:
            # Prefer non-flowing fluids
            non_flowing = [item for item in sorted_items if not item.split(':')[-1].startswith('flowing_')]
            if non_flowing:
                return non_flowing[0]
        
        return sorted_items[0]

