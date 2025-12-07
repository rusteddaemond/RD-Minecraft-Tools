#!/usr/bin/env python3
"""
Block Duplicate Matcher for OneEnough Blocks (OEB)
----------------------------------------------------

Finds duplicate blocks across different namespaces and generates OEB datapacks
for block matching. Useful for mod compatibility and block unification.

Generates OEB datapack format:
- Datapack: data/oeb/replacements/example.json (requires OEI as dependency)

Usage:
    python -m tools.block_matcher [options]
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils import log


# ---------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------
def find_txt_files(directory: Path) -> List[Path]:
    """Find all .txt files in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of .txt file paths
    """
    return [f for f in directory.glob("*.txt") if f.is_file()]


def load_blocks(files: List[Path]) -> Dict[str, List[str]]:
    """Load blocks from text files and map block_id -> list of namespaces.
    
    Args:
        files: List of text file paths
        
    Returns:
        Dictionary mapping block_id to list of namespaces containing it
    """
    blocks: Dict[str, List[str]] = defaultdict(list)
    for file in files:
        try:
            with file.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or ":" not in line:
                        continue
                    ns, block_id = line.split(":", 1)
                    ns = ns.lower().strip()
                    block_id = block_id.lower().strip()
                    blocks[block_id].append(ns)
        except Exception as e:
            log(f"Error reading {file}: {e}", "ERROR")
    return blocks


def filter_duplicates(blocks: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Filter blocks to only those appearing in multiple namespaces.
    
    Args:
        blocks: Dictionary mapping block_id to list of namespaces
        
    Returns:
        Dictionary with only duplicate blocks
    """
    return {bid: ns_list for bid, ns_list in blocks.items() if len(set(ns_list)) > 1}


# ---------------------------------------------------------------------
# User interaction
# ---------------------------------------------------------------------
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


# ---------------------------------------------------------------------
# Match building
# ---------------------------------------------------------------------
def build_matches(dupes: Dict[str, List[str]], result_ns: str) -> List[Dict[str, str]]:
    """Build match list from duplicates and result namespace.
    
    Args:
        dupes: Dictionary of duplicate blocks
        result_ns: Target namespace for results
        
    Returns:
        List of match dictionaries with matchBlock and resultBlock
    """
    matches: List[Dict[str, str]] = []
    for block_id, ns_list in dupes.items():
        if result_ns not in ns_list:
            continue
        for ns in ns_list:
            if ns != result_ns:
                matches.append({
                    "matchBlock": f"{ns}:{block_id}",
                    "resultBlock": f"{result_ns}:{block_id}"
                })
    return matches


def build_oeb_datapack_matches(dupes: Dict[str, List[str]], result_ns: str) -> List[Dict[str, Any]]:
    """Build OEB datapack format matches (Method 2: data/oeb/replacements/).
    
    Groups matches by result block. Format:
    [
        {
            "matchBlock": ["namespace:block_id", ...],
            "resultBlock": "namespace:block_id"
        }
    ]
    
    Args:
        dupes: Dictionary of duplicate blocks
        result_ns: Target namespace for results
        
    Returns:
        List of OEB datapack format dictionaries
    """
    from collections import defaultdict
    
    # Group by result block
    grouped: Dict[str, List[str]] = defaultdict(list)
    
    for block_id, ns_list in dupes.items():
        if result_ns not in ns_list:
            continue
        
        result_block = f"{result_ns}:{block_id}"
        
        # Add all non-result namespace blocks to match list
        for ns in ns_list:
            if ns != result_ns:
                grouped[result_block].append(f"{ns}:{block_id}")
    
    # Convert to OEB datapack format
    datapack_matches: List[Dict[str, Any]] = []
    for result_block, match_blocks in sorted(grouped.items()):
        datapack_matches.append({
            "matchBlock": sorted(match_blocks),
            "resultBlock": result_block
        })
    
    return datapack_matches


# ---------------------------------------------------------------------
# Output formats
# ---------------------------------------------------------------------
def write_json(matches: List[Dict[str, str]], out_file: Path) -> None:
    """Write matches to JSON file (legacy format).
    
    Args:
        matches: List of match dictionaries
        out_file: Output file path
    """
    with out_file.open("w", encoding="utf-8") as fh:
        json.dump(matches, fh, indent=2)


def write_oeb_datapack(datapack_matches: List[Dict[str, Any]], out_file: Path) -> None:
    """Write OEB datapack format to JSON file (Method 2).
    
    Args:
        datapack_matches: List of OEB datapack format dictionaries
        out_file: Output file path
    """
    with out_file.open("w", encoding="utf-8") as fh:
        json.dump(datapack_matches, fh, indent=2)


def create_oeb_datapack_structure(output_dir: Path, filename: str = "example.json") -> Path:
    """Create OEB datapack directory structure (Method 2).
    
    Args:
        output_dir: Base output directory
        filename: Name of the replacements file
        
    Returns:
        Path to the replacements file
    """
    replacements_dir = output_dir / "data" / "oeb" / "replacements"
    replacements_dir.mkdir(parents=True, exist_ok=True)
    return replacements_dir / filename


def create_pack_mcmeta(output_dir: Path, pack_format: int = 10) -> None:
    """Create pack.mcmeta file for the datapack.
    
    Args:
        output_dir: Base output directory
        pack_format: Minecraft datapack format version (default: 10)
    """
    pack_mcmeta = output_dir / "pack.mcmeta"
    
    meta = {
        "pack": {
            "pack_format": pack_format,
            "description": "OneEnough Blocks replacements"
        }
    }
    
    with pack_mcmeta.open("w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)


def write_csv(matches: List[Dict[str, str]], out_file: Path) -> None:
    """Write matches to CSV file.
    
    Args:
        matches: List of match dictionaries
        out_file: Output file path
    """
    import csv
    with out_file.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["matchBlock", "resultBlock"])
        writer.writeheader()
        writer.writerows(matches)


