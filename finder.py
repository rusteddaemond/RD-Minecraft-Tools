#!/usr/bin/env python3
"""
Mod Pair Finder
Discovers mod pairs with overlapping base names from scan output.
Outputs results to find_output/ directory.
"""

import argparse
import sys
from pathlib import Path

from core import DatapackType, DATAPACK_CONFIGS
from core.builder.models import TYPE_NAME_MAP
from core.builder.processors import FileParser, ItemGrouper
from core.finder import PairScanner, save_pairs, save_summary, copy_scan_files
from core.constants import DefaultDirs, DisplayConstants
from core.utils.cli import determine_datapack_types
from core.utils.format import print_separator, print_subseparator
from core.utils.path import validate_directory


def main():
    parser = argparse.ArgumentParser(
        description='Find mod pairs with overlapping base names from scan output',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all types (default)
  python finder.py

  # Process specific types
  python finder.py -i
  python finder.py -b
  python finder.py -f
  python finder.py -i -b  # Process items and blocks

  # Specify custom scan directory
  python finder.py -i --scan-dir ./custom/path

  # Set minimum matches threshold
  python finder.py -i --min-matches 5

  # Specify output directory
  python finder.py -o ./my_find_output
        """
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=DefaultDirs.FIND_OUTPUT,
        help=f'Output directory for pair discovery results (default: {DefaultDirs.FIND_OUTPUT})'
    )
    
    parser.add_argument(
        '-i', '--items',
        action='store_true',
        help='Find item pairs (if no flags specified, processes all types)'
    )
    
    parser.add_argument(
        '-b', '--blocks',
        action='store_true',
        help='Find block pairs (if no flags specified, processes all types)'
    )
    
    parser.add_argument(
        '-f', '--fluids',
        action='store_true',
        help='Find fluid pairs (if no flags specified, processes all types)'
    )
    
    parser.add_argument(
        '--scan-dir',
        type=Path,
        help='Override default scan directory'
    )
    
    parser.add_argument(
        '--min-matches',
        type=int,
        default=DisplayConstants.DEFAULT_MIN_MATCHES,
        help=f'Minimum number of matching base names to include a pair (default: {DisplayConstants.DEFAULT_MIN_MATCHES})'
    )
    
    args = parser.parse_args()
    
    # Determine which types to process
    types_to_process = determine_datapack_types(args)
    
    # Initialize processors
    file_parser = FileParser()
    item_grouper = ItemGrouper()
    pair_scanner = PairScanner(file_parser, item_grouper)
    
    # Create output directory
    if not validate_directory(args.output, create=True, error_on_fail=True):
        sys.exit(1)
    
    print_separator()
    print("MOD PAIR FINDER")
    print_separator()
    print(f"Processing types: {', '.join([TYPE_NAME_MAP[t].upper() for t in types_to_process])}")
    print(f"Output Directory: {args.output}")
    print(f"Minimum Matches: {args.min_matches}")
    print_separator()
    print()
    
    # Process each type
    for datapack_type in types_to_process:
        config = DATAPACK_CONFIGS[datapack_type]
        type_name = TYPE_NAME_MAP[datapack_type]
        
        # Determine scan directory
        scan_dir = args.scan_dir if args.scan_dir else config.scan_dir
        
        print()
        print_separator()
        print(f"Processing {type_name.upper()}")
        print_separator()
        print(f"Scan Directory: {scan_dir}")
        print()
        
        # Scan for pairs
        print(f"Scanning for mod pairs in {scan_dir}...")
        pairs = pair_scanner.scan_installed_mods(
            datapack_type=datapack_type,
            scan_dir=scan_dir,
            min_matches=args.min_matches
        )
        
        if not pairs:
            print(f"No mod pairs found for {type_name}.")
            print(f"  (Minimum matches required: {args.min_matches})")
            continue
        
        print(f"Found {len(pairs)} mod pair(s) with overlapping base names")
        print()
        
        # Display top pairs
        print(f"Top {DisplayConstants.TOP_PAIRS_LIMIT} pairs by match count:")
        print_subseparator()
        for idx, pair in enumerate(pairs[:DisplayConstants.TOP_PAIRS_LIMIT], 1):
            print(f"{idx:3d}. {pair.mod1:20s} + {pair.mod2:20s} ({pair.match_count:4d} matches)")
        if len(pairs) > DisplayConstants.TOP_PAIRS_LIMIT:
            print(f"     ... and {len(pairs) - DisplayConstants.TOP_PAIRS_LIMIT} more pairs")
        print()
        
        # Copy files from scan_output to find_output
        print("Copying files from scan_output...")
        copy_scan_files(scan_dir, args.output, type_name)
        
        # Save results
        print("Saving results...")
        save_summary(pairs, args.output, datapack_type)
        
        print(f"\n{type_name.upper()} complete!")
        print(f"  - {type_name}/: Copied files and pair data")
        print(f"  - {type_name}_summary.txt: Summary of pairs")
    
    print()
    print_separator()
    print("Done!")
    print(f"Results saved to: {args.output}")


if __name__ == '__main__':
    main()

