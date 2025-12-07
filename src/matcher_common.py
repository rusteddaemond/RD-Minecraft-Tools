"""Common matcher functionality for all matcher tools.

**DEPRECATED**: This module is deprecated in favor of the new architecture.
New code should use:
- `src.services.matcher_service.MatcherService` for orchestration
- `src.processors.matcher.*` for matcher processors
- `src.models.matcher.*` for data models

This module is kept for backward compatibility with legacy tools.

This module provides shared functions for matchers that work with
namespace:object format files (scanner output).
"""

from __future__ import annotations
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Optional, Any

from src.utils import log
from src.config_loader import find_txt_files
from src.datapack_generator import create_pack_mcmeta
from src.file_operations import read_namespace_object_lines, write_json_file


def load_objects(files: List[Path]) -> Dict[str, List[str]]:
    """Load objects from text files and map object_id -> list of namespaces.
    
    Args:
        files: List of text file paths containing namespace:object lines
        
    Returns:
        Dictionary mapping object_id to list of namespaces containing it
    """
    objects: Dict[str, List[str]] = defaultdict(list)
    for file in files:
        try:
            for ns, obj_id in read_namespace_object_lines(file):
                objects[obj_id].append(ns)
        except Exception as e:
            log(f"Error reading {file}: {e}", "ERROR")
    return objects


def filter_duplicates(objects: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Filter objects to only those appearing in multiple namespaces.
    
    Args:
        objects: Dictionary mapping object_id to list of namespaces
        
    Returns:
        Dictionary with only duplicate objects
    """
    return {obj_id: ns_list for obj_id, ns_list in objects.items() if len(set(ns_list)) > 1}


def choose_result_namespace(namespaces: Set[str], interactive: bool = True) -> Optional[str]:
    """Prompt user to select the target namespace.
    
    Args:
        namespaces: Set of available namespaces
        interactive: Whether to prompt interactively
        
    Returns:
        Selected namespace, or None if not interactive and no default
    """
    ns_list = sorted(namespaces)
    
    if not interactive:
        # Non-interactive mode: return first namespace or None
        return ns_list[0] if ns_list else None
    
    log("\nChoose RESULT namespace:", "INFO")
    for idx, ns in enumerate(ns_list, 1):
        log(f"{idx}) {ns}")
    
    while True:
        try:
            choice = int(input("Enter number: "))
            if 1 <= choice <= len(ns_list):
                return ns_list[choice - 1]
            log("Invalid number", "WARN")
        except ValueError:
            log("Must enter a number", "WARN")
        except (EOFError, KeyboardInterrupt):
            log("\nCancelled.", "INFO")
            return None


def build_datapack_matches(
    duplicates: Dict[str, List[str]], 
    result_ns: str,
    match_field: str = "matchBlock",
    result_field: str = "resultBlock"
) -> List[Dict[str, Any]]:
    """Build datapack format matches grouped by result.
    
    Groups matches by result object. Format:
    [
        {
            "matchBlock": ["namespace:object_id", ...],
            "resultBlock": "namespace:object_id"
        }
    ]
    
    Args:
        duplicates: Dictionary of duplicate objects
        result_ns: Target namespace for results
        match_field: Field name for match list (e.g., "matchBlock", "matchItems", "matchFluid")
        result_field: Field name for result (e.g., "resultBlock", "resultItems", "resultFluid")
        
    Returns:
        List of datapack format dictionaries
    """
    grouped: Dict[str, List[str]] = defaultdict(list)
    
    for obj_id, ns_list in duplicates.items():
        if result_ns not in ns_list:
            continue
        
        result_obj = f"{result_ns}:{obj_id}"
        
        # Add all non-result namespace objects to match list
        for ns in ns_list:
            if ns != result_ns:
                grouped[result_obj].append(f"{ns}:{obj_id}")
    
    # Convert to datapack format
    datapack_matches: List[Dict[str, Any]] = []
    for result_obj, match_objs in sorted(grouped.items()):
        datapack_matches.append({
            match_field: sorted(match_objs),
            result_field: result_obj
        })
    
    return datapack_matches


def write_datapack(
    datapack_matches: List[Dict[str, Any]], 
    output_dir: Path, 
    datapack_path: str,
    filename: str = "replacements.json"
) -> Path:
    """Write datapack matches to file.
    
    Args:
        datapack_matches: List of datapack format dictionaries
        output_dir: Base output directory
        datapack_path: Path component for datapack (e.g., 'oeb', 'oei', 'oef')
        filename: Name of the replacements file
        
    Returns:
        Path to the replacements file
    """
    replacements_dir = output_dir / "data" / datapack_path / "replacements"
    replacements_dir.mkdir(parents=True, exist_ok=True)
    out_file = replacements_dir / filename
    
    write_json_file(out_file, datapack_matches, indent=2)
    
    return out_file


def create_datapack(
    duplicates: Dict[str, List[str]],
    result_ns: str,
    output_dir: Path,
    datapack_path: str,
    match_field: str,
    result_field: str,
    description: str,
    filename: str = "replacements.json",
    pack_format: int = 10
) -> Path:
    """Create complete datapack from duplicates.
    
    Args:
        duplicates: Dictionary of duplicate objects
        result_ns: Target namespace for results
        output_dir: Base output directory
        datapack_path: Path component for datapack (e.g., 'oeb', 'oei', 'oef')
        match_field: Field name for match list
        result_field: Field name for result
        description: Description for the datapack
        filename: Name of the replacements file
        pack_format: Minecraft datapack format version
        
    Returns:
        Path to the generated replacements file
    """
    # Build matches
    datapack_matches = build_datapack_matches(duplicates, result_ns, match_field, result_field)
    
    # Write datapack
    out_file = write_datapack(datapack_matches, output_dir, datapack_path, filename)
    
    # Create pack.mcmeta
    create_pack_mcmeta(output_dir, pack_format, description)
    
    return out_file
