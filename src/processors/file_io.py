"""File I/O processor implementation."""

from __future__ import annotations
from pathlib import Path
from typing import List

from src.interfaces.processor import IFileProcessor
from src.models.scanner import NamespaceObject
from src.file_operations import (
    read_namespace_object_lines as _read_namespace_object_lines,
    append_text_lines,
    write_text_lines
)


class FileIOProcessor(IFileProcessor):
    """File I/O processor implementing IFileProcessor interface.
    
    Provides thread-safe file operations for reading and writing
    namespace:object data.
    """
    
    def read_namespace_objects(
        self,
        file_path: Path
    ) -> List[NamespaceObject]:
        """Read namespace:object lines from file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of NamespaceObject instances
        """
        tuples = _read_namespace_object_lines(file_path)
        return [
            NamespaceObject(namespace=ns, object_id=obj_id)
            for ns, obj_id in tuples
        ]
    
    def write_namespace_objects(
        self,
        file_path: Path,
        objects: List[NamespaceObject]
    ) -> None:
        """Write namespace:object lines to file.
        
        Args:
            file_path: Path to the file to write
            objects: List of NamespaceObject instances
        """
        entries = [obj.to_string() for obj in objects]
        sorted_entries = sorted(set(entries))
        lines = [entry + "\n" for entry in sorted_entries]
        write_text_lines(file_path, lines)
    
    def append_lines(self, file_path: Path, lines: List[str]) -> None:
        """Thread-safely append lines to a file.
        
        Args:
            file_path: Path to the file
            lines: List of strings to append (should include newlines)
        """
        append_text_lines(file_path, lines)
    
    def write_lines(self, file_path: Path, lines: List[str]) -> None:
        """Write lines to a file (overwrites existing content).
        
        Args:
            file_path: Path to the file
            lines: List of strings to write (should include newlines)
        """
        write_text_lines(file_path, lines)
