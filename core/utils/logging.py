"""
Logging utilities for consistent error and warning messages.
"""

import sys
from pathlib import Path
from typing import Optional


def log_warning(message: str, file_path: Optional[Path] = None) -> None:
    """
    Log a warning message to stderr.
    
    Args:
        message: Warning message to display
        file_path: Optional file path to include in message
    """
    if file_path:
        print(f"Warning: {message}: {file_path}", file=sys.stderr)
    else:
        print(f"Warning: {message}", file=sys.stderr)


def log_error(message: str, exit_code: Optional[int] = None, file_path: Optional[Path] = None) -> None:
    """
    Log an error message to stderr and optionally exit.
    
    Args:
        message: Error message to display
        exit_code: Optional exit code (if provided, sys.exit() is called)
        file_path: Optional file path to include in message
    """
    if file_path:
        print(f"Error: {message}: {file_path}", file=sys.stderr)
    else:
        print(f"Error: {message}", file=sys.stderr)
    
    if exit_code is not None:
        sys.exit(exit_code)

