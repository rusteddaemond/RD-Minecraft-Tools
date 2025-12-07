"""Threading utilities.

Pure threading/concurrency functions with no business logic.
"""

from __future__ import annotations
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, List

from src.utils.logging import log


def execute_concurrent(
    items: List[Any],
    process_func: Callable,
    max_workers: int | None = None,
    verbose: bool = False
) -> None:
    """Execute function concurrently on items using ThreadPoolExecutor.
    
    This function handles thread pool creation, task submission, and error
    handling for concurrent processing of items.
    
    Args:
        items: List of items to process
        process_func: Function to call for each item (will receive item as first arg)
        max_workers: Maximum number of worker threads (default: CPU count)
        verbose: If True, print full tracebacks for errors
        
    Example:
        >>> def process_file(path):
        ...     print(f"Processing {path}")
        >>> files = [Path("a.jar"), Path("b.jar")]
        >>> execute_concurrent(files, process_file, max_workers=2)
    """
    import os
    
    if max_workers is None:
        max_workers = os.cpu_count() or 4
    
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            pool.submit(process_func, item)
            for item in items
        ]
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                log(f"Thread error: {e}", "THREAD ERROR")
                if verbose:
                    traceback.print_exc()
