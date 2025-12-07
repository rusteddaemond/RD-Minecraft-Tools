#!/usr/bin/env python3
"""
Unified JAR Asset Scanner (Triple-Pass Cleaning + Raw Backups + Extended Affixes)
---------------------------------------------------------------------------

Scans JAR files for block/item assets (models, textures) and extracts them
by namespace with intelligent cleaning to remove file extensions and affixes.

Usage:
    python -m tools.asset_scanner [options]
"""

from __future__ import annotations
import argparse
import sys
import zipfile
import traceback
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils import write_entry, log
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


# ---------------------------------------------------------------------
# Extended affix definitions
# ---------------------------------------------------------------------
AFFIX_GROUPS: Dict[str, List[str]] = {
    # State / orientation affixes grouped by meaning
    "orientation_faces": [
        "_bottom", "_top", "_front", "_back", "_left", "_right", "_side", "_reverse", "_base"
    ],
    "orientation_corners": [
        "_corner", "_inner", "_outer", "_noside", "_nosides", "_inside"
    ],
    "orientation_vertical": [
        "_up", "_down", "_upper", "_lower", "_middle", "_mid", "_center", "_centered", "_main", "_full"
    ],
    "orientation_horizontal": [
        "_horizontal", "_ew", "_ns", "_x", "_z"
    ],
    "orientation_end": [
        "_end", "_post", "_even", "_odd", "_foot", "_head", "_far", "_gate_wall"
    ],
    "orientation_size": [
        "_single", "_double", "_tall", "_plus", "_adv"
    ],
    "state_binary": [
        "_open", "_opened", "_close", "_closed", "_on", "_off", "_pressed", "_extended",
        "_connected", "_occupied", "_empty", "_filled", "_drained",
        "_activated", "_lit", "_weak", "_supported", "_support",
        "_moist", "_unused", "_alt", "_wet", "_decorated", "_tied",
        "_extrudes", "_garnish", "_leftover", "_active", "_inactive",
        "_monster", "_player", "_emissive", "_body", "_bone", "_stabilized", "_unlinked"
    ],
    "state_progression": [
        "_new", "_old",
        "_one", "_two", "_three", "_four", "_five",
        "_0", "_1", "_2", "_3", "_4", "_5", "_6", "_7", "_8", "_9", "_10",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
        "_age0", "_age1", "_age2", "_age3", "_age4", "_age5",
        "_age6", "_age7", "_age8", "_age9", "_age10", "_stage",
        "_stage0", "_stage1", "_stage2", "_stage3", "_stage4", "_stage5",
        "_stage6", "_stage7", "_stage8", "_stage9", "_stage10",
        "_slice0", "_slice1", "_slice2", "_slice3", "_slice4", "_slice5",
        "_slice6", "_slice7", "_slice8", "_slice9", "_slice10", "_level",
        "_level0", "_level1", "_level2", "_level3", "_level4", "_level5",
        "_level6", "_level7", "_level8", "_level9", "_level10"
    ],
    "state_content": [
        "_honey", "_water"
    ],
    "inventory": [
        "_inventory", "_slot"
    ],
    "ctm_meta": [
        "-ctm"
    ],
    "misc_suffixes": [
        "_with", "_t"
    ]
}

# Flatten all affixes into one list for fast lookup
AFFIXES: List[str] = [a for group in AFFIX_GROUPS.values() for a in group]

# File extensions to remove
EXTENSIONS: Tuple[str, ...] = (".png", ".jpeg", ".jpg", ".gif")


# ---------------------------------------------------------------------
# Cleansing function
# ---------------------------------------------------------------------
def clean_identifier(stem: str, passes: int = 3) -> str:
    """Remove file extensions and grouped affixes recursively.
    
    Args:
        stem: The identifier to clean
        passes: Number of cleaning passes to perform
        
    Returns:
        Cleaned identifier
    """
    for _ in range(passes):
        for ext in EXTENSIONS:
            if stem.endswith(ext):
                stem = stem[:-len(ext)]
        for affix in AFFIXES:
            if stem.endswith(affix):
                stem = stem[:-len(affix)]
    return stem




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
                write_entry(raw_blocks_dir / f"{ns}_blocks_raw.txt", lines)
            for ns, lines in items_buffer.items():
                write_entry(raw_items_dir / f"{ns}_items_raw.txt", lines)

        log(f"Scanned {jar_path.name}", "OK")

    except zipfile.BadZipFile:
        log(f"Bad zip file: {jar_path.name}", "WARN")
    except Exception as e:
        log(f"{jar_path.name}: {e}", "ERROR")
        traceback.print_exc()


