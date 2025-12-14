"""
Data models for datapack builder.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Set, Dict

from core.constants import DefaultDirs


class DatapackType(Enum):
    """Enumeration of datapack types."""
    ITEMS = "oei"
    BLOCKS = "oeb"
    FLUIDS = "oef"


# Type name mapping for DatapackType enum
TYPE_NAME_MAP: Dict[DatapackType, str] = {
    DatapackType.ITEMS: "items",
    DatapackType.BLOCKS: "blocks",
    DatapackType.FLUIDS: "fluids"
}


@dataclass
class DatapackConfig:
    """Configuration for a datapack type."""
    type: DatapackType
    scan_dir: Path  # Default scan directory
    match_key: str  # JSON key for match items/blocks/fluids
    result_key: str  # JSON key for result items/blocks/fluids
    description: str  # Description prefix for pack.mcmeta
    is_fluid: bool  # Whether to use fluid normalization


@dataclass
class ModPair:
    """Represents a pair of mods with overlapping base names."""
    mod1: str  # namespace
    mod2: str  # namespace
    match_count: int  # number of overlapping base names
    mod1_items: Set[str]
    mod2_items: Set[str]


# Configuration mapping for each datapack type
DATAPACK_CONFIGS = {
    DatapackType.ITEMS: DatapackConfig(
        type=DatapackType.ITEMS,
        scan_dir=DefaultDirs.SCAN_ITEMS,
        match_key="matchItems",
        result_key="resultItems",
        description="One Enough Item",
        is_fluid=False
    ),
    DatapackType.BLOCKS: DatapackConfig(
        type=DatapackType.BLOCKS,
        scan_dir=DefaultDirs.SCAN_BLOCKS,
        match_key="matchBlock",
        result_key="resultBlock",
        description="One Enough Block",
        is_fluid=False
    ),
    DatapackType.FLUIDS: DatapackConfig(
        type=DatapackType.FLUIDS,
        scan_dir=DefaultDirs.SCAN_FLUIDS,
        match_key="matchFluid",
        result_key="resultFluid",
        description="One Enough Fluid",
        is_fluid=True
    ),
}

