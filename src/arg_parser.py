"""Common argument parsing utilities.

This module provides shared argument parser functions used across multiple
JAR processing tools to ensure consistency and reduce duplication.
"""

from __future__ import annotations
import argparse
import os
from pathlib import Path
from typing import Optional

from src.config_loader import StandardPaths, load_paths_from_config, get_default_paths


def add_common_jar_args(parser: argparse.ArgumentParser) -> None:
    """Add common arguments for JAR processing tools.
    
    Adds the following arguments:
    - --config: Path to configuration file for standard paths (optional)
    - --threads: Number of worker threads (default: CPU count)
    - --verbose: Enable verbose error output
    - --skip-raw: Delete raw files after cleaning
    
    Args:
        parser: ArgumentParser instance to add arguments to
    """
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to configuration file for standard paths (JSON format)"
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help="Number of worker threads (default: CPU count)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose error output"
    )
    parser.add_argument(
        "--skip-raw",
        action="store_true",
        help="Delete raw files after cleaning"
    )


def add_namespace_filter_arg(parser: argparse.ArgumentParser) -> None:
    """Add namespace filter argument.
    
    Args:
        parser: ArgumentParser instance to add argument to
    """
    parser.add_argument(
        "--namespace",
        type=str,
        default=None,
        help="Filter by specific namespace (case-insensitive)"
    )


def get_thread_count(args) -> int:
    """Get thread count from args or default to CPU count.
    
    Args:
        args: Parsed arguments object with optional 'threads' attribute
        
    Returns:
        Number of threads to use (at least 1)
    """
    return args.threads or os.cpu_count() or 4