# ---------------------------------------------------------------------
# Phase 2 — Triple-pass cleaning
# ---------------------------------------------------------------------
def clean_results(raw_dir: Path, cleaned_dir: Path, suffix: str, clean_passes: int = 3, skip_raw: bool = False) -> None:
    """Clean all *_raw.txt files and output cleaned files.
    
    Args:
        raw_dir: Directory containing raw files (logs)
        cleaned_dir: Directory for cleaned output files (output)
        suffix: Suffix pattern to match (e.g., "_blocks")
        clean_passes: Number of cleaning passes to perform
        skip_raw: If True, delete raw files after cleaning
    """
    for raw_file in raw_dir.glob(f"*{suffix}_raw.txt"):
        try:
            cleaned_name = raw_file.name.replace("_raw.txt", ".txt")
            cleaned_path = cleaned_dir / cleaned_name

            with raw_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()

            cleaned: set[str] = set()
            for line in lines:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                ns, stem = line.split(":", 1)
                stem = clean_identifier(stem, passes=clean_passes)
                cleaned.add(f"{ns}:{stem}")

            sorted_lines = sorted(cleaned)
            with cleaned_path.open("w", encoding="utf-8") as f:
                for entry in sorted_lines:
                    f.write(entry + "\n")

            log(f"{cleaned_path.name}: {len(sorted_lines)} entries (from {raw_file.name})", "CLEAN x3")
            
            if skip_raw:
                raw_file.unlink()

        except Exception as e:
            log(f"{raw_file.name}: {e}", "ERROR CLEAN")


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
  # Scan JARs in current directory
  python -m tools.asset_scanner
  
  # Scan JARs in specific directory
  python -m tools.asset_scanner --input-dir ./mods
  
  # Filter by namespace
  python -m tools.asset_scanner --namespace minecraft
  
  # Custom cleaning passes
  python -m tools.asset_scanner --clean-passes 5
        """
    )
    
    # Add common arguments
    add_common_jar_args(parser)
    add_namespace_filter_arg(parser)
    
    parser.add_argument(
        "--clean-passes",
        type=int,
        default=3,
        help="Number of cleaning passes (default: 3)"
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    try:
        validate_input_directory(args.input_dir)
    except ValueError as e:
        log(str(e), "ERROR")
        sys.exit(1)
    
    # Find JAR files
    try:
        jars = find_jar_files(args.input_dir)
    except ValueError as e:
        log(str(e), "ERROR")
        sys.exit(1)
    
    # Create output directories
    raw_blocks_dir, cleaned_blocks_dir = create_output_dirs("blocks")
    raw_items_dir, cleaned_items_dir = create_output_dirs("items")
    
    # Determine thread count
    max_workers = get_thread_count(args)
    
    # Create wrapper function for process_jar that captures directories and namespace
    def process_jar_wrapper(jar_path: Path) -> None:
        """Wrapper to adapt process_jar for execute_concurrent."""
        process_jar(jar_path, raw_blocks_dir, raw_items_dir, args.namespace)
    
    # Phase 1: Scanning
    log(f"Found {len(jars)} JAR(s). Scanning with {max_workers} threads...")
    execute_concurrent(jars, process_jar_wrapper, max_workers=max_workers, verbose=args.verbose)
    
    # Phase 2: Cleaning
    log("Starting cleaning of gathered results...")
    clean_results(raw_blocks_dir, cleaned_blocks_dir, "_blocks", args.clean_passes, args.skip_raw)
    clean_results(raw_items_dir, cleaned_items_dir, "_items", args.clean_passes, args.skip_raw)
    
    log(f"Completed. Clean files in:\n  {cleaned_blocks_dir.resolve()}\n  {cleaned_items_dir.resolve()}")
    log(f"Raw files in:\n  {raw_blocks_dir.resolve()}\n  {raw_items_dir.resolve()}")


if __name__ == "__main__":
    main()

