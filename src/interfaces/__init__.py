"""Interfaces (protocols) for RD-Minecraft-Tools."""

from src.interfaces.scanner import (
    IEntryFilter,
    IScannerProcessor
)
from src.interfaces.matcher import (
    IMatcherProcessor,
    IMatcherValidator
)
from src.interfaces.processor import (
    IJarProcessor,
    IFileProcessor
)
from src.interfaces.cleaner import (
    IIdentifierCleaner
)
from src.interfaces.datapack import (
    IDatapackGenerator
)

__all__ = [
    "IEntryFilter",
    "IScannerProcessor",
    "IMatcherProcessor",
    "IMatcherValidator",
    "IJarProcessor",
    "IFileProcessor",
    "IIdentifierCleaner",
    "IDatapackGenerator",
]
