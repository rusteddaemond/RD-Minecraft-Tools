"""Configuration loading utilities for all processors.

See config/README.md for path configuration documentation.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Callable, Tuple, Optional
from dataclasses import dataclass

from src.utils import log, get_project_root
from src.file_operations import read_json_file, find_txt_files as _find_txt_files


@dataclass
class StandardPaths:
    """Standard directory paths for all processors.
    
    Attributes:
        input: Directory containing configuration files (.txt files)
        output: Directory for cleaned/processed output files
        logs: Directory for raw/log files
        mods: Directory containing JAR files for scanning
    """
    input: Path
    output: Path
    logs: Path
    mods: Path
    
    def get_output_category(self, category: str) -> Path:
        """Get output directory for a specific category.
        
        Args:
            category: Category name (e.g., 'blocks', 'items', 'recipes')
            
        Returns:
            Path to output/{category}
        """
        return self.output / category
    
    def get_logs_category(self, category: str) -> Path:
        """Get logs directory for a specific category.
        
        Args:
            category: Category name (e.g., 'blocks', 'items', 'recipes')
            
        Returns:
            Path to logs/{category}
        """
        return self.logs / category


def get_default_paths() -> StandardPaths:
    """Get default standard paths based on project root.
    
    Default paths:
    - input: /input (absolute) or project_root / "input"
    - output: project_root / "output"
    - logs: project_root / "logs"
    - mods: project_root / "mods"
    
    Returns:
        StandardPaths with default values
    """
    project_root = get_project_root()
    
    # Check if /input exists as absolute path (for Docker/container usage)
    input_path = Path("/input")
    if not input_path.exists():
        input_path = project_root / "input"
    
    return StandardPaths(
        input=input_path,
        output=project_root / "output",
        logs=project_root / "logs",
        mods=project_root / "mods"
    )


def load_paths_from_config(config_file: Optional[Path] = None) -> StandardPaths:
    """Load standard paths from configuration file or use defaults.
    
    See config/README.md for configuration file format.
    
    Args:
        config_file: Optional path to configuration file (JSON format)
                    If None, uses default paths
        
    Returns:
        StandardPaths loaded from config or defaults
        
    Raises:
        SystemExit: If config file exists but is invalid
    """
    if config_file is None:
        return get_default_paths()
    
    if not config_file.exists():
        log(f"Config file not found: {config_file}, using defaults", "WARN")
        return get_default_paths()
    
    try:
        config_data = read_json_file(config_file)
    except json.JSONDecodeError as e:
        log(f"Invalid JSON in configuration file: {e}", "ERROR")
        sys.exit(1)
    except Exception as e:
        log(f"Error reading configuration file: {e}", "ERROR")
        sys.exit(1)
    
    project_root = get_project_root()
    
    # Load paths from config, with fallback to defaults
    default_paths = get_default_paths()
    
    def resolve_path(path_str: Optional[str], default: Path) -> Path:
        """Resolve a path string to a Path object.
        
        If path is absolute (starts with /), use as-is.
        Otherwise, resolve relative to project root.
        """
        if path_str is None:
            return default
        
        path = Path(path_str)
        if path.is_absolute():
            return path
        else:
            return project_root / path
    
    paths = StandardPaths(
        input=resolve_path(config_data.get("input"), default_paths.input),
        output=resolve_path(config_data.get("output"), default_paths.output),
        logs=resolve_path(config_data.get("logs"), default_paths.logs),
        mods=resolve_path(config_data.get("mods"), default_paths.mods)
    )
    
    log(f"Loaded paths from config: {config_file}", "OK")
    log(f"  Input: {paths.input}", "INFO")
    log(f"  Output: {paths.output}", "INFO")
    log(f"  Logs: {paths.logs}", "INFO")
    log(f"  Mods: {paths.mods}", "INFO")
    
    return paths


# Legacy functions for backward compatibility with existing config_loader usage
def find_txt_files(directory: Path) -> List[Path]:
    """Find all .txt files in a directory (recursive).
    
    Args:
        directory: Directory to search
        
    Returns:
        List of .txt file paths
    """
    return _find_txt_files(directory, recursive=True)


def load_json_from_txt(config_file: Path) -> Any:
    """Load JSON from .txt file with error handling.
    
    Note: .txt files contain JSON configuration data.
    
    Args:
        config_file: Path to .txt file containing JSON
        
    Returns:
        Parsed JSON data
        
    Raises:
        SystemExit: If file cannot be read or is invalid JSON
    """
    try:
        return read_json_file(config_file)
    except FileNotFoundError:
        log(f"Configuration file not found: {config_file}", "ERROR")
        sys.exit(1)
    except json.JSONDecodeError as e:
        log(f"Invalid JSON in configuration file: {e}", "ERROR")
        sys.exit(1)
    except Exception as e:
        log(f"Error reading configuration file: {e}", "ERROR")
        sys.exit(1)


def load_configs_from_directory(
    input_dir: Path,
    validate_func: Callable[[List[Dict[str, Any]]], Tuple[bool, str]],
    load_func: Callable[[Path], List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """Load and combine configurations from .txt files in directory.
    
    Args:
        input_dir: Directory containing .txt configuration files
        validate_func: Function to validate configuration
        load_func: Function to load and validate a single config file
        
    Returns:
        Combined configuration list from all files
        
    Raises:
        SystemExit: If directory doesn't exist or no files found
    """
    if not input_dir.exists():
        log(f"Input directory does not exist: {input_dir}", "ERROR")
        sys.exit(1)
    
    if not input_dir.is_dir():
        log(f"Input path is not a directory: {input_dir}", "ERROR")
        sys.exit(1)
    
    txt_files = find_txt_files(input_dir)
    if not txt_files:
        log(f"No .txt files found in {input_dir}", "ERROR")
        sys.exit(1)
    
    log(f"Found {len(txt_files)} .txt file(s) in {input_dir}", "OK")
    
    all_config: List[Dict[str, Any]] = []
    
    for txt_file in txt_files:
        try:
            log(f"Loading {txt_file.name}...")
            config = load_func(txt_file)
            all_config.extend(config)
            log(f"Loaded {len(config)} rule(s) from {txt_file.name}", "OK")
        except SystemExit:
            # load_func already logged the error and exited
            raise
        except Exception as e:
            log(f"Error processing {txt_file.name}: {e}", "WARN")
            continue
    
    return all_config
