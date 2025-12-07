#!/usr/bin/env python3
"""
Fluid Matcher for One Enough Fluid (OEF)
-----------------------------------------

Finds duplicate fluids across different namespaces and generates OEF datapacks
for fluid matching. Useful for mod compatibility and fluid unification.

OEF is an add-on for OEI that extends OEI's fluid-replacement functionality.
It enables fluid replacement for blocks, items and recipes — any fluid that JEI can display can be replaced.

Generates OEF datapack format:
- Datapack: data/oef/replacements/replacements.json

Usage:
    python -m tools.matchers.fluid_matcher [options]
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
    """Main entry point for fluid matcher."""
    parser = argparse.ArgumentParser(
        description="Find duplicate fluids across namespaces and generate OEF datapack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate datapack from default input directory (/input)
  python -m tools.matchers.fluid_matcher
  
  # Use config file for paths
  python -m tools.matchers.fluid_matcher --config paths.json
  
  # Non-interactive with pre-selected namespace
  python -m tools.matchers.fluid_matcher --namespace minecraft --no-interactive
  
  # Custom filename
  python -m tools.matchers.fluid_matcher --filename my_replacements.json

Notes:
  - OEF is an add-on for OEI that extends fluid-replacement functionality
  - Datapack fields are "matchFluid" and "resultFluid"
  - For hot-reloaded recipes you may need to reload twice for changes to take full effect
  - Some mods serialize fluid fields in ways outside OEF's handling, so those fluids cannot be replaced
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
        help="Name of the replacements file (default: auto-named after target namespace)"
    )
    parser.add_argument(
        "--pack-format",
        type=int,
        default=10,
        help="Minecraft datapack format version (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Load paths from config
    paths = load_paths_from_config(args.config) if args.config else get_default_paths()
    
    # Create matcher configuration
    # Note: filename will be set automatically based on selected namespace
    config = MatcherConfig(
        input_dir=paths.input,
        output_dir=paths.output / "oef_datapack",
        datapack_path="oef",
        match_field="matchFluid",
        result_field="resultFluid",
        description="OneEnough Fluid replacements",
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
