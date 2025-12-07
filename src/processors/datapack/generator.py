"""Datapack generator processor implementation."""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any

from src.interfaces.datapack import IDatapackGenerator
from src.models.datapack import ReplacementRule, DatapackMetadata
from src.models.matcher import MatcherConfig
from src.file_operations import write_json_file


class DatapackGenerator(IDatapackGenerator):
    """Processor for generating Minecraft datapacks."""
    
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
        replacements_dir = output_dir / "data" / datapack_path / "replacements"
        replacements_dir.mkdir(parents=True, exist_ok=True)
        return replacements_dir
    
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
        # Create structure
        replacements_dir = self.create_structure(config.output_dir, config.datapack_path)
        
        # Convert rules to dictionaries
        replacements = [rule.to_dict() for rule in rules]
        
        # Write replacements file
        output_file = replacements_dir / config.filename
        write_json_file(output_file, replacements, indent=4)
        
        # Create pack.mcmeta
        metadata = DatapackMetadata(
            pack_format=config.pack_format,
            description=config.description
        )
        pack_mcmeta = config.output_dir / "pack.mcmeta"
        write_json_file(pack_mcmeta, metadata.to_dict(), indent=2)
        
        return output_file
    
    def generate_from_dicts(
        self,
        replacements: List[Dict[str, Any]],
        config: MatcherConfig
    ) -> Path:
        """Generate datapack from dictionary format replacements.
        
        Args:
            replacements: List of replacement dictionaries
            config: Matcher configuration
            
        Returns:
            Path to the generated replacements file
        """
        # Create structure
        replacements_dir = self.create_structure(config.output_dir, config.datapack_path)
        
        # Write replacements file
        output_file = replacements_dir / config.filename
        write_json_file(output_file, replacements, indent=4)
        
        # Create pack.mcmeta
        metadata = DatapackMetadata(
            pack_format=config.pack_format,
            description=config.description
        )
        pack_mcmeta = config.output_dir / "pack.mcmeta"
        write_json_file(pack_mcmeta, metadata.to_dict(), indent=2)
        
        return output_file
