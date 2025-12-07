"""Config-based matcher processor implementation."""

from __future__ import annotations
from typing import List, Dict, Any, Tuple
from pathlib import Path

from src.interfaces.matcher import IMatcherProcessor, IMatcherValidator
from src.models.matcher import MatchRule, MatcherConfig
from src.config_loader import load_json_from_txt, load_configs_from_directory


class ConfigMatcherValidator(IMatcherValidator):
    """Validator for matcher configurations."""
    
    def __init__(self, match_field: str, result_field: str):
        """Initialize validator.
        
        Args:
            match_field: Field name for match items/fluids
            result_field: Field name for result item/fluid
        """
        self.match_field = match_field
        self.result_field = result_field
    
    def validate(
        self,
        config: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """Validate configuration and return (is_valid, error_message).
        
        Args:
            config: Configuration list to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
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
        """Load and validate configuration from .txt file.
        
        Args:
            config_file: Path to .txt configuration file
            
        Returns:
            Validated configuration list
        """
        config = load_json_from_txt(config_file)
        is_valid, error_msg = self.validate(config)
        if not is_valid:
            from src.utils.logging import log
            import sys
            log(f"Configuration validation failed: {error_msg}", "ERROR")
            sys.exit(1)
        return config


class ConfigMatcherProcessor(IMatcherProcessor):
    """Processor for config-based matchers (OEI, OEF)."""
    
    def __init__(
        self,
        match_field: str,
        result_field: str
    ):
        """Initialize config matcher processor.
        
        Args:
            match_field: Field name for match items/fluids
            result_field: Field name for result item/fluid
        """
        self.match_field = match_field
        self.result_field = result_field
        self.validator = ConfigMatcherValidator(match_field, result_field)
    
    def find_duplicates(
        self,
        objects: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """Not used for config-based matchers.
        
        Args:
            objects: Dictionary mapping object_id to list of namespaces
            
        Returns:
            Empty dictionary (not applicable for config-based matchers)
        """
        return {}
    
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
    
    def load_config_from_file(self, config_file: Path) -> List[Dict[str, Any]]:
        """Load and validate configuration from file.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Validated configuration list
        """
        return self.validator.load_config(config_file)
    
    def load_configs_from_directory(self, input_dir: Path) -> List[Dict[str, Any]]:
        """Load configurations from directory.
        
        Args:
            input_dir: Directory containing .txt configuration files
            
        Returns:
            Combined configuration list from all files
        """
        return load_configs_from_directory(
            input_dir,
            self.validator.validate,
            self.validator.load_config
        )
