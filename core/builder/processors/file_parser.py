"""
File parser for reading txt files containing namespace:id entries.

This module provides functionality to parse text files containing Minecraft
item/block/fluid identifiers in the format namespace:id.
"""

import sys
from pathlib import Path
from typing import Set, List
from core.utils.file import read_items_from_file
from core.utils.logging import log_warning


class FileParser:
    """Parser for txt files containing namespace:id entries."""
    
    @staticmethod
    def parse_txt_file(file_path: Path) -> Set[str]:
        """
        Parse single txt file and extract namespace:id entries.
        
        Args:
            file_path: Path to the txt file
            
        Returns:
            Set of namespace:id entries found in the file. Returns empty set
            if file doesn't exist or cannot be read.
            
        Note:
            - Skips empty lines and comment lines (starting with #)
            - Handles lines with additional metadata (takes first space-separated token)
            - Silently handles file I/O errors
        """
        if not file_path.exists():
            log_warning(f"File not found: {file_path}")
            return set()
        
        if not file_path.is_file():
            log_warning(f"Path is not a file: {file_path}")
            return set()
        
        # Use shared file reading utility with metadata handling
        return read_items_from_file(
            file_path,
            skip_comments=True,
            skip_tag_refs=True,
            handle_metadata=True  # Handle lines with metadata (e.g., "item_id Inputs: ...")
        )
    
    @staticmethod
    def parse_txt_files(file_paths: List[Path]) -> Set[str]:
        """
        Parse multiple txt files and extract namespace:id entries.
        
        Args:
            file_paths: List of paths to txt files. Empty list returns empty set.
            
        Returns:
            Set of all unique namespace:id entries found in all files.
            Duplicates across files are automatically deduplicated.
        """
        if not file_paths:
            return set()
        
        all_items = set()
        
        for file_path in file_paths:
            items = FileParser.parse_txt_file(file_path)
            all_items.update(items)
        
        return all_items

