"""
User interface functions for interactive selection.

This module provides interactive command-line interfaces for selecting
namespaces and mod pairs during the datapack building process.
"""

import sys
from typing import Dict, Set, List

from core.builder.models import ModPair
from core.utils.format import print_separator


def display_namespace_selection(by_namespace: Dict[str, Set[str]]) -> str:
    """
    Display namespaces with item counts and let user select one.
    
    Args:
        by_namespace: Dictionary mapping namespace to set of items.
            Must not be empty.
        
    Returns:
        Selected namespace string
        
    Raises:
        ValueError: If by_namespace is empty
        SystemExit: If user cancels (Ctrl+C)
    """
    if not by_namespace:
        raise ValueError("Cannot display namespace selection: no namespaces provided")
    
    print()
    print_separator()
    print("Available Namespaces:")
    print_separator()
    
    # Sort by namespace name
    sorted_namespaces = sorted(by_namespace.items(), key=lambda x: x[0])
    
    # Display with item counts
    namespace_list = []
    for idx, (namespace, items) in enumerate(sorted_namespaces, 1):
        count = len(items)
        print(f"  {idx:3d}. {namespace:30s} ({count:5d} items)")
        namespace_list.append(namespace)
    
    print_separator()
    
    # Get user selection
    while True:
        try:
            selection = input(f"\nSelect namespace to use as result (1-{len(namespace_list)}): ").strip()
            idx = int(selection) - 1
            if 0 <= idx < len(namespace_list):
                return namespace_list[idx]
            else:
                print(f"Please enter a number between 1 and {len(namespace_list)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nCancelled by user")
            sys.exit(1)


def display_mod_pairs(pairs: List[ModPair]) -> ModPair:
    """
    Display mod pairs and let user select one.
    
    Args:
        pairs: List of ModPair objects (will be sorted alphabetically for display)
        
    Returns:
        Selected ModPair object
        
    Raises:
        SystemExit: If user cancels or no pairs available
    """
    if not pairs:
        print("No mod pairs found with overlapping base names.")
        sys.exit(1)
    
    # Sort pairs alphabetically by mod names
    sorted_pairs = sorted(pairs, key=lambda p: (p.mod1.lower(), p.mod2.lower()))
    
    print()
    print_separator()
    print("Available Mod Pairs (sorted alphabetically):")
    print_separator()
    
    for idx, pair in enumerate(sorted_pairs, 1):
        print(f"  {idx:3d}. {pair.mod1} + {pair.mod2} ({pair.match_count} matching base names)")
    
    print_separator()
    
    # Get user selection
    while True:
        try:
            selection = input(f"\nSelect pair (1-{len(sorted_pairs)}): ").strip()
            idx = int(selection) - 1
            if 0 <= idx < len(sorted_pairs):
                return sorted_pairs[idx]
            else:
                print(f"Please enter a number between 1 and {len(sorted_pairs)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nCancelled by user")
            sys.exit(1)

