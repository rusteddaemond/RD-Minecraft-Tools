"""Interfaces for processor operations."""

from __future__ import annotations
from typing import Protocol, List
from pathlib import Path

from src.models.jar import JarEntry, JarMetadata
from src.models.scanner import NamespaceObject


class IJarProcessor(Protocol):
    """Interface for JAR file processing.
    
    Implementations should handle reading and validating JAR files.
    """
    
    def read_entries(self, jar_path: Path) -> List[JarEntry]:
        """Read all entries from a JAR file.
        
        Args:
            jar_path: Path to the JAR file
            
        Returns:
            List of JAR entries
        """
        ...
    
    def validate(self, jar_path: Path) -> bool:
        """Validate that a file is a valid JAR.
        
        Args:
            jar_path: Path to the file to validate
            
        Returns:
            True if file is a valid JAR, False otherwise
        """
        ...
    
    def find_jars(self, directory: Path) -> List[Path]:
        """Find all JAR files in a directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of paths to JAR files
        """
        ...


class IFileProcessor(Protocol):
    """Interface for file processing operations.
    
    Implementations should handle reading and writing files
    in various formats.
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
        ...
    
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
        ...
    
    def append_lines(self, file_path: Path, lines: List[str]) -> None:
        """Thread-safely append lines to a file.
        
        Args:
            file_path: Path to the file
            lines: List of strings to append (should include newlines)
        """
        ...
    
    def write_lines(self, file_path: Path, lines: List[str]) -> None:
        """Write lines to a file (overwrites existing content).
        
        Args:
            file_path: Path to the file
            lines: List of strings to write (should include newlines)
        """
        ...
