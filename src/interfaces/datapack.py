"""Interfaces for datapack generation."""

from __future__ import annotations
from typing import Protocol, List
from pathlib import Path

from src.models.datapack import ReplacementRule
from src.models.matcher import MatcherConfig


class IDatapackGenerator(Protocol):
    """Interface for datapack generation.
    
    Implementations should generate complete Minecraft datapacks
    from replacement rules.
    """
    
    def generate(
        self,
        rules: List[ReplacementRule],
        config: MatcherConfig
    ) -> Path:
        """Generate a complete datapack.
        
        Args:
            rules: List of replacement rules
            config: Matcher configuration
            
        Returns:
            Path to the generated replacements file
        """
        ...
    
    def create_structure(
        self,
        output_dir: Path,
        datapack_path: str
    ) -> Path:
        """Create datapack directory structure.
        
        Args:
            output_dir: Base output directory
            datapack_path: Path component for datapack (e.g., 'oei', 'oef')
            
        Returns:
            Path to the replacements directory
        """
        ...
