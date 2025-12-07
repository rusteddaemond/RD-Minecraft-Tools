#!/usr/bin/env python3
"""
Fluid Matcher for One Enough Fluid (OEF)
-----------------------------------------

Reads a JSON configuration file and generates datapacks for the One Enough Fluid mod.
Creates replacement mappings at data/oef/replacements.

OEF is an add-on for OEI that extends OEI's fluid-replacement functionality.
It enables fluid replacement for blocks, items and recipes — any fluid that JEI can display can be replaced.

Usage:
    python -m tools.fluid_matcher [options]
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils import log


# ---------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------
def find_json_files(directory: Path) -> List[Path]:
    """Find all .json files in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of .json file paths
    """
    json_files: List[Path] = []
    if not directory.exists():
        return json_files
    
    json_files.extend(directory.glob("*.json"))
    # Also search recursively
    json_files.extend(directory.rglob("*.json"))
    
    return sorted(set(json_files))  # Remove duplicates and sort


def load_configs_from_directory(input_dir: Path) -> List[Dict[str, Any]]:
    """Load and combine configurations from all JSON files in a directory.
    
    Args:
        input_dir: Directory containing JSON configuration files
        
    Returns:
        Combined configuration list from all files
        
    Raises:
        SystemExit: If directory doesn't exist or no files found
    """
    if not input_dir.exists():
        log(f"Input directory does not exist: {input_dir}", "ERROR")
        sys.exit(1)
    
    if not input_dir.is_dir():
        log(f"Input path is not a directory: {input_dir}", "ERROR")
        sys.exit(1)
    
    json_files = find_json_files(input_dir)
    if not json_files:
        log(f"No .json files found in {input_dir}", "ERROR")
        sys.exit(1)
    
    log(f"Found {len(json_files)} JSON file(s) in {input_dir}", "OK")
    
    all_config: List[Dict[str, Any]] = []
    
    for json_file in json_files:
        try:
            log(f"Loading {json_file.name}...")
            config = load_config(json_file)
            all_config.extend(config)
            log(f"Loaded {len(config)} rule(s) from {json_file.name}", "OK")
        except SystemExit:
            # load_config already logged the error and exited
            raise
        except Exception as e:
            log(f"Error processing {json_file.name}: {e}", "WARN")
            continue
    
    return all_config


# ---------------------------------------------------------------------
# Configuration validation
# ---------------------------------------------------------------------
def validate_config(config: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Validate configuration data.
    
    Args:
        config: Configuration list with matchFluid and resultFluid
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(config, list):
        return False, "Configuration must be a list"
    
    for idx, entry in enumerate(config):
        if not isinstance(entry, dict):
            return False, f"Entry {idx} must be a dictionary"
        
        if "matchFluid" not in entry:
            return False, f"Entry {idx} missing 'matchFluid' field"
        
        if "resultFluid" not in entry:
            return False, f"Entry {idx} missing 'resultFluid' field"
        
        match_fluid = entry["matchFluid"]
        if not isinstance(match_fluid, list):
            return False, f"Entry {idx}: 'matchFluid' must be a list"
        
        if not match_fluid:
            return False, f"Entry {idx}: 'matchFluid' cannot be empty"
        
        result_fluid = entry["resultFluid"]
        if not isinstance(result_fluid, str):
            return False, f"Entry {idx}: 'resultFluid' must be a string"
        
        # Check for self-replacement
        if result_fluid in match_fluid:
            return False, (
                f"Entry {idx}: Cannot replace fluid with itself. "
                f"'{result_fluid}' is in both matchFluid and resultFluid"
            )
    
    return True, ""


def load_config(config_file: Path) -> List[Dict[str, Any]]:
    """Load and validate configuration from JSON file.
    
    Args:
        config_file: Path to JSON configuration file
        
    Returns:
        Validated configuration list
        
    Raises:
        SystemExit: If file cannot be read or is invalid
    """
    try:
        with config_file.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        log(f"Configuration file not found: {config_file}", "ERROR")
        sys.exit(1)
    except json.JSONDecodeError as e:
        log(f"Invalid JSON in configuration file: {e}", "ERROR")
        sys.exit(1)
    except Exception as e:
        log(f"Error reading configuration file: {e}", "ERROR")
        sys.exit(1)
    
    is_valid, error_msg = validate_config(config)
    if not is_valid:
        log(f"Configuration validation failed: {error_msg}", "ERROR")
        sys.exit(1)
    
    return config


# ---------------------------------------------------------------------
# Datapack generation
# ---------------------------------------------------------------------
def create_datapack_structure(output_dir: Path) -> Path:
    """Create the datapack directory structure.
    
    Args:
        output_dir: Base output directory
        
    Returns:
        Path to the replacements directory
    """
    replacements_dir = output_dir / "data" / "oef" / "replacements"
    replacements_dir.mkdir(parents=True, exist_ok=True)
    return replacements_dir


def generate_replacements_file(
    config: List[Dict[str, Any]],
    replacements_dir: Path,
    filename: str = "replacements.json"
) -> Path:
    """Generate the replacements JSON file for OEF.
    
    Args:
        config: Configuration list
        replacements_dir: Directory to write the file
        filename: Name of the output file
        
    Returns:
        Path to the generated file
    """
    output_file = replacements_dir / filename
    
    # OEF expects the replacements in the same format as the config
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    
    return output_file


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
            "description": "One Enough Fluid replacements"
        }
    }
    
    with pack_mcmeta.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


# ---------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------
def main() -> None:
    """Main entry point for fluid matcher."""
    parser = argparse.ArgumentParser(
        description="Generate One Enough Fluid datapack from JSON configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate datapack from default input directory (/input)
  python -m tools.fluid_matcher
  
  # Generate datapack from config.json
  python -m tools.fluid_matcher --config config.json
  
  # Generate datapack from directory of JSON files
  python -m tools.fluid_matcher --input-dir ./configs/fluids
  
  # Specify custom output directory
  python -m tools.fluid_matcher --config config.json --output-dir ./datapacks/oef
  
  # Custom pack format
  python -m tools.fluid_matcher --config config.json --pack-format 15

Configuration format:
  [
      {
          "matchFluid": [
              "minecraft:water",
              "minecraft:lava",
              "forge:crude_oil"
          ],
          "resultFluid": "minecraft:water"
      }
  ]

Notes:
  - OEF is an add-on for OEI that extends fluid-replacement functionality
  - Datapack fields are "matchFluid" and "resultFluid", not "matchItems" and "resultItems"
  - For hot-reloaded recipes you may need to reload twice for changes to take full effect
  - Some mods serialize fluid fields in ways outside OEF's handling, so those fluids cannot be replaced
        """
    )
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument(
        "--config",
        type=Path,
        help="Path to JSON configuration file"
    )
    input_group.add_argument(
        "--input-dir",
        type=Path,
        default=Path("/input"),
        help="Directory containing JSON configuration files (all .json files will be processed) (default: /input)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("oef_datapack"),
        help="Output directory for datapack (default: oef_datapack)"
    )
    parser.add_argument(
        "--pack-format",
        type=int,
        default=10,
        help="Minecraft datapack format version (default: 10)"
    )
    parser.add_argument(
        "--filename",
        type=str,
        default="replacements.json",
        help="Name of the replacements file (default: replacements.json)"
    )
    
    args = parser.parse_args()
    
    # Load configuration from file or directory
    if args.config:
        # Single file mode
        if not args.config.exists():
            log(f"Configuration file does not exist: {args.config}", "ERROR")
            sys.exit(1)
        
        if not args.config.is_file():
            log(f"Configuration path is not a file: {args.config}", "ERROR")
            sys.exit(1)
        
        log(f"Loading configuration from {args.config}")
        config = load_config(args.config)
        log(f"Loaded {len(config)} replacement rule(s)", "OK")
    else:
        # Directory mode (uses default /input if neither --config nor --input-dir specified)
        log(f"Loading configurations from directory: {args.input_dir}")
        config = load_configs_from_directory(args.input_dir)
        log(f"Loaded {len(config)} total replacement rule(s) from directory", "OK")
    
    # Create datapack structure
    log(f"Creating datapack structure in {args.output_dir}")
    replacements_dir = create_datapack_structure(args.output_dir)
    
    # Generate replacements file
    log("Generating replacements file...")
    output_file = generate_replacements_file(config, replacements_dir, args.filename)
    log(f"Generated {output_file.name}", "OK")
    
    # Create pack.mcmeta
    log("Creating pack.mcmeta...")
    create_pack_mcmeta(args.output_dir, args.pack_format)
    log("Created pack.mcmeta", "OK")
    
    log(f"\nDatapack generated successfully at: {args.output_dir.resolve()}")
    log(f"Install by copying to: .minecraft/saves/<world>/datapacks/")
    log("Note: Requires OEI as a dependency", "INFO")


if __name__ == "__main__":
    main()
