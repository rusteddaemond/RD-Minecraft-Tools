"""Thread pool execution utilities.

This module provides standardized concurrent execution patterns using
ThreadPoolExecutor for processing multiple items in parallel.

Note: This module now re-exports from src.utils.threading for backward compatibility.
New code should import directly from src.utils.threading.
"""

from __future__ import annotations
from typing import Any, Callable, List

# Re-export from new utils module for backward compatibility
from src.utils.threading import execute_concurrent

__all__ = ["execute_concurrent"]
