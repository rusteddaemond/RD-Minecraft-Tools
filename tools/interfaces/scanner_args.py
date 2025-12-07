"""Scanner argument parsing interfaces.

This module provides shared argument parsing functions for all scanner tools.
"""

from __future__ import annotations
import argparse
from pathlib import Path
from typing import Optional

from src.arg_parser import (
    add_common_jar_args,
    add_namespace_filter_arg
)
from src.config_loader import StandardPaths, load_paths_from_config, get_default_paths


def add_scanner_input_args(parser: argparse.ArgumentParser) -> None:
    """Add common input arguments for scanner tools.
    
    Adds:
    - --config: Path to configuration file for standard paths (optional)
    - --threads: Number of worker threads
    - --namespace: Filter by namespace
    - --verbose: Enable verbose error output
    
    Args:
        parser: ArgumentParser instance to add arguments to
    """
    add_common_jar_args(parser)
    add_namespace_filter_arg(parser)


def add_scanner_output_args(parser: argparse.ArgumentParser) -> None:
    """Add common output arguments for scanner tools.
    
    Adds:
    - --skip-raw: Delete raw files after cleaning
    
    Args:
        parser: ArgumentParser instance to add arguments to
    """
    # skip-raw is already included in add_common_jar_args
    pass


def add_scanner_cleaning_args(parser: argparse.ArgumentParser) -> None:
    """Add cleaning arguments for scanner tools.
    
    Note: Cleaning now uses thorough convergence-based approach (no passes needed).
    This function is kept for backward compatibility but does nothing.
    
    Args:
        parser: ArgumentParser instance to add arguments to
    """
    # Cleaning is now thorough and automatic, no arguments needed
    pass
