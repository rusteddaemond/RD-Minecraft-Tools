"""Interfaces for matcher operations."""

from __future__ import annotations
from typing import Protocol, List, Dict, Any, Tuple
from pathlib import Path

from src.models.matcher import MatchRule, MatcherConfig, DuplicateMatch


class IMatcherProcessor(Protocol):
    """Interface for matcher processors.
    
    Implementations should find duplicates or process match rules
    to generate datapacks.
    """
    
    def find_duplicates(
        self,
        objects: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """Find duplicate objects across namespaces.
        
        Args:
            objects: Dictionary mapping object_id to list of namespaces
            
        Returns:
            Dictionary with only duplicate objects (appearing in multiple namespaces)
        """
        ...
    
    def generate_datapack(
        self,
        matches: List[MatchRule],
        config: MatcherConfig
    ) -> Path:
        """Generate datapack from match rules.
        
        Args:
            matches: List of match rules
            config: Matcher configuration
            
        Returns:
            Path to the generated replacements file
        """
        ...


class IMatcherValidator(Protocol):
    """Interface for validating matcher configurations.
    
    Implementations should validate configuration data structures
    to ensure they are correct before processing.
    """
    
    def validate(
        self,
        config: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """Validate configuration and return (is_valid, error_message).
        
        Args:
            config: Configuration list to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
            If is_valid is True, error_message should be empty string
        """
        ...
