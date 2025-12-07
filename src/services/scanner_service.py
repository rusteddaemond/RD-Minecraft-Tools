"""High-level service for scanner operations."""

from __future__ import annotations
from pathlib import Path
from typing import List

from src.interfaces.scanner import IScannerProcessor
from src.interfaces.processor import IFileProcessor
from src.interfaces.cleaner import IIdentifierCleaner
from src.models.scanner import ScannerConfig, ScannerResult
from src.processors.jar.reader import JarReader, JarValidator
from src.utils.threading import execute_concurrent
from src.utils.logging import log


class ScannerService:
    """High-level service for scanner operations.
    
    Orchestrates scanner processors, file I/O, and cleaning to provide
    a complete scanner workflow.
    """
    
    def __init__(
        self,
        processor: IScannerProcessor,
        file_io: IFileProcessor,
        cleaner: IIdentifierCleaner | None = None
    ):
        """Initialize scanner service.
        
        Args:
            processor: Scanner processor implementation
            file_io: File I/O processor
            cleaner: Optional identifier cleaner (if None, no cleaning is performed)
        """
        self.processor = processor
        self.file_io = file_io
        self.cleaner = cleaner
        self.jar_reader = JarReader()
        self.jar_validator = JarValidator()
    
    def run_scan(self, config: ScannerConfig) -> None:
        """Run complete scanner workflow.
        
        Args:
            config: Scanner configuration
        """
        # 1. Validate input directory
        try:
            self.jar_validator.validate_input_directory(config.input_dir)
        except ValueError as e:
            log(str(e), "ERROR")
            return
        
        # 2. Find JAR files
        try:
            jars = self.jar_reader.find_jars(config.input_dir)
        except ValueError as e:
            log(str(e), "ERROR")
            return
        
        if not jars:
            log("No JAR files found", "ERROR")
            return
        
        log(f"Found {len(jars)} JAR(s). Scanning with {config.max_workers} threads...")
        
        # 3. Process JARs (concurrent)
        all_results: List[ScannerResult] = []
        
        def process_wrapper(jar_path: Path) -> None:
            """Wrapper for concurrent processing."""
            results = self.processor.process_jar(jar_path, config)
            all_results.extend(results)
            
            # Write raw results immediately
            for result in results:
                self._write_raw_result(result, config)
        
        execute_concurrent(
            jars,
            process_wrapper,
            max_workers=config.max_workers,
            verbose=config.verbose
        )
        
        # 4. Clean results
        log("Starting thorough cleaning of gathered results...")
        cleaned_results = self._clean_all_results(all_results)
        
        # 5. Write cleaned results
        for result in cleaned_results:
            self._write_cleaned_result(result, config)
        
        # 6. Optionally delete raw files
        if config.skip_raw:
            self._delete_raw_files(config)
        
        log(f"Completed. Clean files in:\n  {config.output_dir.resolve()}")
        log(f"Raw files in:\n  {config.raw_dir.resolve()}")
    
    def _write_raw_result(self, result: ScannerResult, config: ScannerConfig) -> None:
        """Write raw scanner result to file.
        
        Args:
            result: Scanner result to write
            config: Scanner configuration
        """
        raw_file = config.raw_dir / f"{result.namespace}{config.category_suffix}_raw.txt"
        lines = [f"{result.namespace}:{obj_id}\n" for obj_id in result.objects]
        self.file_io.append_lines(raw_file, lines)
    
    def _write_cleaned_result(self, result: ScannerResult, config: ScannerConfig) -> None:
        """Write cleaned scanner result to file.
        
        Args:
            result: Scanner result to write
            config: Scanner configuration
        """
        cleaned_file = config.output_dir / f"{result.namespace}{config.category_suffix}.txt"
        
        if self.cleaner:
            # Clean identifiers
            cleaned_objects: List[NamespaceObject] = []
            for obj_id in result.objects:
                cleaned_obj = self.cleaner.clean_namespace_object(result.namespace, obj_id)
                if cleaned_obj:
                    cleaned_objects.append(cleaned_obj)
            
            # Deduplicate and sort
            unique_objects = sorted(set(obj.to_string() for obj in cleaned_objects))
        else:
            # No cleaning, just deduplicate and sort
            unique_objects = sorted(set(f"{result.namespace}:{obj_id}" for obj_id in result.objects))
        
        lines = [obj + "\n" for obj in unique_objects]
        self.file_io.write_lines(cleaned_file, lines)
        log(f"{cleaned_file.name}: {len(unique_objects)} entries", "CLEAN")
    
    def _clean_all_results(self, results: List[ScannerResult]) -> List[ScannerResult]:
        """Clean all results using processor.
        
        Args:
            results: Raw scanner results
            
        Returns:
            Cleaned scanner results
        """
        return self.processor.clean_results(results)
    
    def _delete_raw_files(self, config: ScannerConfig) -> None:
        """Delete raw files after cleaning.
        
        Args:
            config: Scanner configuration
        """
        for raw_file in config.raw_dir.glob(f"*{config.category_suffix}_raw.txt"):
            try:
                raw_file.unlink()
            except Exception as e:
                log(f"Error deleting {raw_file.name}: {e}", "WARN")
