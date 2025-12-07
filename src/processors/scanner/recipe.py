"""Recipe scanner processor implementation."""

from __future__ import annotations
import json
import zipfile
from pathlib import Path
from typing import List, Set
from collections import defaultdict
from datetime import datetime

from src.interfaces.scanner import IScannerProcessor
from src.models.scanner import ScannerResult, ScannerConfig
from src.models.recipe import RecipeResult
from src.utils.logging import log


class RecipeScannerProcessor(IScannerProcessor):
    """Processor for scanning recipe JSON files in JAR files."""
    
    def __init__(self, include_minecraft: bool = False):
        """Initialize recipe scanner processor.
        
        Args:
            include_minecraft: If True, include minecraft: recipes (default: False)
        """
        self.include_minecraft = include_minecraft
    
    def process_jar(
        self,
        jar_path: Path,
        config: ScannerConfig
    ) -> List[ScannerResult]:
        """Process a JAR file and extract recipe results.
        
        Args:
            jar_path: Path to the JAR file
            config: Scanner configuration
            
        Returns:
            List of scanner results grouped by namespace
        """
        per_namespace: dict[str, Set[str]] = defaultdict(set)
        
        try:
            with zipfile.ZipFile(jar_path, "r") as zf:
                for name in zf.namelist():
                    parts = name.split("/")
                    if len(parts) < 4 or parts[0] != "data":
                        continue
                    
                    ns = parts[1]
                    
                    # Apply namespace filter if specified
                    if config.namespace_filter:
                        if ns.lower() != config.namespace_filter.lower():
                            continue
                    
                    if not parts[2].startswith("recipe") or not name.endswith(".json"):
                        continue
                    
                    try:
                        with zf.open(name) as f:
                            content = f.read().decode("utf-8", errors="ignore")
                        
                        for rid in self._extract_results_from_json(content):
                            rid = rid.strip()
                            if rid:
                                # Filter minecraft: recipes unless included
                                if not self.include_minecraft and rid.startswith("minecraft:"):
                                    continue
                                per_namespace[ns].add(rid)
                    except Exception:
                        continue
        
        except zipfile.BadZipFile:
            log(f"Bad zip: {jar_path.name}", "WARN")
            return []
        except Exception as e:
            log(f"{jar_path.name}: {e}", "ERROR")
            return []
        
        # Convert to ScannerResult objects
        results = [
            ScannerResult(
                namespace=ns,
                objects=list(items),
                source_jar=jar_path,
                timestamp=datetime.now()
            )
            for ns, items in per_namespace.items()
        ]
        
        return results
    
    def _extract_results_from_json(self, content: str) -> List[str]:
        """Extract recipe result IDs from JSON content.
        
        Args:
            content: JSON string content
            
        Returns:
            List of recipe result IDs
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return []
        
        results: List[str] = []
        if isinstance(data, dict):
            # Single result
            r = data.get("result")
            if isinstance(r, str):
                results.append(r)
            elif isinstance(r, dict) and isinstance(r.get("id"), str):
                results.append(r["id"])
            # Multiple results
            if isinstance(data.get("results"), list):
                for e in data["results"]:
                    if isinstance(e, dict) and isinstance(e.get("id"), str):
                        results.append(e["id"])
        return results
    
    def clean_results(
        self,
        raw_results: List[ScannerResult]
    ) -> List[ScannerResult]:
        """Clean results (simple deduplication for recipes).
        
        Args:
            raw_results: Raw scanner results
            
        Returns:
            Cleaned scanner results (deduplicated)
        """
        cleaned_results: List[ScannerResult] = []
        
        for result in raw_results:
            # Simple deduplication and sorting
            unique_objects = sorted(set(result.objects))
            
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
