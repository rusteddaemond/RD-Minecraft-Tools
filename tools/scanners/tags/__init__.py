"""Tag scanning module for extracting and processing Minecraft tags.

This module provides classes and functions for:
- Extracting tags from JAR files
- Resolving tag references
- Processing tag data structures
- Detecting equipment items and slots
"""

from __future__ import annotations

from .tag_processor import TagData, TagExtractor, TagReferenceResolver
from .equipment_detector import EquipmentDetector
from .constants import (
    COMMON_TAG_PATTERNS,
    ALL_EQUIPMENT_SLOTS,
    EQUIPMENT_KEYWORDS,
)

__all__ = [
    "TagData",
    "TagExtractor",
    "TagReferenceResolver",
    "EquipmentDetector",
    "COMMON_TAG_PATTERNS",
    "ALL_EQUIPMENT_SLOTS",
    "EQUIPMENT_KEYWORDS",
]
