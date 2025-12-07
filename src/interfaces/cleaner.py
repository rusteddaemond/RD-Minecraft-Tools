"""Interfaces for cleaning operations."""

from __future__ import annotations
from typing import Protocol, Optional
from src.models.scanner import NamespaceObject


class IIdentifierCleaner(Protocol):
    """Interface for identifier cleaning.
    
    Implementations should clean identifiers by removing
    file extensions and affixes.
    """
    
    def clean(self, identifier: str) -> str:
        """Clean an identifier by removing extensions and affixes.
        
        Args:
            identifier: The identifier to clean
            
        Returns:
            Cleaned identifier
        """
        ...
    
    def clean_namespace_object(
        self,
        namespace: str,
        object_id: str
    ) -> Optional[NamespaceObject]:
        """Clean a namespace:object pair.
        
        Args:
            namespace: The namespace
            object_id: The object ID to clean
            
        Returns:
            NamespaceObject with cleaned object_id, or None if invalid
        """
        ...
