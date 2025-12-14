"""
Unified Core Module
Consolidates scanner and builder functionality into a single module.
"""

# Scanner exports
from core.scanner import scan, discover_mods_and_namespaces

# Builder exports
from core.builder import DatapackType, DatapackConfig, ModPair, DATAPACK_CONFIGS
from core.builder.processors import FileParser, ItemGrouper, PairScanner, DatapackBuilder
from core.builder.ui import display_namespace_selection, display_mod_pairs

# Finder
from core.finder import save_pairs, save_summary

__all__ = [
    # Scanner
    'scan',
    'discover_mods_and_namespaces',
    # Builder models
    'DatapackType',
    'DatapackConfig',
    'ModPair',
    'DATAPACK_CONFIGS',
    # Builder processors
    'FileParser',
    'ItemGrouper',
    'PairScanner',
    'DatapackBuilder',
    # Builder UI
    'display_namespace_selection',
    'display_mod_pairs',
    # Finder
    'save_pairs',
    'save_summary',
]

