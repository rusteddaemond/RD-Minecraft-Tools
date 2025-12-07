"""Asset scanner processor for blocks, items, and fluids."""

from __future__ import annotations
from typing import List

from src.interfaces.scanner import IEntryFilter
from src.interfaces.cleaner import IIdentifierCleaner
from src.models.scanner import ScannerResult, ScannerConfig
from src.processors.scanner.base import BaseScannerProcessor
from src.utils.logging import log


class AssetScannerProcessor(BaseScannerProcessor):
    """Processor for asset scanners (blocks, items, fluids).
    
    This processor extends BaseScannerProcessor with cleaning capabilities
    for asset identifiers.
    """
    
    def __init__(
        self,
        entry_filter: IEntryFilter,
        cleaner: IIdentifierCleaner | None = None
    ):
        """Initialize asset scanner processor.
        
        Args:
            entry_filter: Filter for ZIP entries
            cleaner: Optional identifier cleaner (if None, no cleaning is performed)
        """
        super().__init__(entry_filter)
        self.cleaner = cleaner
    
    def clean_results(
        self,
        raw_results: List[ScannerResult]
    ) -> List[ScannerResult]:
        """Clean results using identifier cleaner if available.
        
        Args:
            raw_results: Raw scanner results
            
        Returns:
            Cleaned scanner results
        """
        if self.cleaner is None:
            return raw_results
        
        cleaned_results: List[ScannerResult] = []
        
        for result in raw_results:
            cleaned_objects: List[str] = []
            for obj_id in result.objects:
                cleaned_obj = self.cleaner.clean(obj_id)
                if cleaned_obj:
                    cleaned_objects.append(cleaned_obj)
            
            # Deduplicate
            unique_objects = sorted(set(cleaned_objects))
            
            if unique_objects:
                cleaned_results.append(
                    ScannerResult(
                        namespace=result.namespace,
                        objects=unique_objects,
                        source_jar=result.source_jar,
                        timestamp=result.timestamp
                    )
                )
        
        return cleaned_results
