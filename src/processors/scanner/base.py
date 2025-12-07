"""Base scanner processor implementation."""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional
import zipfile
from collections import defaultdict
from datetime import datetime

from src.interfaces.scanner import IEntryFilter, IScannerProcessor
from src.models.scanner import ScannerResult, ScannerConfig
from src.utils.logging import log


class BaseScannerProcessor(IScannerProcessor):
    """Base implementation for scanner processors.
    
    This processor handles the common logic of reading JAR files,
    filtering entries, and extracting namespace:object pairs.
    """
    
    def __init__(self, entry_filter: IEntryFilter):
        """Initialize with entry filter.
        
        Args:
            entry_filter: Filter for ZIP entries
        """
        self.entry_filter = entry_filter
    
    def process_jar(
        self,
        jar_path: Path,
        config: ScannerConfig
    ) -> List[ScannerResult]:
        """Process JAR using entry filter.
        
        Args:
            jar_path: Path to the JAR file
            config: Scanner configuration
            
        Returns:
            List of scanner results grouped by namespace
        """
        results_by_namespace: dict[str, List[str]] = defaultdict(list)
        
        try:
            with zipfile.ZipFile(jar_path, "r") as zf:
                for name in zf.namelist():
                    if name.endswith("/"):
                        continue
                    
                    parts = name.split("/")
                    obj_id = self.entry_filter.filter(parts)
                    
                    if obj_id is None:
                        continue
                    
                    # Extract namespace
                    namespace = self._extract_namespace(parts)
                    if namespace is None:
                        continue
                    
                    # Apply namespace filter
                    if config.namespace_filter:
                        if namespace.lower() != config.namespace_filter.lower():
                            continue
                    
                    results_by_namespace[namespace].append(obj_id)
        
        except zipfile.BadZipFile:
            log(f"Bad zip file: {jar_path.name}", "WARN")
            return []
        except Exception as e:
            log(f"{jar_path.name}: {e}", "ERROR")
            return []
        
        # Convert to ScannerResult objects
        results = [
            ScannerResult(
                namespace=ns,
                objects=objects,
                source_jar=jar_path,
                timestamp=datetime.now()
            )
            for ns, objects in results_by_namespace.items()
        ]
        
        return results
    
    def _extract_namespace(self, parts: List[str]) -> Optional[str]:
        """Extract namespace from path parts.
        
        Args:
            parts: Path components split by '/'
            
        Returns:
            Namespace if found, None otherwise
        """
        if len(parts) >= 2:
            if parts[0] == "assets" and len(parts) >= 2:
                return parts[1]
            elif parts[0] == "data" and len(parts) >= 2:
                return parts[1]
        return None
    
    def clean_results(
        self,
        raw_results: List[ScannerResult]
    ) -> List[ScannerResult]:
        """Clean results (to be implemented by subclasses or injected cleaner).
        
        Args:
            raw_results: Raw scanner results
            
        Returns:
            Cleaned scanner results (default: no cleaning)
        """
        # Default: no cleaning
        return raw_results
