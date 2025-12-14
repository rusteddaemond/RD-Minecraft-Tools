#!/usr/bin/env python3
"""
CLI entry point for the Minecraft Mod Scanner.
This is the command-line interface that uses the scanner module.
"""

import argparse
import sys
from pathlib import Path
from core import scan
from core.constants import DefaultDirs
from core.utils.path import validate_directory
from core.utils.logging import log_error


def main():
    """Main CLI entry point for the mod scanner."""
    parser = argparse.ArgumentParser(
        description='Scan Minecraft mods and extract items, tags, recipes, and more',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan mods in default directories (mods/ -> scan_output/)
  python scanner.py

  # Specify custom mods directory
  python scanner.py -m ./my_mods

  # Specify both mods and output directories
  python scanner.py -m ./my_mods -o ./my_output

  # Use long flags
  python scanner.py --mods-dir ./my_mods --output-dir ./my_output
        """
    )
    
    parser.add_argument(
        '-m', '--mods-dir',
        type=Path,
        default=DefaultDirs.MODS,
        help=f'Directory containing mod JAR files (default: {DefaultDirs.MODS})'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=Path,
        default=DefaultDirs.SCAN_OUTPUT,
        help=f'Directory to save scan results (default: {DefaultDirs.SCAN_OUTPUT})'
    )
    
    args = parser.parse_args()
    
    # Validate mods directory exists
    if not validate_directory(args.mods_dir, error_on_fail=True):
        log_error("Please specify a valid directory with -m/--mods-dir", exit_code=1)
    
    if not args.mods_dir.is_dir():
        log_error(f"Path is not a directory: {args.mods_dir}", exit_code=1)
    
    # Run the scan
    try:
        scan(str(args.mods_dir), str(args.output_dir))
    except KeyboardInterrupt:
        print("\n\nScan interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError during scan: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
