"""Affix cleaning utilities for scanner tools.

This module provides shared affix definitions and cleaning functions
used across all scanner tools to remove file extensions and affixes.
"""

from __future__ import annotations
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------
# Extended affix definitions
# ---------------------------------------------------------------------
AFFIX_GROUPS: Dict[str, List[str]] = {
    # State / orientation affixes grouped by meaning
    "orientation_faces": [
        "_bottom", "_top", "_front", "_back", "_left", "_right", "_side", "_reverse", "_base"
    ],
    "orientation_corners": [
        "_corner", "_inner", "_outer", "_noside", "_nosides", "_inside"
    ],
    "orientation_vertical": [
        "_up", "_down", "_upper", "_lower", "_middle", "_mid", "_center", "_centered", "_main", "_full"
    ],
    "orientation_horizontal": [
        "_horizontal", "_ew", "_ns", "_x", "_z"
    ],
    "orientation_end": [
        "_end", "_post", "_even", "_odd", "_foot", "_head", "_far", "_gate_wall"
    ],
    "orientation_size": [
        "_single", "_double", "_tall", "_plus", "_adv"
    ],
    "state_binary": [
        "_open", "_opened", "_close", "_closed", "_on", "_off", "_pressed", "_extended",
        "_connected", "_occupied", "_empty", "_filled", "_drained",
        "_activated", "_lit", "_weak", "_supported", "_support",
        "_moist", "_unused", "_alt", "_wet", "_decorated", "_tied",
        "_extrudes", "_garnish", "_leftover", "_active", "_inactive",
        "_monster", "_player", "_emissive", "_body", "_bone", "_stabilized", "_unlinked"
    ],
    "state_progression": [
        "_new", "_old",
        "_one", "_two", "_three", "_four", "_five",
        "_0", "_1", "_2", "_3", "_4", "_5", "_6", "_7", "_8", "_9", "_10",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
        "_age0", "_age1", "_age2", "_age3", "_age4", "_age5",
        "_age6", "_age7", "_age8", "_age9", "_age10", "_stage",
        "_stage0", "_stage1", "_stage2", "_stage3", "_stage4", "_stage5",
        "_stage6", "_stage7", "_stage8", "_stage9", "_stage10",
        "_slice0", "_slice1", "_slice2", "_slice3", "_slice4", "_slice5",
        "_slice6", "_slice7", "_slice8", "_slice9", "_slice10", "_level",
        "_level0", "_level1", "_level2", "_level3", "_level4", "_level5",
        "_level6", "_level7", "_level8", "_level9", "_level10"
    ],
    "state_content": [
        "_honey", "_water"
    ],
    "inventory": [
        "_inventory", "_slot"
    ],
    "ctm_meta": [
        "-ctm"
    ],
    "misc_suffixes": [
        "_with", "_t"
    ]
}

# Flatten all affixes into one list for fast lookup
AFFIXES: List[str] = [a for group in AFFIX_GROUPS.values() for a in group]

# Default file extensions to remove (for block/item scanners)
DEFAULT_EXTENSIONS: Tuple[str, ...] = (".png", ".jpeg", ".jpg", ".gif")

# File extensions for fluid scanner (includes .json)
FLUID_EXTENSIONS: Tuple[str, ...] = (".png", ".jpeg", ".jpg", ".gif", ".json")


# ---------------------------------------------------------------------
# Cleansing function
# ---------------------------------------------------------------------
def clean_identifier(stem: str, passes: int = 3, extensions: Tuple[str, ...] = DEFAULT_EXTENSIONS) -> str:
    """Remove file extensions and grouped affixes recursively.
    
    Args:
        stem: The identifier to clean
        passes: Number of cleaning passes to perform
        extensions: Tuple of file extensions to remove
        
    Returns:
        Cleaned identifier
    """
    for _ in range(passes):
        for ext in extensions:
            if stem.endswith(ext):
                stem = stem[:-len(ext)]
        for affix in AFFIXES:
            if stem.endswith(affix):
                stem = stem[:-len(affix)]
    return stem
