"""Duplicate matcher processor implementation."""

from __future__ import annotations
from typing import Dict, List
from pathlib import Path

from src.interfaces.matcher import IMatcherProcessor
from src.interfaces.processor import IFileProcessor
from src.models.matcher import MatchRule, MatcherConfig, DuplicateMatch
from src.models.scanner import NamespaceObject


class DuplicateMatcherProcessor(IMatcherProcessor):
    """Processor for finding duplicate objects across namespaces."""
    
    def __init__(self, file_processor: IFileProcessor):
        """Initialize duplicate matcher processor.
        
        Args:
            file_processor: File processor for reading namespace:object files
        """
        self.file_processor = file_processor
    
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
        return {
            obj_id: ns_list
            for obj_id, ns_list in objects.items()
            if len(set(ns_list)) > 1
        }
    
    def load_objects_from_files(
        self,
        files: List[Path]
    ) -> Dict[str, List[str]]:
        """Load objects from text files and map object_id -> list of namespaces.
        
        Args:
            files: List of text file paths containing namespace:object lines
            
        Returns:
            Dictionary mapping object_id to list of namespaces containing it
        """
        from collections import defaultdict
        
        objects: Dict[str, List[str]] = defaultdict(list)
        for file in files:
            try:
                namespace_objects = self.file_processor.read_namespace_objects(file)
                for ns_obj in namespace_objects:
                    objects[ns_obj.object_id].append(ns_obj.namespace)
            except Exception as e:
                from src.utils.logging import log
                log(f"Error reading {file}: {e}", "ERROR")
        return objects
    
    def build_match_rules(
        self,
        duplicates: Dict[str, List[str]],
        result_ns: str,
        match_field: str,
        result_field: str
    ) -> List[MatchRule]:
        """Build match rules from duplicates.
        
        Args:
            duplicates: Dictionary of duplicate objects
            result_ns: Target namespace for results
            match_field: Field name for match list
            result_field: Field name for result
            
        Returns:
            List of match rules
        """
        from collections import defaultdict
        
        grouped: Dict[str, List[str]] = defaultdict(list)
        
        for obj_id, ns_list in duplicates.items():
            if result_ns not in ns_list:
                continue
            
            result_obj = f"{result_ns}:{obj_id}"
            
            # Add all non-result namespace objects to match list
            for ns in ns_list:
                if ns != result_ns:
                    grouped[result_obj].append(f"{ns}:{obj_id}")
        
        # Convert to match rules
        match_rules: List[MatchRule] = []
        for result_obj, match_objs in sorted(grouped.items()):
            match_rules.append(
                MatchRule(
                    match_items=sorted(match_objs),
                    result_item=result_obj,
                    match_field=match_field,
                    result_field=result_field
                )
            )
        
        return match_rules
    
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
        from src.processors.datapack.generator import DatapackGenerator
        
        generator = DatapackGenerator()
        replacement_rules = [
            rule.to_dict() for rule in matches
        ]
        
        return generator.generate_from_dicts(replacement_rules, config)
