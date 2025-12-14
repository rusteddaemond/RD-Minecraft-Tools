#!/usr/bin/env python3
"""
JAR Utilities
Common functions for working with JAR/ZIP files.
"""

import zipfile
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)


@contextmanager
def open_jar_safe(jar_path: Path | str) -> Iterator[zipfile.ZipFile]:
    """
    Safely open a JAR file with error handling.
    
    Args:
        jar_path: Path to JAR file
    
    Yields:
        ZipFile object
    
    Example:
        with open_jar_safe('mod.jar') as jar:
            files = jar.namelist()
    """
    try:
        with zipfile.ZipFile(jar_path, 'r') as jar:
            yield jar
    except (zipfile.BadZipFile, OSError) as e:
        logger.debug(f"Failed to open JAR {jar_path}: {e}")
        # Yield a dummy object that won't cause errors
        class DummyZipFile:
            def namelist(self):
                return []
        yield DummyZipFile()


def extract_namespaces_from_jar(jar_path: Path | str) -> set[str]:
    """
    Extract all namespaces from a JAR file's data/ directory.
    
    Args:
        jar_path: Path to JAR file
    
    Returns:
        Set of namespace strings found in data/ directory
    """
    namespaces = set()
    try:
        with zipfile.ZipFile(jar_path, 'r') as jar:
            for file_path in jar.namelist():
                if file_path.startswith('data/') and '/' in file_path[5:]:
                    parts = file_path.split('/')
                    if len(parts) >= 2:
                        namespace = parts[1]
                        namespaces.add(namespace)
    except (zipfile.BadZipFile, OSError) as e:
        logger.debug(f"Failed to extract namespaces from JAR {jar_path}: {e}")
    
    return namespaces

