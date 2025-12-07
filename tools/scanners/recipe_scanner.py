#!/usr/bin/env python3
"""
Per-Namespace Recipe Result Extractor
--------------------------------------

Scans JAR files for JSON recipes and extracts recipe results by namespace.
By default excludes 'minecraft:' recipes.

Usage:
    python -m tools.scanners.recipe_scanner [options]
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
from src.processors.scanner import RecipeScannerProcessor
from src.processors.file_io import FileIOProcessor
from src.processors.jar.reader import JarReader
from src.services.scanner_service import ScannerService
from tools.interfaces.scanner_args import add_scanner_input_args


def main() -> None:
    """Main entry point for recipe scanner."""
    parser = argparse.ArgumentParser(
        description="Scan JAR files for recipes and extract results by namespace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan JARs using default paths (exclude minecraft recipes)
  python -m tools.scanners.recipe_scanner
  
  # Include minecraft recipes
  python -m tools.scanners.recipe_scanner --include-minecraft
  
  # Use config file for paths
  python -m tools.scanners.recipe_scanner --config paths.json
        """
    )
    
    # Add shared scanner arguments
    add_scanner_input_args(parser)
    
    parser.add_argument(
        "--include-minecraft",
        action="store_true",
        help="Include minecraft: recipes (default: exclude)"
    )
    
    args = parser.parse_args()
    
    # Load paths from config
    paths = load_paths_from_config(args.config) if args.config else get_default_paths()
    
    # Create output directories
    jar_reader = JarReader()
    raw_dir, cleaned_dir = jar_reader.create_output_dirs("recipes", paths)
    
    # Create scanner configuration
    config = ScannerConfig(
        input_dir=paths.mods,
        output_dir=cleaned_dir,
        raw_dir=raw_dir,
        category="recipes",
        category_suffix="_recipes",
        max_workers=get_thread_count(args),
        namespace_filter=getattr(args, 'namespace', None),
        skip_raw=getattr(args, 'skip_raw', False),
        verbose=getattr(args, 'verbose', False)
    )
    
    # Create components (RecipeScannerProcessor handles its own cleaning)
    processor = RecipeScannerProcessor(include_minecraft=getattr(args, 'include_minecraft', False))
    file_io = FileIOProcessor()
    
    # Create service and run (no cleaner needed - RecipeScannerProcessor handles it)
    service = ScannerService(processor, file_io, cleaner=None)
    service.run_scan(config)


if __name__ == "__main__":
    main()
