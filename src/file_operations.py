"""File operations utilities for all processors.

This module provides centralized file I/O operations including reading,
writing, finding files, and thread-safe operations.
"""

from __future__ import annotations
import json
import threading
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional


# Thread-safe writing utilities
_write_locks: Dict[Path, threading.Lock] = {}
_write_locks_lock = threading.Lock()


def get_lock(path: Path) -> threading.Lock:
    """Get or create a thread-safe lock for a file path.
    
    Args:
        path: The file path to get a lock for
        
    Returns:
        A threading.Lock object for the specified path
    """
    with _write_locks_lock:
        if path not in _write_locks:
            _write_locks[path] = threading.Lock()
        return _write_locks[path]


# ---------------------------------------------------------------------
# Text file operations
# ---------------------------------------------------------------------
def read_text_file(file_path: Path, errors: str = "strict") -> str:
    """Read entire text file as string.
    
    Args:
        file_path: Path to the file to read
        errors: Error handling mode (default: "strict", use "ignore" for binary-like files)
        
    Returns:
        File contents as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    with file_path.open("r", encoding="utf-8", errors=errors) as f:
        return f.read()


def read_text_lines(file_path: Path) -> List[str]:
    """Read text file as list of lines.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        List of lines (with newlines preserved)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    with file_path.open("r", encoding="utf-8") as f:
        return f.readlines()


def read_text_lines_stripped(file_path: Path) -> List[str]:
    """Read text file as list of lines (stripped of whitespace).
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        List of lines (whitespace stripped, empty lines excluded)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    with file_path.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def write_text_file(file_path: Path, content: str) -> None:
    """Write text content to file.
    
    Args:
        file_path: Path to the file to write
        content: Text content to write
        
    Raises:
        IOError: If file cannot be written
    """
    with file_path.open("w", encoding="utf-8") as f:
        f.write(content)


def write_text_lines(file_path: Path, lines: List[str]) -> None:
    """Write lines to file.
    
    Args:
        file_path: Path to the file to write
        lines: List of strings to write (should include newlines if needed)
        
    Raises:
        IOError: If file cannot be written
    """
    with file_path.open("w", encoding="utf-8") as f:
        f.writelines(lines)


def append_text_lines(file_path: Path, lines: List[str]) -> None:
    """Thread-safely append lines to a file.
    
    This function uses file-level locking to ensure that multiple threads
    can safely write to the same file without data corruption.
    
    Args:
        file_path: Path to the file to write to
        lines: List of strings to write (should include newlines if needed)
        
    Raises:
        IOError: If file cannot be written
    """
    lock = get_lock(file_path)
    with lock:
        with file_path.open("a", encoding="utf-8") as f:
            f.writelines(lines)


# ---------------------------------------------------------------------
# JSON file operations
# ---------------------------------------------------------------------
def read_json_file(file_path: Path) -> Any:
    """Read JSON from file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        IOError: If file cannot be read
    """
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(file_path: Path, data: Any, indent: int = 2) -> None:
    """Write JSON to file.
    
    Args:
        file_path: Path to the file to write
        data: Data to serialize as JSON
        indent: JSON indentation (default: 2)
        
    Raises:
        IOError: If file cannot be written
    """
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)


# ---------------------------------------------------------------------
# File finding operations
# ---------------------------------------------------------------------
def find_files(
    directory: Path,
    pattern: str,
    recursive: bool = False
) -> List[Path]:
    """Find files matching pattern in directory.
    
    Args:
        directory: Directory to search
        pattern: Glob pattern (e.g., "*.txt", "*.jar")
        recursive: If True, search recursively (default: False)
        
    Returns:
        List of matching file paths (sorted)
    """
    if not directory.exists():
        return []
    
    files: List[Path] = []
    if recursive:
        files.extend(directory.rglob(pattern))
    else:
        files.extend(directory.glob(pattern))
    
    # Filter to files only and sort
    return sorted([f for f in files if f.is_file()])


def find_txt_files(directory: Path, recursive: bool = True) -> List[Path]:
    """Find all .txt files in directory.
    
    Args:
        directory: Directory to search
        recursive: If True, search recursively (default: True)
        
    Returns:
        List of .txt file paths (sorted, deduplicated)
    """
    return sorted(set(find_files(directory, "*.txt", recursive=recursive)))


def find_jar_files(directory: Path) -> List[Path]:
    """Find all .jar files in directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of .jar file paths (sorted)
    """
    return find_files(directory, "*.jar", recursive=False)


# ---------------------------------------------------------------------
# Namespace:object file operations
# ---------------------------------------------------------------------
def read_namespace_object_lines(file_path: Path) -> List[tuple[str, str]]:
    """Read namespace:object lines from file.
    
    Args:
        file_path: Path to file containing namespace:object lines
        
    Returns:
        List of (namespace, object_id) tuples
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    results: List[tuple[str, str]] = []
    try:
        lines = read_text_lines_stripped(file_path)
        for line in lines:
            if ":" not in line:
                continue
            ns, obj_id = line.split(":", 1)
            results.append((ns.lower().strip(), obj_id.lower().strip()))
    except Exception as e:
        # Import here to avoid circular dependency
        from src.utils import log
        log(f"Error reading {file_path}: {e}", "ERROR")
    return results


def write_namespace_object_lines(file_path: Path, entries: List[str]) -> None:
    """Write namespace:object lines to file.
    
    Args:
        file_path: Path to the file to write
        entries: List of namespace:object strings (one per line)
        
    Raises:
        IOError: If file cannot be written
    """
    sorted_entries = sorted(set(entries))
    lines = [entry + "\n" for entry in sorted_entries]
    write_text_lines(file_path, lines)

