#!/usr/bin/env python3
"""
Items Matcher for OneEnough Items (OEI)
----------------------------------------

Reads a JSON configuration file and generates datapacks for the OneEnough Items mod.
Creates replacement mappings at data/oei/replacements.

Usage:
    python -m tools.items_matcher [options]
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
# Configuration validation
# ---------------------------------------------------------------------
def validate_config(config: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Validate configuration data.
    
    Args:
        config: Configuration list with matchItems and resultItems
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(config, list):
        return False, "Configuration must be a list"
    
    for idx, entry in enumerate(config):
        if not isinstance(entry, dict):
            return False, f"Entry {idx} must be a dictionary"
        
        if "matchItems" not in entry:
            return False, f"Entry {idx} missing 'matchItems' field"
        
        if "resultItems" not in entry:
            return False, f"Entry {idx} missing 'resultItems' field"
        
        match_items = entry["matchItems"]
        if not isinstance(match_items, list):
            return False, f"Entry {idx}: 'matchItems' must be a list"
        
        if not match_items:
            return False, f"Entry {idx}: 'matchItems' cannot be empty"
        
        result_item = entry["resultItems"]
        if not isinstance(result_item, str):
            return False, f"Entry {idx}: 'resultItems' must be a string"
        
        # Check for self-replacement
        if result_item in match_items:
            return False, (
                f"Entry {idx}: Cannot replace item with itself. "
                f"'{result_item}' is in both matchItems and resultItems"
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
    replacements_dir = output_dir / "data" / "oei" / "replacements"
    replacements_dir.mkdir(parents=True, exist_ok=True)
    return replacements_dir


def generate_replacements_file(
    config: List[Dict[str, Any]],
    replacements_dir: Path,
    filename: str = "replacements.json"
) -> Path:
    """Generate the replacements JSON file for OEI.
    
    Args:
        config: Configuration list
        replacements_dir: Directory to write the file
        filename: Name of the output file
        
    Returns:
        Path to the generated file
    """
    output_file = replacements_dir / filename
    
    # OEI expects the replacements in the same format as the config
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
            "description": "OneEnough Items replacements"
        }
    }
    
    with pack_mcmeta.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


# ---------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------
def main() -> None:
    """Main entry point for items matcher."""
    parser = argparse.ArgumentParser(
        description="Generate OneEnough Items datapack from JSON configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate datapack from config.json
  python -m tools.items_matcher --config config.json
  
  # Specify custom output directory
  python -m tools.items_matcher --config config.json --output-dir ./datapacks/oei
  
  # Custom pack format
  python -m tools.items_matcher --config config.json --pack-format 15

Configuration format:
  [
      {
          "matchItems": [
              "#forge:ore",
              "minecraft:potato",
              "minecraft:carrot"
          ],
          "resultItems": "minecraft:egg"
      }
  ]
        """
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to JSON configuration file"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("oei_datapack"),
        help="Output directory for datapack (default: oei_datapack)"
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
    
    # Validate config file exists
    if not args.config.exists():
        log(f"Configuration file does not exist: {args.config}", "ERROR")
        sys.exit(1)
    
    if not args.config.is_file():
        log(f"Configuration path is not a file: {args.config}", "ERROR")
        sys.exit(1)
    
    # Load and validate configuration
    log(f"Loading configuration from {args.config}")
    config = load_config(args.config)
    log(f"Loaded {len(config)} replacement rule(s)", "OK")
    
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


if __name__ == "__main__":
    main()
