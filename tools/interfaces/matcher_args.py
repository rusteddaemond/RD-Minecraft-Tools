"""Matcher argument parsing interfaces.

This module provides shared argument parsing functions for all matcher tools.
"""

from __future__ import annotations
import argparse
from pathlib import Path
from typing import Optional

from src.config_loader import StandardPaths, load_paths_from_config, get_default_paths


def add_matcher_input_args(parser: argparse.ArgumentParser) -> None:
    """Add common input arguments for matcher tools.
    
    Adds:
    - --config: Path to configuration file for standard paths (optional)
    
    Args:
        parser: ArgumentParser instance to add arguments to
    """
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to configuration file for standard paths (JSON format)"
    )


def add_matcher_output_args(parser: argparse.ArgumentParser) -> None:
    """Add common output arguments for matcher tools.
    
    Adds:
    - --filename: Name of the replacements file
    - --pack-format: Minecraft datapack format version
    
    Args:
        parser: ArgumentParser instance to add arguments to
    """
    parser.add_argument(
        "--filename",
        type=str,
        default="replacements.json",
        help="Name of the replacements file (default: replacements.json)"
    )
    parser.add_argument(
        "--pack-format",
        type=int,
        default=10,
        help="Minecraft datapack format version (default: 10)"
    )
