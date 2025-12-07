"""JAR file reader processor implementation."""

from __future__ import annotations
import zipfile
from pathlib import Path
from typing import List, Tuple, Optional

from src.interfaces.processor import IJarProcessor
from src.models.jar import JarEntry, JarMetadata
from src.file_operations import find_jar_files as _find_jar_files
from src.config_loader import StandardPaths, get_default_paths
from src.utils.config import create_directory_with_fallback


class JarReader(IJarProcessor):
    """JAR file reader and validator.
    
    Implements IJarProcessor interface for reading and validating JAR files.
    """
    
    def read_entries(self, jar_path: Path) -> List[JarEntry]:
        """Read all entries from a JAR file.
        
        Args:
            jar_path: Path to the JAR file
            
        Returns:
            List of JAR entries
        """
        entries: List[JarEntry] = []
        
        try:
            with zipfile.ZipFile(jar_path, "r") as zf:
                for name in zf.namelist():
                    is_directory = name.endswith("/")
                    
                    # Extract namespace and category from path
                    parts = name.split("/")
                    namespace = None
                    category = None
                    
                    if len(parts) >= 2:
                        if parts[0] == "assets" and len(parts) >= 2:
                            namespace = parts[1]
                            if len(parts) >= 3:
                                category = parts[2]
                        elif parts[0] == "data" and len(parts) >= 2:
                            namespace = parts[1]
                            if len(parts) >= 3:
                                category = parts[2]
                    
                    entries.append(
                        JarEntry(
                            path=name,
                            namespace=namespace,
                            category=category,
                            is_directory=is_directory
                        )
                    )
        except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError):
            pass
        
        return entries
    
    def validate(self, jar_path: Path) -> bool:
        """Validate that a file is a valid JAR.
        
        Args:
            jar_path: Path to the file to validate
            
        Returns:
            True if file is a valid JAR, False otherwise
        """
        try:
            with zipfile.ZipFile(jar_path, "r") as zf:
                # Try to read the file list to ensure it's valid
                _ = zf.namelist()
            return True
        except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError):
            return False
    
    def find_jars(self, directory: Path) -> List[Path]:
        """Find all JAR files in a directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of paths to JAR files
        """
        return _find_jar_files(directory)
    
    def create_output_dirs(
        self,
        category: str,
        paths: Optional[StandardPaths] = None
    ) -> Tuple[Path, Path]:
        """Create raw (logs) and cleaned (output) directories for a category.
        
        Args:
            category: Category name (e.g., 'blocks', 'items', 'recipes', 'fluids')
            paths: Optional StandardPaths instance. If None, uses default paths.
            
        Returns:
            Tuple of (raw_dir, cleaned_dir)
        """
        if paths is None:
            paths = get_default_paths()
        
        raw_dir = create_directory_with_fallback(
            paths.logs,
            [category],
            fallback_prefix="jar_scan_"
        )
        
        cleaned_dir = create_directory_with_fallback(
            paths.output,
            [category],
            fallback_prefix="jar_scan_"
        )
        
        return raw_dir, cleaned_dir


class JarValidator:
    """JAR file validator utility."""
    
    @staticmethod
    def validate(jar_path: Path) -> bool:
        """Validate that a file is a valid JAR.
        
        Args:
            jar_path: Path to the file to validate
            
        Returns:
            True if file is a valid JAR, False otherwise
        """
        try:
            with zipfile.ZipFile(jar_path, "r") as zf:
                _ = zf.namelist()
            return True
        except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError):
            return False
    
    @staticmethod
    def validate_input_directory(input_dir: Path) -> None:
        """Validate input directory exists and is a directory.
        
        Args:
            input_dir: Path to validate
            
        Raises:
            ValueError: If directory doesn't exist or is not a directory
        """
        if not input_dir.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")
        
        if not input_dir.is_dir():
            raise ValueError(f"Input path is not a directory: {input_dir}")
