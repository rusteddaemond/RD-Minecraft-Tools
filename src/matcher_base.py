"""Base class for matcher tools.

**DEPRECATED**: This module is deprecated in favor of the new architecture.
New code should use:
- `src.processors.matcher.ConfigMatcherProcessor` for config-based matchers
- `src.processors.matcher.DuplicateMatcherProcessor` for duplicate-based matchers
- `src.models.matcher.*` for data models

This module is kept for backward compatibility with legacy tools.

This module provides a base class that eliminates code duplication between
fluid_matcher, items_matcher, and potentially other matcher tools.
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

from src.utils import log
from src.config_loader import find_txt_files, load_json_from_txt, load_configs_from_directory
from src.datapack_generator import (
    create_datapack_structure,
    generate_replacements_file,
    create_pack_mcmeta
)


class MatcherBase:
    """Base class for matcher tools.
    
    This class provides common functionality for matcher tools that generate
    Minecraft datapacks from configuration files.
    """
    
    def __init__(
        self,
        mod_name: str,
        match_field: str,
        result_field: str,
        datapack_path: str,
        description: str
    ):
        """Initialize matcher base.
        
        Args:
            mod_name: Mod name (e.g., 'oei', 'oef', 'oeb')
            match_field: Field name for match items/fluids (e.g., 'matchItems', 'matchFluid')
            result_field: Field name for result item/fluid (e.g., 'resultItems', 'resultFluid')
            datapack_path: Path component for datapack (e.g., 'oei', 'oef', 'oeb')
            description: Description for the datapack
        """
        self.mod_name = mod_name
        self.match_field = match_field
        self.result_field = result_field
        self.datapack_path = datapack_path
        self.description = description
    
    def validate_config(self, config: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Validate configuration data.
        
        Args:
            config: Configuration list with match and result fields
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(config, list):
            return False, "Configuration must be a list"
        
        for idx, entry in enumerate(config):
            if not isinstance(entry, dict):
                return False, f"Entry {idx} must be a dictionary"
            
            if self.match_field not in entry:
                return False, f"Entry {idx} missing '{self.match_field}' field"
            
            if self.result_field not in entry:
                return False, f"Entry {idx} missing '{self.result_field}' field"
            
            match_items = entry[self.match_field]
            if not isinstance(match_items, list):
                return False, f"Entry {idx}: '{self.match_field}' must be a list"
            
            if not match_items:
                return False, f"Entry {idx}: '{self.match_field}' cannot be empty"
            
            result_item = entry[self.result_field]
            if not isinstance(result_item, str):
                return False, f"Entry {idx}: '{self.result_field}' must be a string"
            
            # Check for self-replacement
            if result_item in match_items:
                return False, (
                    f"Entry {idx}: Cannot replace {self.match_field} with itself. "
                    f"'{result_item}' is in both {self.match_field} and {self.result_field}"
                )
        
        return True, ""
    
    def load_config(self, config_file: Path) -> List[Dict[str, Any]]:
        """Load and validate configuration from .txt file (containing JSON).
        
        Args:
            config_file: Path to .txt configuration file (contains JSON data)
            
        Returns:
            Validated configuration list
            
        Raises:
            SystemExit: If file cannot be read or is invalid
        """
        config = load_json_from_txt(config_file)
        
        is_valid, error_msg = self.validate_config(config)
        if not is_valid:
            log(f"Configuration validation failed: {error_msg}", "ERROR")
            sys.exit(1)
        
        return config
    
    def load_configs_from_directory(self, input_dir: Path) -> List[Dict[str, Any]]:
        """Load configurations from directory.
        
        Args:
            input_dir: Directory containing .txt configuration files
            
        Returns:
            Combined configuration list from all files
            
        Raises:
            SystemExit: If directory doesn't exist or no files found
        """
        return load_configs_from_directory(
            input_dir,
            self.validate_config,
            self.load_config
        )
    
    def generate_datapack(
        self,
        config: List[Dict[str, Any]],
        output_dir: Path,
        filename: str = "replacements.json",
        pack_format: int = 10
    ) -> Path:
        """Generate complete datapack.
        
        Args:
            config: Configuration list
            output_dir: Base output directory
            filename: Name of the replacements file
            pack_format: Minecraft datapack format version
            
        Returns:
            Path to the generated replacements file
        """
        # Create datapack structure
        replacements_dir = create_datapack_structure(output_dir, self.datapack_path)
        
        # Generate replacements file
        output_file = generate_replacements_file(config, replacements_dir, filename)
        
        # Create pack.mcmeta
        create_pack_mcmeta(output_dir, pack_format, self.description)
        
        return output_file
