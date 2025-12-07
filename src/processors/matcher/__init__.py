"""Matcher processors.

This module contains implementations of matcher processors.
"""

from src.processors.matcher.duplicate import DuplicateMatcherProcessor
from src.processors.matcher.config import (
    ConfigMatcherProcessor,
    ConfigMatcherValidator
)

__all__ = [
    "DuplicateMatcherProcessor",
    "ConfigMatcherProcessor",
    "ConfigMatcherValidator",
]
