"""Configuration utilities.

Pure configuration helper functions with no business logic.
"""

from __future__ import annotations
import tempfile
from pathlib import Path
from typing import List

from src.utils.logging import log
from src.file_operations import write_text_file


def get_project_root() -> Path:
    """Get the project root directory.
    
    Returns:
        Path to the project root (parent of src directory)
    """
    return Path(__file__).parent.parent.parent


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
        write_text_file(test_file, "test")
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
