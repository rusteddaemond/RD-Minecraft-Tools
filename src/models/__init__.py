"""Data models for RD-Minecraft-Tools."""

from src.models.scanner import (
    NamespaceObject,
    ScannerResult,
    ScannerConfig
)
from src.models.matcher import (
    MatchRule,
    MatcherConfig,
    DuplicateMatch
)
from src.models.datapack import (
    DatapackMetadata,
    ReplacementRule
)
from src.models.jar import (
    JarEntry,
    JarMetadata
)
from src.models.recipe import (
    RecipeResult
)

__all__ = [
    # Scanner models
    "NamespaceObject",
    "ScannerResult",
    "ScannerConfig",
    # Matcher models
    "MatchRule",
    "MatcherConfig",
    "DuplicateMatch",
    # Datapack models
    "DatapackMetadata",
    "ReplacementRule",
    # JAR models
    "JarEntry",
    "JarMetadata",
    # Recipe models
    "RecipeResult",
]
