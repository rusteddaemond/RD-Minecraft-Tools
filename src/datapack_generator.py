"""Datapack generation utilities for Minecraft mods.

This module provides shared functions for generating Minecraft datapacks
for mods like OEI (OneEnough Items), OEF (One Enough Fluid), and OEB (OneEnough Blocks).
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any

from src.file_operations import write_json_file


def create_datapack_structure(output_dir: Path, mod_name: str) -> Path:
    """Create datapack directory structure.
    
    Args:
        output_dir: Base output directory
        mod_name: Mod name (e.g., 'oei', 'oef', 'oeb')
    
    Returns:
        Path to the replacements directory
    """
    replacements_dir = output_dir / "data" / mod_name / "replacements"
    replacements_dir.mkdir(parents=True, exist_ok=True)
    return replacements_dir


def generate_replacements_file(
    config: List[Dict[str, Any]],
    replacements_dir: Path,
    filename: str = "replacements.json"
) -> Path:
    """Generate the replacements JSON file for datapack.
    
    Args:
        config: Configuration list
        replacements_dir: Directory to write the file
        filename: Name of the output file
        
    Returns:
        Path to the generated file
    """
    output_file = replacements_dir / filename
    
    # Datapacks expect the replacements in JSON format
    write_json_file(output_file, config, indent=4)
    
    return output_file


def create_pack_mcmeta(
    output_dir: Path,
    pack_format: int = 10,
    description: str = "Minecraft datapack"
) -> None:
    """Create pack.mcmeta file for the datapack.
    
    Args:
        output_dir: Base output directory
        pack_format: Minecraft datapack format version (default: 10)
        description: Description for the datapack
    """
    pack_mcmeta = output_dir / "pack.mcmeta"
    
    meta = {
        "pack": {
            "pack_format": pack_format,
            "description": description
        }
    }
    
    write_json_file(pack_mcmeta, meta, indent=2)
