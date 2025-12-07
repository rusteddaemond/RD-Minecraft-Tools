"""Common utility functions for Minecraft modding tools.

This module provides shared utilities used across multiple tools, including
thread-safe file writing, logging, timestamp generation, and directory management.
"""

from __future__ import annotations
import threading
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List


# Thread-safe writing utilities
_write_locks: Dict[Path, threading.Lock] = {}
_write_locks_lock = threading.Lock()


def get_lock(path: Path) -> threading.Lock:
    """Get or create a thread-safe lock for a file path.
    
    This function ensures that each file path has its own lock, allowing
    concurrent writes to different files while preventing race conditions
    when multiple threads write to the same file.
    
    Args:
        path: The file path to get a lock for
        
    Returns:
        A threading.Lock object for the specified path
        
    Note:
        Locks are cached in a global dictionary. The same path will always
        return the same lock instance.
    """
    with _write_locks_lock:
        if path not in _write_locks:
            _write_locks[path] = threading.Lock()
        return _write_locks[path]


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
    lock = get_lock(out_file)
    with lock:
        with out_file.open("a", encoding="utf-8") as f:
            f.writelines(lines)


def utc_now_str() -> str:
    """Get current UTC time as ISO format string.
    
    Returns:
        ISO 8601 formatted timestamp string (e.g., "2024-01-01T12:00:00+00:00")
        
    Example:
        >>> timestamp = utc_now_str()
        >>> isinstance(timestamp, str)
        True
    """
    return datetime.now(timezone.utc).isoformat()


def log(msg: str, prefix: str = "") -> None:
    """Log a message with timestamp.
    
    Prints a formatted log message with UTC timestamp. Optional prefix
    can be used to categorize messages (e.g., "ERROR", "WARN", "OK").
    
    Args:
        msg: The message to log
        prefix: Optional prefix to categorize the message
        
    Example:
        >>> log("Processing started", "INFO")
        [2024-01-01T12:00:00+00:00] [INFO] Processing started
    """
    timestamp = utc_now_str()
    if prefix:
        print(f"[{timestamp}] [{prefix}] {msg}")
    else:
        print(f"[{timestamp}] {msg}")


def get_project_root() -> Path:
    """Get the project root directory.
    
    Returns:
        Path to the project root (parent of src directory)
    """
    return Path(__file__).parent.parent


def create_directory_with_fallback(
    base_path: Path,
    subdirs: List[str],
    fallback_prefix: str = "temp_"
) -> Path:
    """Create directory with fallback to temp if permission denied.
    
    Attempts to create a directory structure at base_path/subdirs. If a
    PermissionError occurs, falls back to creating the structure in a
    temporary directory.
    
    Args:
        base_path: Base path for the directory structure
        subdirs: List of subdirectory names to create (e.g., ["logs", "blocks"])
        fallback_prefix: Prefix for temporary directory name
        
    Returns:
        Path to the created directory (either at base_path or in temp)
        
    Example:
        >>> path = create_directory_with_fallback(Path("/project"), ["logs", "blocks"])
        >>> path.exists()
        True
    """
    target_path = base_path
    for subdir in subdirs:
        target_path = target_path / subdir
    
    try:
        target_path.mkdir(parents=True, exist_ok=True)
        # Test write permission
        test_file = base_path / "_write_test.tmp"
        with test_file.open("w", encoding="utf-8") as f:
            f.write("test")
        test_file.unlink(missing_ok=True)
        return target_path
    except PermissionError:
        # Fallback to temp directory
        tempdir = Path(tempfile.mkdtemp(prefix=fallback_prefix))
        fallback_path = tempdir
        for subdir in subdirs:
            fallback_path = fallback_path / subdir
        fallback_path.mkdir(parents=True, exist_ok=True)
        log(f"Access denied to {base_path}. Using temp dir: {tempdir}", "WARN")
        return fallback_path

