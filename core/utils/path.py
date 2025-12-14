"""
Path validation utilities.
"""

from pathlib import Path
from typing import Optional

from core.utils.logging import log_warning, log_error


def validate_directory(
    path: Path,
    create: bool = False,
    error_on_fail: bool = False
) -> bool:
    """
    Validate that a path exists and is a directory.
    
    Args:
        path: Path to validate
        create: If True, create directory if it doesn't exist
        error_on_fail: If True, log error and return False; otherwise log warning
        
    Returns:
        True if path is a valid directory, False otherwise
    """
    if not path.exists():
        if create:
            try:
                path.mkdir(parents=True, exist_ok=True)
                return True
            except OSError as e:
                if error_on_fail:
                    log_error(f"Failed to create directory {path}: {e}")
                else:
                    log_warning(f"Failed to create directory {path}: {e}")
                return False
        else:
            if error_on_fail:
                log_error(f"Directory does not exist: {path}")
            else:
                log_warning(f"Directory does not exist: {path}")
            return False
    
    if not path.is_dir():
        if error_on_fail:
            log_error(f"Path is not a directory: {path}")
        else:
            log_warning(f"Path is not a directory: {path}")
        return False
    
    return True


def validate_file(
    path: Path,
    error_on_fail: bool = False
) -> bool:
    """
    Validate that a path exists and is a file.
    
    Args:
        path: Path to validate
        error_on_fail: If True, log error and return False; otherwise log warning
        
    Returns:
        True if path is a valid file, False otherwise
    """
    if not path.exists():
        if error_on_fail:
            log_error(f"File does not exist: {path}")
        else:
            log_warning(f"File does not exist: {path}")
        return False
    
    if not path.is_file():
        if error_on_fail:
            log_error(f"Path is not a file: {path}")
        else:
            log_warning(f"Path is not a file: {path}")
        return False
    
    return True

