"""Common scanner functionality for all scanner tools.

**DEPRECATED**: This module is deprecated in favor of the new architecture.
New code should use:
- `src.services.scanner_service.ScannerService` for orchestration
- `src.processors.scanner.*` for scanner processors
- `src.models.scanner.*` for data models

This module is kept for backward compatibility with:
- `tools.scanners.tag_scanner`
- `tools.asset_scanner`

This module provides shared functions for scanners that process JAR files
as ZIP archives and extract information by namespace.
"""

from __future__ import annotations
import zipfile
import traceback
import sys
from pathlib import Path
from typing import Dict, List, Callable, Optional, Any
from collections import defaultdict

from src.utils import log
from src.file_operations import (
    append_text_lines,
    read_text_lines,
    read_text_lines_stripped,
    write_text_lines
)
from src.jar_processor import (
    validate_input_directory,
    find_jar_files,
    create_output_dirs
)
from src.arg_parser import get_thread_count
from src.thread_pool import execute_concurrent
from src.identifier_cleaner import clean_namespace_object_line
from src.affix_cleaner import FLUID_EXTENSIONS, DEFAULT_EXTENSIONS
from src.config_loader import StandardPaths, load_paths_from_config, get_default_paths


def process_jar_entries(
    jar_path: Path,
    raw_output_dir: Path,
    category_suffix: str,
    entry_filter: Callable[[List[str]], Optional[str]],
    namespace_filter: Optional[str] = None
) -> None:
    """Process a single JAR file and extract entries using a filter function.
    
    Args:
        jar_path: Path to the JAR file
        raw_output_dir: Directory for raw outputs (logs/{category})
        category_suffix: Suffix for output files (e.g., "_blocks", "_items")
        entry_filter: Function that takes path parts and returns object_id if entry matches, None otherwise
        namespace_filter: Optional namespace to filter by
    """
    try:
        buffer: Dict[str, List[str]] = {}
        
        with zipfile.ZipFile(jar_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith("/"):
                    continue
                
                parts = name.split("/")
                obj_id = entry_filter(parts)
                
                if obj_id is None:
                    continue
                
                # Extract namespace from path
                namespace = None
                if len(parts) >= 2:
                    if parts[0] == "assets" and len(parts) >= 2:
                        namespace = parts[1]
                    elif parts[0] == "data" and len(parts) >= 2:
                        namespace = parts[1]
                
                if namespace is None:
                    continue
                
                # Apply namespace filter if specified
                if namespace_filter and namespace.lower() != namespace_filter.lower():
                    continue
                
                buffer.setdefault(namespace, []).append(f"{namespace}:{obj_id}\n")
        
        # Write buffered entries
        for ns, lines in buffer.items():
            append_text_lines(raw_output_dir / f"{ns}{category_suffix}_raw.txt", lines)
        
        log(f"Scanned {jar_path.name}", "OK")
    
    except zipfile.BadZipFile:
        log(f"Bad zip file: {jar_path.name}", "WARN")
    except Exception as e:
        log(f"{jar_path.name}: {e}", "ERROR")
        traceback.print_exc()


def clean_results(
    raw_dir: Path,
    cleaned_dir: Path,
    suffix: str,
    skip_raw: bool = False,
    extensions: Optional[tuple] = None
) -> None:
    """Clean all *_raw.txt files and output cleaned files.
    
    Uses thorough cleaning that continues until convergence (no more changes).
    
    Args:
        raw_dir: Directory containing raw files (logs)
        cleaned_dir: Directory for cleaned output files (output)
        suffix: Suffix pattern to match (e.g., "_blocks")
        skip_raw: If True, delete raw files after cleaning
        extensions: Optional tuple of extensions for cleaning (for fluids)
    """
    for raw_file in raw_dir.glob(f"*{suffix}_raw.txt"):
        try:
            cleaned_name = raw_file.name.replace("_raw.txt", ".txt")
            cleaned_path = cleaned_dir / cleaned_name
            
            lines = read_text_lines(raw_file)
            
            cleaned: set[str] = set()
            ext_tuple = extensions if extensions else DEFAULT_EXTENSIONS
            
            for line in lines:
                cleaned_line = clean_namespace_object_line(line, ext_tuple)
                if cleaned_line:
                    cleaned.add(cleaned_line)
            
            sorted_lines = sorted(cleaned)
            entries = [entry + "\n" for entry in sorted_lines]
            write_text_lines(cleaned_path, entries)
            
            log(f"{cleaned_path.name}: {len(sorted_lines)} entries (from {raw_file.name})", "CLEAN")
            
            if skip_raw:
                raw_file.unlink()
        
        except Exception as e:
            log(f"{raw_file.name}: {e}", "ERROR CLEAN")


def clean_results_simple(
    raw_dir: Path,
    cleaned_dir: Path,
    suffix: str,
    skip_raw: bool = False
) -> None:
    """Simple cleaning: just sort and deduplicate (for recipes).
    
    Args:
        raw_dir: Directory containing raw files (logs)
        cleaned_dir: Directory for cleaned output files (output)
        suffix: Suffix pattern to match (e.g., "_recipes")
        skip_raw: If True, delete raw files after cleaning
    """
    for raw_file in raw_dir.glob(f"*{suffix}_raw.txt"):
        try:
            cleaned_name = raw_file.name.replace("_raw.txt", ".txt")
            cleaned_path = cleaned_dir / cleaned_name
            
            lines = read_text_lines_stripped(raw_file)
            unique_sorted = sorted(set(lines))
            entries = [entry + "\n" for entry in unique_sorted]
            write_text_lines(cleaned_path, entries)
            
            log(f"{cleaned_path.name}: {len(unique_sorted)} entries", "CLEAN")
            
            if skip_raw:
                raw_file.unlink()
        
        except Exception as e:
            log(f"{raw_file.name}: {e}", "ERROR CLEAN")


def run_scanner(
    category: str,
    category_suffix: str,
    entry_filter: Optional[Callable[[List[str]], Optional[str]]],
    description: str,
    args: Any,
    paths: StandardPaths,
    clean_func: Optional[Callable] = None,
    process_jar_func: Optional[Callable] = None
) -> None:
    """Run a scanner with common workflow.
    
    Args:
        category: Category name (e.g., "blocks", "items")
        category_suffix: Suffix for output files (e.g., "_blocks")
        entry_filter: Function to filter ZIP entries
        description: Description for logging
        args: Parsed arguments
        paths: StandardPaths from config
        clean_func: Optional custom cleaning function (default: clean_results)
        process_jar_func: Optional custom JAR processing function
    """
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
    raw_dir, cleaned_dir = create_output_dirs(category, paths)
    
    # Determine thread count
    max_workers = get_thread_count(args)
    
    # Create JAR processing function
    if process_jar_func is None:
        if entry_filter is None:
            raise ValueError("entry_filter is required when process_jar_func is not provided")
        def process_jar_wrapper(jar_path: Path) -> None:
            """Wrapper to adapt process_jar for execute_concurrent."""
            process_jar_entries(
                jar_path,
                raw_dir,
                category_suffix,
                entry_filter,
                args.namespace if hasattr(args, 'namespace') else None
            )
    else:
        def process_jar_wrapper(jar_path: Path) -> None:
            """Wrapper using custom processing function."""
            process_jar_func(jar_path, raw_dir, args)
    
    # Phase 1: Scanning
    log(f"Found {len(jars)} JAR(s). Scanning with {max_workers} threads...")
    execute_concurrent(
        jars,
        process_jar_wrapper,
        max_workers=max_workers,
        verbose=args.verbose if hasattr(args, 'verbose') else False
    )
    
    # Phase 2: Cleaning
    log("Starting thorough cleaning of gathered results...")
    if clean_func is None:
        skip_raw = args.skip_raw if hasattr(args, 'skip_raw') else False
        extensions = None
        if category == "fluids":
            extensions = FLUID_EXTENSIONS
        clean_results(raw_dir, cleaned_dir, category_suffix, skip_raw, extensions)
    else:
        skip_raw = args.skip_raw if hasattr(args, 'skip_raw') else False
        clean_func(raw_dir, cleaned_dir, category_suffix, skip_raw)
    
    log(f"Completed. Clean files in:\n  {cleaned_dir.resolve()}")
    log(f"Raw files in:\n  {raw_dir.resolve()}")
