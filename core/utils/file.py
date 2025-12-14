"""
Shared utilities for reading item files.

This module provides functions for reading Minecraft item identifiers from text files,
with consistent handling of comments, tag references, and metadata.

Used by both scanner and builder modules.
"""

from typing import Iterator
from pathlib import Path
from .item import is_tag_reference, is_valid_item_id


def read_item_lines(
    file_path: Path,
    skip_comments: bool = True,
    skip_tag_refs: bool = False,
    handle_metadata: bool = False
) -> Iterator[str]:
    """
    Read item IDs from a file, line by line.
    
    Args:
        file_path: Path to the file to read
        skip_comments: If True, skip lines starting with '#' (default: True)
        skip_tag_refs: If True, skip tag references (lines starting with '#') (default: False)
        handle_metadata: If True, take first space-separated token from each line (default: False)
                        Useful for files with metadata like recipe files
    
    Yields:
        Item ID strings in namespace:id format
    
    Examples:
        >>> from pathlib import Path
        >>> # Read simple item list
        >>> for item in read_item_lines(Path('items.txt')):
        ...     print(item)
        'minecraft:stone'
        'forge:iron_ingot'
        
        >>> # Read recipe file with metadata
        >>> for item in read_item_lines(Path('recipe.txt'), handle_metadata=True):
        ...     print(item)
        'minecraft:stone'  # from line "minecraft:stone Inputs: ..."
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Handle comments and tag references
                if skip_comments and line.startswith('#'):
                    # Check if it's a special tag marker (like #TAG:namespace:tag)
                    if line.startswith('#TAG:'):
                        # Skip the tag marker line itself
                        continue
                    elif skip_tag_refs:
                        continue
                
                # Extract item ID
                if handle_metadata:
                    # Take first space-separated token (for files with metadata)
                    parts = line.split()
                    if not parts:
                        continue
                    item_id = parts[0]
                else:
                    item_id = line
                
                # Validate and yield item ID
                if is_valid_item_id(item_id):
                    yield item_id
                elif not skip_tag_refs and is_tag_reference(item_id):
                    # Yield tag references if not skipping them
                    yield item_id
    except (IOError, OSError, UnicodeDecodeError):
        # Silently handle file errors (caller can check if file exists)
        return


def read_items_from_file(
    file_path: Path,
    skip_comments: bool = True,
    skip_tag_refs: bool = False,
    handle_metadata: bool = False
) -> set[str]:
    """
    Read all item IDs from a file into a set.
    
    This is a convenience function that collects all items from read_item_lines()
    into a set, automatically deduplicating.
    
    Args:
        file_path: Path to the file to read
        skip_comments: If True, skip lines starting with '#' (default: True)
        skip_tag_refs: If True, skip tag references (default: False)
        handle_metadata: If True, take first space-separated token (default: False)
    
    Returns:
        Set of item ID strings. Empty set if file doesn't exist or cannot be read.
    
    Examples:
        >>> from pathlib import Path
        >>> items = read_items_from_file(Path('items.txt'))
        >>> print(items)
        {'minecraft:stone', 'forge:iron_ingot'}
    """
    if not file_path.exists() or not file_path.is_file():
        return set()
    
    return set(read_item_lines(file_path, skip_comments, skip_tag_refs, handle_metadata))

