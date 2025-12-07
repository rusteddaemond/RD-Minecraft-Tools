"""High-level service for matcher operations."""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Set, Optional

from src.interfaces.matcher import IMatcherProcessor
from src.interfaces.processor import IFileProcessor
from src.models.matcher import MatcherConfig, MatchRule
from src.utils.logging import log
from src.config_loader import find_txt_files


class MatcherService:
    """High-level service for matcher operations.
    
    Orchestrates matcher processors to provide complete matcher workflows
    for both duplicate-based and config-based matchers.
    """
    
    def __init__(
        self,
        processor: IMatcherProcessor,
        file_io: IFileProcessor
    ):
        """Initialize matcher service.
        
        Args:
            processor: Matcher processor implementation
            file_io: File I/O processor
        """
        self.processor = processor
        self.file_io = file_io
    
    def run_duplicate_matcher(
        self,
        config: MatcherConfig,
        result_ns: Optional[str] = None,
        interactive: bool = True
    ) -> Path:
        """Run duplicate-based matcher workflow.
        
        Args:
            config: Matcher configuration
            result_ns: Optional pre-selected namespace (enables non-interactive mode)
            interactive: Whether to prompt for namespace selection
            
        Returns:
            Path to the generated replacements file
        """
        # 1. Validate input directory
        if not config.input_dir.exists():
            log(f"Input directory does not exist: {config.input_dir}", "ERROR")
            raise ValueError(f"Input directory does not exist: {config.input_dir}")
        
        if not config.input_dir.is_dir():
            log(f"Input path is not a directory: {config.input_dir}", "ERROR")
            raise ValueError(f"Input path is not a directory: {config.input_dir}")
        
        log(f"Scanning: {config.input_dir}")
        
        # 2. Find and load text files
        txt_files = find_txt_files(config.input_dir)
        if not txt_files:
            log("No .txt files found", "ERROR")
            raise ValueError("No .txt files found")
        
        log(f"Found {len(txt_files)} text file(s)", "OK")
        
        # 3. Load objects from files
        if hasattr(self.processor, 'load_objects_from_files'):
            # DuplicateMatcherProcessor
            objects = self.processor.load_objects_from_files(txt_files)
        else:
            # Fallback: use file_io directly
            objects: Dict[str, List[str]] = {}
            for file in txt_files:
                namespace_objects = self.file_io.read_namespace_objects(file)
                for ns_obj in namespace_objects:
                    if ns_obj.object_id not in objects:
                        objects[ns_obj.object_id] = []
                    objects[ns_obj.object_id].append(ns_obj.namespace)
        
        # 4. Find duplicates
        duplicates = self.processor.find_duplicates(objects)
        
        if not duplicates:
            log("No cross-namespace duplicates found", "INFO")
            return Path()  # Return empty path
        
        log(f"\nFound {len(duplicates)} duplicate objects:", "INFO")
        for obj_id, ns_list in sorted(duplicates.items())[:10]:  # Show first 10
            unique_ns = sorted(set(ns_list))
            log(f"  {obj_id}: {', '.join(unique_ns)}")
        if len(duplicates) > 10:
            log(f"  ... and {len(duplicates) - 10} more", "INFO")
        
        # 5. Determine result namespace
        all_namespaces = set(ns for ns_list in duplicates.values() for ns in ns_list)
        
        if result_ns:
            if result_ns.lower() not in all_namespaces:
                log(f"Namespace '{result_ns}' not found in duplicates", "ERROR")
                log(f"Available namespaces: {', '.join(sorted(all_namespaces))}", "INFO")
                raise ValueError(f"Namespace '{result_ns}' not found in duplicates")
            selected_ns = result_ns.lower()
        else:
            selected_ns = self._choose_result_namespace(all_namespaces, interactive)
            if not selected_ns:
                log("No namespace selected. Exiting.", "ERROR")
                raise ValueError("No namespace selected")
        
        log(f"\nUsing namespace: {selected_ns}", "INFO")
        
        # 6. Build match rules
        if hasattr(self.processor, 'build_match_rules'):
            # DuplicateMatcherProcessor
            match_rules = self.processor.build_match_rules(
                duplicates,
                selected_ns,
                config.match_field,
                config.result_field
            )
        else:
            # Fallback: build manually
            from collections import defaultdict
            grouped: Dict[str, List[str]] = defaultdict(list)
            
            for obj_id, ns_list in duplicates.items():
                if selected_ns not in ns_list:
                    continue
                
                result_obj = f"{selected_ns}:{obj_id}"
                for ns in ns_list:
                    if ns != selected_ns:
                        grouped[result_obj].append(f"{ns}:{obj_id}")
            
            match_rules = [
                MatchRule(
                    match_items=sorted(match_objs),
                    result_item=result_obj,
                    match_field=config.match_field,
                    result_field=config.result_field
                )
                for result_obj, match_objs in sorted(grouped.items())
            ]
        
        # 7. Set filename based on selected namespace
        # Output file is named after the target namespace (e.g., "farm_and_charm.json")
        from src.models.matcher import MatcherConfig
        config_with_filename = MatcherConfig(
            input_dir=config.input_dir,
            output_dir=config.output_dir,
            datapack_path=config.datapack_path,
            match_field=config.match_field,
            result_field=config.result_field,
            description=config.description,
            pack_format=config.pack_format,
            filename=f"{selected_ns}.json"
        )
        
        # 8. Generate datapack
        output_file = self.processor.generate_datapack(match_rules, config_with_filename)
        
        log(f"\nWrote datapack to {output_file}", "OK")
        log(f"Datapack generated at: {config.output_dir.resolve()}", "INFO")
        
        return output_file
    
    def run_config_matcher(
        self,
        config: MatcherConfig,
        config_file: Optional[Path] = None
    ) -> Path:
        """Run config-based matcher workflow.
        
        Args:
            config: Matcher configuration
            config_file: Optional single config file (if None, loads from input_dir)
            
        Returns:
            Path to the generated replacements file
        """
        # 1. Load configuration
        if hasattr(self.processor, 'load_config_from_file') and config_file:
            # Load from single file
            config_data = self.processor.load_config_from_file(config_file)
        elif hasattr(self.processor, 'load_configs_from_directory'):
            # Load from directory
            config_data = self.processor.load_configs_from_directory(config.input_dir)
        else:
            raise ValueError("Processor does not support config loading")
        
        # 2. Convert to match rules
        match_rules = [
            MatchRule(
                match_items=entry[config.match_field],
                result_item=entry[config.result_field],
                match_field=config.match_field,
                result_field=config.result_field
            )
            for entry in config_data
        ]
        
        # 3. Generate datapack
        output_file = self.processor.generate_datapack(match_rules, config)
        
        log(f"\nWrote datapack to {output_file}", "OK")
        log(f"Datapack generated at: {config.output_dir.resolve()}", "INFO")
        
        return output_file
    
    def _choose_result_namespace(
        self,
        namespaces: Set[str],
        interactive: bool = True
    ) -> Optional[str]:
        """Prompt user to select the target namespace.
        
        Args:
            namespaces: Set of available namespaces
            interactive: Whether to prompt interactively
            
        Returns:
            Selected namespace, or None if not interactive and no default
        """
        ns_list = sorted(namespaces)
        
        if not interactive:
            return ns_list[0] if ns_list else None
        
        log("\nChoose RESULT namespace:", "INFO")
        for idx, ns in enumerate(ns_list, 1):
            log(f"{idx}) {ns}")
        
        while True:
            try:
                choice = int(input("Enter number: "))
                if 1 <= choice <= len(ns_list):
                    return ns_list[choice - 1]
                log("Invalid number", "WARN")
            except ValueError:
                log("Must enter a number", "WARN")
            except (EOFError, KeyboardInterrupt):
                log("\nCancelled.", "INFO")
                return None
