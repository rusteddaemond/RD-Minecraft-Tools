#!/usr/bin/env python3
"""
Block Duplicate Matcher for OneEnough Blocks (OEB)
----------------------------------------------------

Finds duplicate blocks across different namespaces and generates OEB datapacks
for block matching. Useful for mod compatibility and block unification.

Generates OEB datapack format:
- Datapack: data/oeb/replacements/example.json (requires OEI as dependency)

Usage:
    python -m tools.matchers.block_matcher [options]
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config_loader import load_paths_from_config, get_default_paths
from src.models.matcher import MatcherConfig
from src.processors.matcher import DuplicateMatcherProcessor
from src.processors.file_io import FileIOProcessor
from src.services.matcher_service import MatcherService


def main() -> None:
    """Main entry point for block matcher."""
    parser = argparse.ArgumentParser(
        description="Find duplicate blocks across namespaces and generate matching mappings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate OEB datapack (default, uses /input directory)
  python -m tools.matchers.block_matcher
  
  # Use config file for paths
  python -m tools.matchers.block_matcher --config paths.json
  
  # Non-interactive with pre-selected namespace
  python -m tools.matchers.block_matcher --namespace minecraft --no-interactive
  
  # Custom filename
  python -m tools.matchers.block_matcher --filename my_replacements.json
        """
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to configuration file for standard paths (JSON format)"
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
        "--filename",
        type=str,
        default=None,
        help="Name of the replacements file for OEB datapack (default: auto-named after target namespace)"
    )
    parser.add_argument(
        "--pack-format",
        type=int,
        default=10,
        help="Minecraft datapack format version for oeb-datapack (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Load paths from config
    paths = load_paths_from_config(args.config) if args.config else get_default_paths()
    
    # Create matcher configuration
    # Note: filename will be set automatically based on selected namespace
    config = MatcherConfig(
        input_dir=paths.input,
        output_dir=paths.output / "oeb_datapack",
        datapack_path="oeb",
        match_field="matchBlock",
        result_field="resultBlock",
        description="OneEnough Blocks replacements",
        pack_format=args.pack_format,
        filename=args.filename if args.filename else "replacements.json"  # Will be overridden by service
    )
    
    # Create components
    file_io = FileIOProcessor()
    processor = DuplicateMatcherProcessor(file_io)
    
    # Create service and run
    service = MatcherService(processor, file_io)
    
    try:
        output_file = service.run_duplicate_matcher(
            config,
            result_ns=args.namespace.lower() if args.namespace else None,
            interactive=not args.no_interactive
        )
        
        if output_file and output_file.exists():
            from src.utils.logging import log
            log(f"Datapack generated at: {config.output_dir.resolve()}", "INFO")
            log(f"Install by copying to: .minecraft/saves/<world>/datapacks/", "INFO")
            log("Note: Requires OEI as a dependency", "INFO")
    except ValueError as e:
        from src.utils.logging import log
        log(str(e), "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
