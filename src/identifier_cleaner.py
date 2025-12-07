"""Identifier cleaning utilities for scanner output.

This module provides thorough cleaning of identifiers extracted from JAR files,
removing file extensions and affixes until convergence (no more changes).
"""

from __future__ import annotations
from typing import Tuple
from src.affix_cleaner import AFFIXES, DEFAULT_EXTENSIONS, FLUID_EXTENSIONS


def clean_identifier_thorough(
    stem: str,
    extensions: Tuple[str, ...] = DEFAULT_EXTENSIONS,
    max_iterations: int = 100
) -> str:
    """Thoroughly clean identifier by removing extensions and affixes until convergence.
    
    Continues cleaning until no more changes occur, ensuring all affixes
    and extensions are removed regardless of nesting depth.
    
    Args:
        stem: The identifier to clean
        extensions: Tuple of file extensions to remove
        max_iterations: Maximum iterations to prevent infinite loops (default: 100)
        
    Returns:
        Cleaned identifier
    """
    previous = stem
    iterations = 0
    
    while iterations < max_iterations:
        # Remove extensions
        for ext in extensions:
            if stem.endswith(ext):
                stem = stem[:-len(ext)]
        
        # Remove affixes
        for affix in AFFIXES:
            if stem.endswith(affix):
                stem = stem[:-len(affix)]
        
        # Check for convergence
        if stem == previous:
            break
        
        previous = stem
        iterations += 1
    
    return stem


def clean_namespace_object_line(
    line: str,
    extensions: Tuple[str, ...] = DEFAULT_EXTENSIONS
) -> str | None:
    """Clean a namespace:object line.
    
    Args:
        line: Line in format "namespace:object_id"
        extensions: Tuple of file extensions to remove
        
    Returns:
        Cleaned line in format "namespace:cleaned_object_id", or None if invalid
    """
    line = line.strip()
    if not line or ":" not in line:
        return None
    
    ns, obj_id = line.split(":", 1)
    cleaned_id = clean_identifier_thorough(obj_id, extensions)
    
    return f"{ns}:{cleaned_id}"
