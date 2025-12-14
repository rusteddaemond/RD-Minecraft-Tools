#!/usr/bin/env python3
"""
One Enough Datapack Builder
Creates datapacks for One Enough Item (OEI), One Enough Block (OEB), and One Enough Fluid (OEF)
from txt files containing namespace:id lists.
"""

import argparse
import shutil
import sys
from pathlib import Path

from core import DatapackType, DATAPACK_CONFIGS
from core.builder.processors import FileParser, ItemGrouper, DatapackBuilder
from core.builder.ui import display_namespace_selection
from core.constants import DefaultDirs, FilePatterns
from core.utils.path import validate_directory
from core.utils.logging import log_error, log_warning


def main():
    parser = argparse.ArgumentParser(
        description='Build One Enough datapacks from txt files containing namespace:id lists',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan mode (default when no files specified)
  python builder.py -i
  python builder.py -b
  python builder.py -f

  # Manual mode (specify files)
  python builder.py file1.txt file2.txt
  python builder.py -i file1.txt file2.txt
  python builder.py -b file1.txt file2.txt
  python builder.py -f file1.txt file2.txt

  # Specify output directory and datapack name
  python builder.py -o ./datapacks -n my_replacements file1.txt
        """
    )
    
    parser.add_argument(
        'files',
        nargs='*',
        type=Path,
        help='Txt files containing namespace:id lists (optional - if not provided, uses scan mode)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=DefaultDirs.BUILD_OUTPUT,
        help=f'Output directory for datapacks (default: {DefaultDirs.BUILD_OUTPUT})'
    )
    
    parser.add_argument(
        '-n', '--name',
        type=str,
        default='one_enough_replacements',
        help='Datapack name (default: one_enough_replacements)'
    )
    
    parser.add_argument(
        '-b', '--blocks',
        action='store_true',
        help='Create One Enough Block (OEB) datapack instead of OEI'
    )
    
    parser.add_argument(
        '-f', '--fluids',
        action='store_true',
        help='Create One Enough Fluid (OEF) datapack instead of OEI'
    )
    
    parser.add_argument(
        '-i', '--items',
        action='store_true',
        help='Create One Enough Item (OEI) datapack (default)'
    )
    
    parser.add_argument(
        '--result-namespace',
        type=str,
        help='Skip namespace selection and use this namespace as result'
    )
    
    
    parser.add_argument(
        '--skip-scan',
        action='store_true',
        help='Force manual mode even when no files are specified (requires files argument)'
    )
    
    args = parser.parse_args()
    
    # Determine datapack type from flags
    if args.fluids:
        datapack_type = DatapackType.FLUIDS
    elif args.blocks:
        datapack_type = DatapackType.BLOCKS
    else:
        datapack_type = DatapackType.ITEMS
    
    config = DATAPACK_CONFIGS[datapack_type]
    
    # Initialize processors
    file_parser = FileParser()
    item_grouper = ItemGrouper()
    datapack_builder = DatapackBuilder(item_grouper)
    
    # Create output directory
    if not validate_directory(args.output, create=True, error_on_fail=True):
        sys.exit(1)
    
    # Create builder work directory in project root (where builder.py is located)
    project_root = Path(__file__).parent
    work_dir = project_root / f"{args.name}{FilePatterns.WORK_SUFFIX}"
    if not validate_directory(work_dir, create=True, error_on_fail=True):
        sys.exit(1)
    print(f"Created builder work directory: {work_dir}")
    
    # Determine workflow mode
    use_scan_mode = not args.files and not args.skip_scan
    files_to_process = []
    
    if use_scan_mode:
        # Scan mode: search for txt files in project root
        print("Scan mode: Searching for txt files in project root...")
        
        # Find txt files in project root
        project_root_txt_files = list(project_root.glob("*.txt"))
        
        if not project_root_txt_files:
            log_error("No txt files found in project root directory.")
            print(f"  Project root: {project_root}")
            print("\nPlease either:")
            print("  1. Place txt files in the project root directory, or")
            print("  2. Specify files explicitly: python builder.py file1.txt file2.txt")
            sys.exit(1)
        
        print(f"Found {len(project_root_txt_files)} txt file(s) in project root")
        # Use project root txt files
        for txt_file in project_root_txt_files:
            namespace = txt_file.stem
            dest_file = work_dir / txt_file.name
            shutil.copy2(txt_file, dest_file)
            files_to_process.append(dest_file)
            print(f"  Using: {txt_file.name}")
        
        # Parse files from work directory
        all_items = file_parser.parse_txt_files(files_to_process)
        print(f"\nLoaded {len(all_items)} items from project root txt files")
        
        if not all_items:
            log_error("No valid namespace:id entries found in project root txt files", exit_code=1)
        
        # Group by namespace
        by_namespace = item_grouper.group_by_namespace(all_items)
        print(f"Found {len(by_namespace)} unique namespaces")
        
        # Select result namespace
        if args.result_namespace:
            result_namespace = args.result_namespace
            if result_namespace not in by_namespace:
                log_error(f"Namespace '{result_namespace}' not found in project root files")
                print(f"Available namespaces: {', '.join(sorted(by_namespace.keys()))}")
                sys.exit(1)
        else:
            result_namespace = display_namespace_selection(by_namespace)
    
    else:
        # Manual mode: use specified files
        if not args.files:
            log_error("No files specified and --skip-scan flag set. Please specify files.", exit_code=1)
        
        # Copy specified files to work directory
        print(f"Manual mode: Copying {len(args.files)} file(s) to work directory...")
        for source_file in args.files:
            if not source_file.exists():
                log_warning(f"File not found: {source_file}")
                continue
            dest_file = work_dir / source_file.name
            shutil.copy2(source_file, dest_file)
            files_to_process.append(dest_file)
            print(f"Copied {source_file.name} to work directory")
        
        if not files_to_process:
            log_error("No valid files to process", exit_code=1)
        
        # Parse files from work directory
        print(f"Reading {len(files_to_process)} file(s) from work directory...")
        all_items = file_parser.parse_txt_files(files_to_process)
        
        if not all_items:
            log_error("No valid namespace:id entries found in input files", exit_code=1)
        
        print(f"Found {len(all_items)} unique items")
        
        # Group by namespace
        by_namespace = item_grouper.group_by_namespace(all_items)
        print(f"Found {len(by_namespace)} unique namespaces")
        
        # Select result namespace
        if args.result_namespace:
            result_namespace = args.result_namespace
            if result_namespace not in by_namespace:
                log_error(f"Namespace '{result_namespace}' not found in input files")
                print(f"Available namespaces: {', '.join(sorted(by_namespace.keys()))}")
                sys.exit(1)
        else:
            result_namespace = display_namespace_selection(by_namespace)
    
    # Create datapack using unified builder
    try:
        datapack_builder.create_datapack(
            items=all_items,
            result_namespace=result_namespace,
            output_dir=args.output,
            datapack_name=args.name,
            config=config
        )
    except ValueError as e:
        log_error(str(e), exit_code=1)
    except OSError as e:
        log_error(str(e), exit_code=1)
    
    print("\nDone!")


if __name__ == '__main__':
    main()

