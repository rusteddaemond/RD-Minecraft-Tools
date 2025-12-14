"""
Constants used throughout the application.
Centralizes magic strings, numbers, and configuration values.
"""

from pathlib import Path


class DefaultDirs:
    """Default directory paths used throughout the application."""
    MODS = Path('mods')
    SCAN_OUTPUT = Path('scan_output')
    FIND_OUTPUT = Path('./find_output')
    BUILD_OUTPUT = Path('./build_output/datapacks')
    
    # Subdirectories
    SCAN_ITEMS = SCAN_OUTPUT / 'items' / 'installed'
    SCAN_BLOCKS = SCAN_OUTPUT / 'blocks' / 'installed'
    SCAN_FLUIDS = SCAN_OUTPUT / 'fluids' / 'installed'


class FilePatterns:
    """File naming patterns and extensions."""
    TXT_EXTENSION = ".txt"
    JSON_EXTENSION = ".json"
    SUMMARY_SUFFIX = "_summary.txt"
    WORK_SUFFIX = "_work"
    INSTALLED_MODS_SUMMARY = "installed_mods_summary.txt"


class DisplayConstants:
    """Constants for display formatting."""
    SEPARATOR_WIDTH = 60
    TOP_PAIRS_LIMIT = 10
    DEFAULT_MIN_MATCHES = 1

