"""Common utility functions for Minecraft modding tools.

This module provides shared utilities used across multiple tools, including
logging, timestamp generation, and directory management.

Note: This module now re-exports from src.utils.* for backward compatibility.
New code should import directly from src.utils.* modules.
"""

from __future__ import annotations
from pathlib import Path
from typing import List

from src.file_operations import append_text_lines

# Re-export from new utils modules for backward compatibility
from src.utils.logging import log, utc_now_str
from src.utils.config import get_project_root, create_directory_with_fallback

# Re-export for backward compatibility
def write_entry(out_file: Path, lines: list[str]) -> None:
    """Thread-safely append lines to a file.
    
    This function uses file-level locking to ensure that multiple threads
    can safely write to the same file without data corruption. Lines are
    appended to the file in the order they are received (per thread).
    
    Args:
        out_file: Path to the file to write to
        lines: List of strings to write (should include newlines if needed)
        
    Example:
        >>> write_entry(Path("output.txt"), ["line1\\n", "line2\\n"])
    """
    append_text_lines(out_file, lines)

