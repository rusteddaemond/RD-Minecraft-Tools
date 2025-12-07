"""Logging utilities.

Pure logging functions with no business logic.
"""

from __future__ import annotations
from datetime import datetime, timezone


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
