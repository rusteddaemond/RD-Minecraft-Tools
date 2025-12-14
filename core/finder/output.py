"""
Output functions for saving mod pair discovery results.
"""

import json
import shutil
from pathlib import Path
from typing import List

from core.builder.models import ModPair, DatapackType, TYPE_NAME_MAP
from core.constants import FilePatterns, DisplayConstants
from core.utils.format import format_separator, format_subseparator
from core.utils.logging import log_warning


def copy_scan_files(
    scan_dir: Path,
    output_dir: Path,
    type_name: str
) -> None:
    """
    Copy all files from scan_output directory to find_output directory.
    
    Args:
        scan_dir: Source directory (from scan_output)
        output_dir: Destination directory (find_output)
        type_name: Type name (items, blocks, fluids)
    """
    if not scan_dir.exists():
        log_warning(f"Scan directory does not exist: {scan_dir}")
        return
    
    # Create type directory in find_output
    type_dir = output_dir / type_name
    type_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy all files from scan_dir to type_dir
    copied_count = 0
    for source_file in scan_dir.glob("*.txt"):
        dest_file = type_dir / source_file.name
        try:
            shutil.copy2(source_file, dest_file)
            copied_count += 1
        except (OSError, shutil.Error) as e:
            log_warning(f"Failed to copy {source_file.name}: {e}")
    
    if copied_count > 0:
        print(f"Copied {copied_count} file(s) from {scan_dir} to {type_dir}")


def save_pairs(
    pairs: List[ModPair],
    output_dir: Path,
    datapack_type: DatapackType
) -> None:
    """
    Placeholder function for compatibility.
    Pairs are now saved via save_summary() only.
    
    This function is kept for API compatibility but does not perform any operations.
    All pair data is saved via save_summary() function.
    
    Args:
        pairs: List of ModPair objects to save
        output_dir: Directory to save results to
        datapack_type: Type of datapack (for subdirectory organization)
    """
    # No-op: Function kept for API compatibility
    pass


def save_summary(
    pairs: List[ModPair],
    output_dir: Path,
    datapack_type: DatapackType
) -> None:
    """
    Save summary of pair discovery results with list of all found pairs.
    Creates separate summary file by type (items_summary.txt, blocks_summary.txt, fluids_summary.txt).
    
    Args:
        pairs: List of ModPair objects
        output_dir: Directory to save summary to
        datapack_type: Type of datapack
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    type_name = TYPE_NAME_MAP[datapack_type]
    summary_file = output_dir / f'{type_name}{FilePatterns.SUMMARY_SUFFIX}'
    
    separator = format_separator()
    subseparator = format_subseparator()
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("Mod Pair Discovery Summary\n")
        f.write(f"{separator}\n\n")
        f.write(f"Type: {type_name.upper()}\n")
        f.write(f"Total pairs found: {len(pairs)}\n\n")
        
        if pairs:
            f.write("All pairs by match count (sorted descending):\n")
            f.write(f"{subseparator}\n")
            for idx, pair in enumerate(pairs, 1):
                f.write(f"{idx:4d}. {pair.mod1:25s} + {pair.mod2:25s} ({pair.match_count:4d} matches)\n")
            f.write("\n")
            f.write(f"{separator}\n")
            f.write("Pair Details:\n")
            f.write(f"{separator}\n\n")
            for idx, pair in enumerate(pairs, 1):
                f.write(f"{idx}. {pair.mod1} + {pair.mod2}\n")
                f.write(f"   Matches: {pair.match_count}\n")
                f.write(f"   {pair.mod1}: {len(pair.mod1_items)} items\n")
                f.write(f"   {pair.mod2}: {len(pair.mod2_items)} items\n")
                f.write("\n")
        else:
            f.write("No pairs found.\n")
    
    print(f"Saved summary to {summary_file}")

