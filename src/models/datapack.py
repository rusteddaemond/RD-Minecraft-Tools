"""Models for datapack generation."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class DatapackMetadata:
    """Metadata for a Minecraft datapack.
    
    Represents the pack.mcmeta file contents.
    """
    pack_format: int
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary in pack.mcmeta format
        """
        return {
            "pack": {
                "pack_format": self.pack_format,
                "description": self.description
            }
        }


@dataclass
class ReplacementRule:
    """A replacement rule in datapack format.
    
    Represents a single replacement rule that can be serialized
    to the replacements.json file in a datapack.
    """
    match_field: str
    result_field: str
    match_values: List[str]
    result_value: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary in replacements.json format
        """
        return {
            self.match_field: self.match_values,
            self.result_field: self.result_value
        }
