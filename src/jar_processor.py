"""JAR file processing utilities.

This module provides common functions for discovering, validating, and processing
JAR files used across multiple scanning tools.
"""

from __future__ import annotations
import zipfile
from pathlib import Path
from typing import List, Tuple

from src.utils import get_project_root, create_directory_with_fallback, log


def find_jar_files(input_dir: Path) -> List[Path]:
    """Find and validate JAR files in directory.
    
    Args:
        input_dir: Directory to search for JAR files
        
    Returns:
        List of Path objects for found JAR files
        
    Raises:
        ValueError: If no JAR files are found
    """
    jars = list(input_dir.glob("*.jar"))
    if not jars:
        raise ValueError(f"No .jar files found in {input_dir}")
    return jars


def validate_input_directory(input_dir: Path) -> None:
    """Validate input directory exists and is a directory.
    
    Args:
        input_dir: Path to validate
        
    Raises:
        ValueError: If directory doesn't exist or is not a directory
    """
    if not input_dir.exists():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    
    if not input_dir.is_dir():
        raise ValueError(f"Input path is not a directory: {input_dir}")


def validate_jar_file(jar_path: Path) -> bool:
    """Validate that a file is a valid JAR/ZIP file.
    
    Args:
        jar_path: Path to the JAR file to validate
        
    Returns:
        True if the file is a valid JAR, False otherwise
    """
    try:
        with zipfile.ZipFile(jar_path, "r") as zf:
            # Try to read the file list to ensure it's valid
            _ = zf.namelist()
        return True
    except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError):
        return False


def create_output_dirs(category: str) -> Tuple[Path, Path]:
    """Create raw (logs) and cleaned (output) directories for a category.
    
    Creates directory structure for storing raw and cleaned output files.
    Raw files go to logs/{category}/, cleaned files go to output/{category}/.
    Falls back to temp directory if permission denied.
    
    Args:
        category: One of 'blocks', 'items', 'recipes'
    
    Returns:
        Tuple of (raw_dir, cleaned_dir)
        
    Example:
        >>> raw, cleaned = create_output_dirs("blocks")
        >>> raw.exists()
        True
        >>> cleaned.exists()
        True
    """
    project_root = get_project_root()
    
    raw_dir = create_directory_with_fallback(
        project_root,
        ["logs", category],
        fallback_prefix="jar_scan_"
    )
    
    cleaned_dir = create_directory_with_fallback(
        project_root,
        ["output", category],
        fallback_prefix="jar_scan_"
    )
    
    return raw_dir, cleaned_dir
