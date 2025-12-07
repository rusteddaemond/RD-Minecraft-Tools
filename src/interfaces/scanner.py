"""Interfaces for scanner operations."""

from __future__ import annotations
from typing import Protocol, Optional, List
from pathlib import Path

from src.models.scanner import ScannerResult, ScannerConfig


class IEntryFilter(Protocol):
    """Interface for filtering ZIP entries.
    
    Implementations should check if a ZIP entry path matches
    the criteria and return the object ID if it does.
    """
    
    def filter(self, path_parts: List[str]) -> Optional[str]:
        """Filter entry and return object ID if matches, None otherwise.
        
        Args:
            path_parts: Path components split by '/'
            
        Returns:
            Object ID (stem) if entry matches, None otherwise
        """
        ...


class IScannerProcessor(Protocol):
    """Interface for scanner processors.
    
    Implementations should process JAR files and extract
    relevant information based on the scanner type.
    """
    
    def process_jar(
        self,
        jar_path: Path,
        config: ScannerConfig
    ) -> List[ScannerResult]:
        """Process a JAR file and return scanner results.
        
        Args:
            jar_path: Path to the JAR file
            config: Scanner configuration
            
        Returns:
            List of scanner results grouped by namespace
        """
        ...
    
    def clean_results(
        self,
        raw_results: List[ScannerResult]
    ) -> List[ScannerResult]:
        """Clean and normalize scanner results.
        
        Args:
            raw_results: Raw scanner results
            
        Returns:
            Cleaned scanner results
        """
        ...
