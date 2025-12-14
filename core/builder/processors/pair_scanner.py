"""
Pair scanner for discovering mod pairs with overlapping base names.

This module provides functionality to scan installed mod directories and
automatically discover mod pairs that have overlapping base names, which
indicates potential replacement opportunities.
"""

import itertools
from pathlib import Path
from typing import List, Optional

from core.builder.models import DatapackType, ModPair
from core.builder.processors.file_parser import FileParser
from core.builder.processors.item_grouper import ItemGrouper
from core.utils.logging import log_warning


class PairScanner:
    """Scanner for finding mod pairs with overlapping base names."""
    
    def __init__(self, file_parser: FileParser, item_grouper: ItemGrouper):
        """
        Initialize PairScanner.
        
        Args:
            file_parser: FileParser instance for reading mod files
            item_grouper: ItemGrouper instance for calculating base names
        """
        self.file_parser = file_parser
        self.item_grouper = item_grouper
    
    def scan_installed_mods(
        self,
        datapack_type: DatapackType,
        scan_dir: Optional[Path] = None,
        min_matches: int = 1,
        work_dir: Optional[Path] = None
    ) -> List[ModPair]:
        """
        Scan installed mods and find pairs with matching base names.
        
        Args:
            datapack_type: Type of datapack (determines default scan directory and fluid handling)
            scan_dir: Optional directory to scan. If None, uses default from DATAPACK_CONFIGS
            min_matches: Minimum number of matching base names to include a pair (default: 1)
            work_dir: Optional work directory to copy discovered mod files to immediately
            
        Returns:
            List of ModPair objects sorted by match count (descending)
        """
        from core.builder.models import DATAPACK_CONFIGS
        
        # Use default scan directory if not provided
        if scan_dir is None:
            config = DATAPACK_CONFIGS[datapack_type]
            scan_dir = config.scan_dir
        
        # Check if scan directory exists
        if not scan_dir.exists():
            log_warning(f"Scan directory does not exist: {scan_dir}")
            return []
        
        if not scan_dir.is_dir():
            log_warning(f"Scan path is not a directory: {scan_dir}")
            return []
        
        # Load all mod files
        mod_data = {}
        from core.constants import FilePatterns
        txt_files = list(scan_dir.glob(f"*{FilePatterns.TXT_EXTENSION}"))
        if not txt_files:
            log_warning(f"No .txt files found in scan directory: {scan_dir}")
            return []
        
        for file_path in txt_files:
            namespace = file_path.stem  # e.g., "create" from "create.txt"
            if not namespace:  # Skip files with no stem (shouldn't happen, but be safe)
                continue
            items = self.file_parser.parse_txt_file(file_path)
            if items:  # Only include mods with items
                mod_data[namespace] = items
        
        if len(mod_data) < 2:
            log_warning(f"Need at least 2 mods to find pairs. Found {len(mod_data)} mod(s) in {scan_dir}")
            return []
        
        # Calculate base name overlap for each pair
        pairs = []
        is_fluid = DATAPACK_CONFIGS[datapack_type].is_fluid
        
        for mod1, mod2 in itertools.combinations(mod_data.keys(), 2):
            # Get base names for each mod
            mod1_base_names = {
                self.item_grouper.get_base_name(item, is_fluid)
                for item in mod_data[mod1]
            }
            mod2_base_names = {
                self.item_grouper.get_base_name(item, is_fluid)
                for item in mod_data[mod2]
            }
            
            # Calculate overlap
            overlap = mod1_base_names & mod2_base_names
            
            if len(overlap) >= min_matches:
                pairs.append(ModPair(
                    mod1=mod1,
                    mod2=mod2,
                    match_count=len(overlap),
                    mod1_items=mod_data[mod1],
                    mod2_items=mod_data[mod2]
                ))
        
        # Sort by match count (descending)
        pairs.sort(key=lambda p: p.match_count, reverse=True)
        
        # Copy files from discovered pairs to work directory immediately
        if work_dir is not None and pairs:
            import shutil
            mods_in_pairs = set()
            for pair in pairs:
                mods_in_pairs.add(pair.mod1)
                mods_in_pairs.add(pair.mod2)
            
            for mod_name in mods_in_pairs:
                source_file = scan_dir / f"{mod_name}.txt"
                if source_file.exists():
                    try:
                        dest_file = work_dir / f"{mod_name}.txt"
                        shutil.copy2(source_file, dest_file)
                    except (OSError, shutil.Error):
                        # Non-fatal: continue even if copy fails
                        pass
        
        return pairs

