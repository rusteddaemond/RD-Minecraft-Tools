#!/usr/bin/env python3
"""
Per-Namespace Recipe Result Extractor
--------------------------------------

Scans JAR files for JSON recipes and extracts recipe results by namespace.
By default excludes 'minecraft:' recipes.

Usage:
    python -m tools.recipe_scanner [options]
"""

from __future__ import annotations
import argparse
import sys
import zipfile
import json
import traceback
from pathlib import Path
from collections import defaultdict
from typing import List, Set, Tuple

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
# JSON parsing
# ---------------------------------------------------------------------
def extract_results_from_json(content: str) -> List[str]:
    """Extract recipe result IDs from JSON content.
    
    Args:
        content: JSON string content
        
    Returns:
        List of recipe result IDs
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []

    results: List[str] = []
    if isinstance(data, dict):
        # Single result
        r = data.get("result")
        if isinstance(r, str):
            results.append(r)
        elif isinstance(r, dict) and isinstance(r.get("id"), str):
            results.append(r["id"])
        # Multiple results
        if isinstance(data.get("results"), list):
            for e in data["results"]:
                if isinstance(e, dict) and isinstance(e.get("id"), str):
                    results.append(e["id"])
    return results




# ---------------------------------------------------------------------
# Phase 1 — Scanning
# ---------------------------------------------------------------------
def process_jar(
    jar_path: Path,
    raw_recipes_dir: Path,
    include_minecraft: bool = False,
    namespace_filter: str | None = None
) -> None:
    """Process a single JAR file and extract recipes.
    
    Args:
        jar_path: Path to the JAR file
        raw_recipes_dir: Directory for raw recipe outputs (logs/recipes)
        include_minecraft: Whether to include minecraft: recipes
        namespace_filter: Optional namespace to filter by
    """
    try:
        per_namespace: dict[str, Set[str]] = defaultdict(set)
        with zipfile.ZipFile(jar_path, "r") as zf:
            for name in zf.namelist():
                parts = name.split("/")
                if len(parts) < 4 or parts[0] != "data":
                    continue
                ns = parts[1]
                
                # Apply namespace filter if specified
                if namespace_filter and ns.lower() != namespace_filter.lower():
                    continue
                
                if not parts[2].startswith("recipe") or not name.endswith(".json"):
                    continue
                
                try:
                    with zf.open(name) as f:
                        content = f.read().decode("utf-8", errors="ignore")
                    for rid in extract_results_from_json(content):
                        rid = rid.strip()
                        if rid:
                            # Filter minecraft: recipes unless included
                            if not include_minecraft and rid.startswith("minecraft:"):
                                continue
                            per_namespace[ns].add(rid)
                except Exception:
                    continue
        
        for ns, items in per_namespace.items():
            raw_file = raw_recipes_dir / f"{ns}_recipes_raw.txt"
            lines: List[str] = []
            for i in items:
                if ":" not in i:
                    lines.append(f"{ns}:{i}\n")
                else:
                    lines.append(f"{i}\n")
            write_entry(raw_file, lines)
        
        log(f"{jar_path.name}: {len(per_namespace)} namespaces", "OK")
    except zipfile.BadZipFile:
        log(f"Bad zip: {jar_path.name}", "WARN")
    except Exception as e:
        log(f"{jar_path.name}: {e}", "ERROR")
        traceback.print_exc()


# ---------------------------------------------------------------------
# Phase 2 — Sort & deduplicate
# ---------------------------------------------------------------------
def clean_results(raw_dir: Path, cleaned_dir: Path, skip_raw: bool = False) -> None:
    """Clean all *_raw.txt files and output cleaned files.
    
    Args:
        raw_dir: Directory containing raw files (logs/recipes)
        cleaned_dir: Directory for cleaned output files (output/recipes)
        skip_raw: If True, delete raw files after cleaning
    """
    for raw in raw_dir.glob("*_recipes_raw.txt"):
        try:
            clean_name = raw.name.replace("_raw.txt", ".txt")
            clean_path = cleaned_dir / clean_name
            with raw.open("r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
            unique_sorted = sorted(set(lines))
            with clean_path.open("w", encoding="utf-8") as f:
                for e in unique_sorted:
                    f.write(e + "\n")
            log(f"{clean_path.name}: {len(unique_sorted)} entries", "CLEAN")
            
            if skip_raw:
                raw.unlink()
        except Exception as e:
            log(f"{raw.name}: {e}", "ERROR CLEAN")


# ---------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------
def main() -> None:
    """Main entry point for recipe scanner."""
    parser = argparse.ArgumentParser(
        description="Scan JAR files for recipes and extract results by namespace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan JARs in current directory (exclude minecraft recipes)
  python -m tools.recipe_scanner
  
  # Include minecraft recipes
  python -m tools.recipe_scanner --include-minecraft
  
  # Scan JARs in specific directory
  python -m tools.recipe_scanner --input-dir ./mods
        """
    )
    
    # Add common arguments
    add_common_jar_args(parser)
    add_namespace_filter_arg(parser)
    
    parser.add_argument(
        "--include-minecraft",
        action="store_true",
        help="Include minecraft: recipes (default: exclude)"
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
    raw_recipes_dir, cleaned_recipes_dir = create_output_dirs("recipes")
    
    # Determine thread count
    max_workers = get_thread_count(args)
    
    # Create wrapper function for process_jar that captures parameters
    def process_jar_wrapper(jar_path: Path) -> None:
        """Wrapper to adapt process_jar for execute_concurrent."""
        process_jar(jar_path, raw_recipes_dir, args.include_minecraft, args.namespace)
    
    # Phase 1: Scanning
    log(f"Scanning {len(jars)} jars (excluding minecraft recipes: {not args.include_minecraft})...")
    execute_concurrent(jars, process_jar_wrapper, max_workers=max_workers, verbose=args.verbose)
    
    # Phase 2: Cleaning
    log("Sorting & deduplicating per-namespace results...")
    clean_results(raw_recipes_dir, cleaned_recipes_dir, args.skip_raw)
    
    log(f"Done. Clean files in: {cleaned_recipes_dir.resolve()}")
    log(f"Raw files in: {raw_recipes_dir.resolve()}")


if __name__ == "__main__":
    main()

