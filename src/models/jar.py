"""Models for JAR file operations."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class JarEntry:
    """Represents an entry in a JAR file.
    
    A JAR file is a ZIP archive, and this represents a single
    entry (file or directory) within that archive.
    """
    path: str
    namespace: Optional[str] = None
    category: Optional[str] = None
    is_directory: bool = False
    
    def get_path_parts(self) -> list[str]:
        """Get path components split by '/'.
        
        Returns:
            List of path components
        """
        return self.path.split("/")


@dataclass
class JarMetadata:
    """Metadata about a JAR file.
    
    Contains information about a JAR file without needing
    to open and read its contents.
    """
    path: Path
    size: int
    mod_count: int = 0
    is_valid: bool = True
