"""Identifier cleaner processor implementation."""

from __future__ import annotations
from typing import Optional, Tuple

from src.interfaces.cleaner import IIdentifierCleaner
from src.models.scanner import NamespaceObject
from src.affix_cleaner import AFFIXES, DEFAULT_EXTENSIONS, FLUID_EXTENSIONS


class IdentifierCleaner(IIdentifierCleaner):
    """Convergence-based identifier cleaner.
    
    Removes file extensions and affixes until convergence (no more changes).
    """
    
    def __init__(
        self,
        extensions: Tuple[str, ...] = DEFAULT_EXTENSIONS,
        max_iterations: int = 100
    ):
        """Initialize identifier cleaner.
        
        Args:
            extensions: Tuple of file extensions to remove
            max_iterations: Maximum iterations to prevent infinite loops
        """
        self.extensions = extensions
        self.max_iterations = max_iterations
    
    def clean(self, identifier: str) -> str:
        """Clean an identifier by removing extensions and affixes.
        
        Args:
            identifier: The identifier to clean
            
        Returns:
            Cleaned identifier
        """
        previous = identifier
        iterations = 0
        
        while iterations < self.max_iterations:
            # Remove extensions
            for ext in self.extensions:
                if identifier.endswith(ext):
                    identifier = identifier[:-len(ext)]
            
            # Remove affixes
            for affix in AFFIXES:
                if identifier.endswith(affix):
                    identifier = identifier[:-len(affix)]
            
            # Check for convergence
            if identifier == previous:
                break
            
            previous = identifier
            iterations += 1
        
        return identifier
    
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
        cleaned_id = self.clean(object_id)
        if not cleaned_id:
            return None
        
        return NamespaceObject(namespace=namespace, object_id=cleaned_id)


class FluidIdentifierCleaner(IdentifierCleaner):
    """Identifier cleaner for fluid assets (includes .json extension)."""
    
    def __init__(self, max_iterations: int = 100):
        """Initialize fluid identifier cleaner.
        
        Args:
            max_iterations: Maximum iterations to prevent infinite loops
        """
        super().__init__(extensions=FLUID_EXTENSIONS, max_iterations=max_iterations)
