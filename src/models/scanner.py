"""Models for scanner operations."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class NamespaceObject:
    """Represents a namespace:object identifier.
    
    This is the fundamental data structure for representing
    Minecraft identifiers in the format namespace:object_id.
    """
    namespace: str
    object_id: str
    
    def to_string(self) -> str:
        """Convert to namespace:object_id string.
        
        Returns:
            String in format "namespace:object_id"
        """
        return f"{self.namespace}:{self.object_id}"
    
    @classmethod
    def from_string(cls, s: str) -> Optional[NamespaceObject]:
        """Parse from namespace:object_id string.
        
        Args:
            s: String in format "namespace:object_id"
            
        Returns:
            NamespaceObject instance, or None if invalid format
        """
        if ":" not in s:
            return None
        parts = s.split(":", 1)
        return cls(namespace=parts[0].strip(), object_id=parts[1].strip())


@dataclass
class ScannerResult:
    """Result from scanning a JAR file.
    
    Represents the objects found in a JAR file, grouped by namespace.
    """
    namespace: str
    objects: List[str]  # Object IDs
    source_jar: Path
    timestamp: datetime
    
    def to_namespace_objects(self) -> List[NamespaceObject]:
        """Convert to list of NamespaceObject.
        
        Returns:
            List of NamespaceObject instances
        """
        return [
            NamespaceObject(namespace=self.namespace, object_id=obj_id)
            for obj_id in self.objects
        ]


@dataclass
class ScannerConfig:
    """Configuration for scanner execution.
    
    Contains all parameters needed to run a scanner operation.
    """
    input_dir: Path
    output_dir: Path
    raw_dir: Path
    category: str
    category_suffix: str
    max_workers: int
    namespace_filter: Optional[str] = None
    skip_raw: bool = False
    verbose: bool = False
