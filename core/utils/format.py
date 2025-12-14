"""
Formatting utilities for console and file output.
"""

from core.constants import DisplayConstants


def print_separator(width: int = None) -> None:
    """
    Print a separator line to console.
    
    Args:
        width: Width of separator (default: DisplayConstants.SEPARATOR_WIDTH)
    """
    if width is None:
        width = DisplayConstants.SEPARATOR_WIDTH
    print("=" * width)


def print_subseparator(width: int = None) -> None:
    """
    Print a sub-separator line (dashes) to console.
    
    Args:
        width: Width of separator (default: DisplayConstants.SEPARATOR_WIDTH)
    """
    if width is None:
        width = DisplayConstants.SEPARATOR_WIDTH
    print("-" * width)


def format_separator(width: int = None) -> str:
    """
    Return a separator string for file output.
    
    Args:
        width: Width of separator (default: DisplayConstants.SEPARATOR_WIDTH)
        
    Returns:
        Separator string
    """
    if width is None:
        width = DisplayConstants.SEPARATOR_WIDTH
    return "=" * width


def format_subseparator(width: int = None) -> str:
    """
    Return a sub-separator string (dashes) for file output.
    
    Args:
        width: Width of separator (default: DisplayConstants.SEPARATOR_WIDTH)
        
    Returns:
        Sub-separator string
    """
    if width is None:
        width = DisplayConstants.SEPARATOR_WIDTH
    return "-" * width

