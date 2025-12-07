#!/usr/bin/env python3
"""
Unified JAR Asset Scanner
-------------------------

Scans JAR files for block/item assets (models, textures) and extracts them
by namespace with thorough convergence-based cleaning to remove file extensions and affixes.

Usage:
    python -m tools.asset_scanner [options]
"""

from __future__ import annotations
import argparse
import sys
import zipfile
import traceback
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils import log
from src.file_operations import append_text_lines
from src.jar_processor import (
    validate_input_directory,
    find_jar_files,
    create_output_dirs
)
from src.arg_parser import (
    add_common_jar_args,
    add_namespace_filter_arg,
    get_thread_count
)
from src.thread_pool import execute_concurrent
from src.config_loader import load_paths_from_config, get_default_paths
from src.scanner_common import clean_results


# Note: Affix definitions and cleaning are now in src.affix_cleaner and src.identifier_cleaner




# ---------------------------------------------------------------------
# Phase 1 — Scan JARs
# ---------------------------------------------------------------------
def process_jar(jar_path: Path, raw_blocks_dir: Path, raw_items_dir: Path, namespace_filter: str | None = None) -> None:
    """Scan a single JAR and append raw entries per namespace.
    
    Args:
        jar_path: Path to the JAR file
        raw_blocks_dir: Directory for raw block outputs (logs/blocks)
        raw_items_dir: Directory for raw item outputs (logs/items)
        namespace_filter: Optional namespace to filter by
    """
    try:
        with zipfile.ZipFile(jar_path, "r") as zf:
            blocks_buffer: Dict[str, List[str]] = {}
            items_buffer: Dict[str, List[str]] = {}

            for name in zf.namelist():
                parts = name.split("/")
                if len(parts) < 4 or parts[0] != "assets":
                    continue
                namespace = parts[1]
                
                # Apply namespace filter if specified
                if namespace_filter and namespace.lower() != namespace_filter.lower():
                    continue
                
                category = parts[2:4]

                if category in (["models", "block"], ["textures", "block"]):
                    target = blocks_buffer
                elif category in (["models", "item"], ["textures", "item"]):
                    target = items_buffer
                else:
                    continue

                if name.endswith("/"):
                    continue

                stem = Path(name).stem
                target.setdefault(namespace, []).append(f"{namespace}:{stem}\n")

            for ns, lines in blocks_buffer.items():
                append_text_lines(raw_blocks_dir / f"{ns}_blocks_raw.txt", lines)
            for ns, lines in items_buffer.items():
                append_text_lines(raw_items_dir / f"{ns}_items_raw.txt", lines)

        log(f"Scanned {jar_path.name}", "OK")

    except zipfile.BadZipFile:
        log(f"Bad zip file: {jar_path.name}", "WARN")
    except Exception as e:
        log(f"{jar_path.name}: {e}", "ERROR")
        traceback.print_exc()


# Note: Cleaning is now handled by src.scanner_common.clean_results


# ---------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------
def main() -> None:
    """Main entry point for asset scanner."""
    parser = argparse.ArgumentParser(
        description="Scan JAR files for block/item assets and extract them by namespace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan JARs using default paths
  python -m tools.asset_scanner
  
  # Use config file for paths
  python -m tools.asset_scanner --config paths.json
  
  # Filter by namespace
  python -m tools.asset_scanner --namespace minecraft
  
  # Cleaning is now automatic and thorough
        """
    )
    
    # Add common arguments
    add_common_jar_args(parser)
    add_namespace_filter_arg(parser)
    
    # Note: Cleaning is now thorough and automatic (convergence-based)
    
    args = parser.parse_args()
    
    # Load paths from config
    paths = load_paths_from_config(args.config) if args.config else get_default_paths()
    
    # Use mods directory from config
    input_dir = paths.mods
    
    # Validate input directory
    try:
        validate_input_directory(input_dir)
    except ValueError as e:
        log(str(e), "ERROR")
        sys.exit(1)
    
    # Find JAR files
    try:
        jars = find_jar_files(input_dir)
    except ValueError as e:
        log(str(e), "ERROR")
        sys.exit(1)
    
    # Create output directories using config paths
    raw_blocks_dir, cleaned_blocks_dir = create_output_dirs("blocks", paths)
    raw_items_dir, cleaned_items_dir = create_output_dirs("items", paths)
    
    # Determine thread count
    max_workers = get_thread_count(args)
    
    # Create wrapper function for process_jar that captures directories and namespace
    def process_jar_wrapper(jar_path: Path) -> None:
        """Wrapper to adapt process_jar for execute_concurrent."""
        process_jar(jar_path, raw_blocks_dir, raw_items_dir, args.namespace)
    
    # Phase 1: Scanning
    log(f"Found {len(jars)} JAR(s). Scanning with {max_workers} threads...")
    execute_concurrent(jars, process_jar_wrapper, max_workers=max_workers, verbose=args.verbose)
    
    # Phase 2: Cleaning (using shared thorough cleaning)
    log("Starting thorough cleaning of gathered results...")
    clean_results(raw_blocks_dir, cleaned_blocks_dir, "_blocks", args.skip_raw)
    clean_results(raw_items_dir, cleaned_items_dir, "_items", args.skip_raw)
    
    log(f"Completed. Clean files in:\n  {cleaned_blocks_dir.resolve()}\n  {cleaned_items_dir.resolve()}")
    log(f"Raw files in:\n  {raw_blocks_dir.resolve()}\n  {raw_items_dir.resolve()}")


if __name__ == "__main__":
    main()

