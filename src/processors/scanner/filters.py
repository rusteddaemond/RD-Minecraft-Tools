"""Entry filter implementations for different scanner types."""

from __future__ import annotations
from typing import Optional, List
from pathlib import Path

from src.interfaces.scanner import IEntryFilter


class BlockEntryFilter(IEntryFilter):
    """Filter for block assets (models/block, textures/block)."""
    
    def filter(self, path_parts: List[str]) -> Optional[str]:
        """Filter ZIP entries for block assets.
        
        Args:
            path_parts: Path components split by '/'
            
        Returns:
            Object ID (stem) if entry is a block asset, None otherwise
        """
        if len(path_parts) < 4 or path_parts[0] != "assets":
            return None
        
        category = path_parts[2:4]
        
        # Only process block assets
        if category in (["models", "block"], ["textures", "block"]):
            return Path("/".join(path_parts)).stem
        
        return None


class ItemsEntryFilter(IEntryFilter):
    """Filter for item assets (models/item, textures/item)."""
    
    def filter(self, path_parts: List[str]) -> Optional[str]:
        """Filter ZIP entries for item assets.
        
        Args:
            path_parts: Path components split by '/'
            
        Returns:
            Object ID (stem) if entry is an item asset, None otherwise
        """
        if len(path_parts) < 4 or path_parts[0] != "assets":
            return None
        
        category = path_parts[2:4]
        
        # Only process item assets
        if category in (["models", "item"], ["textures", "item"]):
            return Path("/".join(path_parts)).stem
        
        return None


class FluidEntryFilter(IEntryFilter):
    """Filter for fluid assets (fluid/, fluid_types/)."""
    
    def filter(self, path_parts: List[str]) -> Optional[str]:
        """Filter ZIP entries for fluid assets.
        
        Args:
            path_parts: Path components split by '/'
            
        Returns:
            Object ID (stem) if entry is a fluid asset, None otherwise
        """
        if len(path_parts) < 3 or path_parts[0] != "assets":
            return None
        
        # Check for fluid/ or fluid_types/ directories
        if len(path_parts) >= 3:
            if path_parts[2] in ("fluid", "fluid_types"):
                return Path("/".join(path_parts)).stem
        
        return None