def write_txt(matches: List[Dict[str, str]], out_file: Path) -> None:
    """Write matches to text file.
    
    Args:
        matches: List of match dictionaries
        out_file: Output file path
    """
    with out_file.open("w", encoding="utf-8") as fh:
        for match in matches:
            fh.write(f"{match['matchBlock']} -> {match['resultBlock']}\n")


# ---------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------
def main() -> None:
    """Main entry point for block matcher."""
    parser = argparse.ArgumentParser(
        description="Find duplicate blocks across namespaces and generate matching mappings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate OEB datapack (default)
  python -m tools.block_matcher
  
  # Non-interactive with pre-selected namespace
  python -m tools.block_matcher --namespace minecraft --no-interactive
  
  # Custom output directory and filename
  python -m tools.block_matcher --output-dir ./oeb_datapack --filename my_replacements.json
  
  # Legacy formats (json, csv, txt)
  python -m tools.block_matcher --format json --output-file ./matches.json
        """
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Directory containing .txt files (default: current directory)"
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Output file path (default: matches.json in input directory)"
    )
    parser.add_argument(
        "--namespace",
        type=str,
        default=None,
        help="Pre-select namespace (enables non-interactive mode)"
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable interactive namespace selection"
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv", "txt", "oeb-datapack"],
        default="oeb-datapack",
        help="Output format: json (legacy), csv, txt, or oeb-datapack (default: oeb-datapack)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for OEB datapack (default: oeb_output)"
    )
    parser.add_argument(
        "--filename",
        type=str,
        default="example.json",
        help="Name of the replacements file for OEB datapack (default: example.json)"
    )
    parser.add_argument(
        "--pack-format",
        type=int,
        default=10,
        help="Minecraft datapack format version for oeb-datapack (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Determine input directory
    if args.input_dir:
        input_dir = args.input_dir
    else:
        # Default to current directory
        input_dir = Path.cwd()
    
    if not input_dir.exists():
        log(f"Input directory does not exist: {input_dir}", "ERROR")
        sys.exit(1)
    
    if not input_dir.is_dir():
        log(f"Input path is not a directory: {input_dir}", "ERROR")
        sys.exit(1)
    
    log(f"Scanning: {input_dir}")
    
    # Find and load text files
    txt_files = find_txt_files(input_dir)
    if not txt_files:
        log("No .txt files found", "ERROR")
        sys.exit(1)
    
    log(f"Found {len(txt_files)} text file(s)", "OK")
    
    blocks = load_blocks(txt_files)
    dupes = filter_duplicates(blocks)
    
    if not dupes:
        log("No cross-namespace duplicates found", "INFO")
        sys.exit(0)
    
    log(f"\nFound {len(dupes)} duplicate blocks:", "INFO")
    for bid, ns_list in sorted(dupes.items()):
        unique_ns = sorted(set(ns_list))
        log(f"  {bid}: {', '.join(unique_ns)}")
    
    # Determine result namespace
    all_namespaces = set(ns for ns_list in dupes.values() for ns in ns_list)
    
    if args.namespace:
        # Use provided namespace
        result_ns = args.namespace.lower()
        if result_ns not in all_namespaces:
            log(f"Namespace '{args.namespace}' not found in duplicates", "ERROR")
            log(f"Available namespaces: {', '.join(sorted(all_namespaces))}", "INFO")
            sys.exit(1)
    else:
        # Interactive or non-interactive selection
        interactive = not args.no_interactive
        result_ns = choose_result_namespace(all_namespaces, interactive=interactive)
        if not result_ns:
            log("No namespace selected. Exiting.", "ERROR")
            sys.exit(1)
    
    log(f"\nUsing namespace: {result_ns}", "INFO")
    
    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    elif args.format == "oeb-datapack":
        output_dir = Path("oeb_output")
    else:
        output_dir = input_dir
    
    # Build matches based on format
    if args.format == "oeb-datapack":
        # OEB datapack format
        datapack_matches = build_oeb_datapack_matches(dupes, result_ns)
        out_file = create_oeb_datapack_structure(output_dir, args.filename)
        write_oeb_datapack(datapack_matches, out_file)
        create_pack_mcmeta(output_dir, args.pack_format)
        log(f"\nWrote {len(datapack_matches)} OEB datapack rule(s) to {out_file}", "OK")
        log(f"Datapack generated at: {output_dir.resolve()}", "INFO")
        log(f"Install by copying to: .minecraft/saves/<world>/datapacks/", "INFO")
        log("Note: Requires OEI as a dependency", "INFO")
        
    else:
        # Legacy formats (json, csv, txt)
        matches = build_matches(dupes, result_ns)
        
        # Determine output file
        if args.output_file:
            out_file = args.output_file
        else:
            # Default based on format
            ext = {
                "json": ".json",
                "csv": ".csv",
                "txt": ".txt"
            }[args.format]
            out_file = input_dir / f"matches{ext}"
        
        # Write output
        if args.format == "json":
            write_json(matches, out_file)
        elif args.format == "csv":
            write_csv(matches, out_file)
        else:  # txt
            write_txt(matches, out_file)
        
        log(f"\nWrote {len(matches)} matches to {out_file}", "OK")


if __name__ == "__main__":
    main()

