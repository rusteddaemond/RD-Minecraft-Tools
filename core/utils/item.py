"""
Shared utilities for working with Minecraft item identifiers.

This module provides functions for parsing, validating, and manipulating
Minecraft item/block/fluid identifiers in the format namespace:id.

Used by both scanner and builder modules.
"""


def extract_namespace(item_id: str) -> str | None:
    """
    Extract namespace from an item ID.
    
    Args:
        item_id: Item ID in format 'namespace:item_name' or '#namespace:tag_name'
    
    Returns:
        Namespace string or None if invalid format
    
    Examples:
        >>> extract_namespace('minecraft:stone')
        'minecraft'
        >>> extract_namespace('#forge:ores')
        'forge'
        >>> extract_namespace('invalid')
        None
    """
    if not item_id or ':' not in item_id:
        return None
    
    # Remove tag prefix if present
    clean_id = item_id.lstrip('#')
    return clean_id.split(':', 1)[0]


def get_base_name(item_id: str, is_fluid: bool = False) -> str:
    """
    Extract the base name from an item ID (the part after namespace:).
    
    Args:
        item_id: Item ID in format namespace:id
        is_fluid: Whether to normalize flowing_* fluids (removes 'flowing_' prefix)
    
    Returns:
        Base name (id part) of the item. Returns full item_id if no ':' found.
    
    Examples:
        >>> get_base_name('minecraft:stone')
        'stone'
        >>> get_base_name('minecraft:flowing_water', is_fluid=True)
        'water'
        >>> get_base_name('minecraft:flowing_water', is_fluid=False)
        'flowing_water'
    """
    if ':' not in item_id:
        return item_id
    
    base = item_id.split(':', 1)[1]
    
    # For fluids, normalize flowing_* to the base name
    if is_fluid and base.startswith('flowing_'):
        base = base[8:]  # Remove 'flowing_' prefix
    
    return base


def is_tag_reference(item_id: str) -> bool:
    """
    Check if an item ID is a tag reference.
    
    Args:
        item_id: Item ID to check
    
    Returns:
        True if item_id starts with '#', False otherwise
    
    Examples:
        >>> is_tag_reference('#forge:ores')
        True
        >>> is_tag_reference('minecraft:stone')
        False
    """
    return item_id.startswith('#')


def is_valid_item_id(item_id: str) -> bool:
    """
    Check if an item ID has valid format.
    
    Args:
        item_id: Item ID to validate
    
    Returns:
        True if item_id contains ':' and is not empty, False otherwise.
        Tag references (starting with '#') are considered invalid item IDs.
    
    Examples:
        >>> is_valid_item_id('minecraft:stone')
        True
        >>> is_valid_item_id('#forge:ores')
        False
        >>> is_valid_item_id('invalid')
        False
    """
    return bool(item_id and ':' in item_id and not item_id.startswith('#'))


def sanitize_filename(name: str) -> str:
    """
    Sanitize a name for use as a filename.
    
    Replaces ':', '/', and '#' with safe alternatives that are valid in filenames.
    
    Args:
        name: Name to sanitize (e.g., 'minecraft:stone' or '#forge:ores')
    
    Returns:
        Sanitized filename-safe string
    
    Examples:
        >>> sanitize_filename('minecraft:stone')
        'minecraft_stone'
        >>> sanitize_filename('#forge:ores')
        'tag_forge_ores'
        >>> sanitize_filename('mod/name')
        'mod_name'
    """
    return name.replace(':', '_').replace('/', '_').replace('#', 'tag_')

