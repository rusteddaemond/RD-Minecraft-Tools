#!/usr/bin/env python3
"""
Items Scanner for Minecraft Mods
---------------------------------

Scans JAR files for item assets (models, textures) and extracts them
by namespace with intelligent cleaning to remove file extensions and affixes.

Usage:
    python -m tools.scanners.items_scanner [options]
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config_loader import load_paths_from_config, get_default_paths
from src.arg_parser import get_thread_count
from src.models.scanner import ScannerConfig
from src.processors.scanner import AssetScannerProcessor, ItemsEntryFilter
from src.processors.cleaner import IdentifierCleaner
from src.processors.file_io import FileIOProcessor
from src.processors.jar.reader import JarReader
from src.services.scanner_service import ScannerService
from tools.interfaces.scanner_args import (
    add_scanner_input_args,
    add_scanner_cleaning_args
)


def main() -> None:
    """Main entry point for items scanner."""
    parser = argparse.ArgumentParser(
        description="Scan JAR files for item assets and extract them by namespace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan JARs using default paths
  python -m tools.scanners.items_scanner
  
  # Use config file for paths
  python -m tools.scanners.items_scanner --config paths.json
  
  # Filter by namespace
  python -m tools.scanners.items_scanner --namespace minecraft
  
  # Cleaning is now automatic and thorough (convergence-based)
        """
    )
    
    # Add shared scanner arguments
    add_scanner_input_args(parser)
    add_scanner_cleaning_args(parser)
    
    args = parser.parse_args()
    
    # Load paths from config
    paths = load_paths_from_config(args.config) if args.config else get_default_paths()
    
    # Create output directories
    jar_reader = JarReader()
    raw_dir, cleaned_dir = jar_reader.create_output_dirs("items", paths)
    
    # Create scanner configuration
    config = ScannerConfig(
        input_dir=paths.mods,
        output_dir=cleaned_dir,
        raw_dir=raw_dir,
        category="items",
        category_suffix="_items",
        max_workers=get_thread_count(args),
        namespace_filter=getattr(args, 'namespace', None),
        skip_raw=getattr(args, 'skip_raw', False),
        verbose=getattr(args, 'verbose', False)
    )
    
    # Create components
    entry_filter = ItemsEntryFilter()
    cleaner = IdentifierCleaner()
    processor = AssetScannerProcessor(entry_filter, cleaner)
    file_io = FileIOProcessor()
    
    # Create service and run
    service = ScannerService(processor, file_io, cleaner)
    service.run_scan(config)


if __name__ == "__main__":
    main()
