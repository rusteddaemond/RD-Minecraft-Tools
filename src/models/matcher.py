"""Models for matcher operations."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any


@dataclass
class MatchRule:
    """A single match rule for datapack generation.
    
    Represents a rule that matches multiple items/fluids/blocks
    and replaces them with a single result.
    """
    match_items: List[str]
    result_item: str
    match_field: str
    result_field: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary in datapack format
        """
        return {
            self.match_field: self.match_items,
            self.result_field: self.result_item
        }


@dataclass
class MatcherConfig:
    """Configuration for matcher execution.
    
    Contains all parameters needed to run a matcher operation.
    """
    input_dir: Path
    output_dir: Path
    datapack_path: str
    match_field: str
    result_field: str
    description: str
    pack_format: int = 10
    filename: str = "replacements.json"


@dataclass
class DuplicateMatch:
    """Represents a duplicate object across namespaces.
    
    Used when finding duplicate objects that appear in multiple
    namespaces (e.g., same block ID in different mods).
    """
    object_id: str
    namespaces: List[str]
    
    def has_duplicates(self) -> bool:
        """Check if this object appears in multiple namespaces.
        
        Returns:
            True if object appears in more than one namespace
        """
        return len(set(self.namespaces)) > 1
