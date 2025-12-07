"""Shared interfaces for scanners and matchers.

This module provides common argument parsing interfaces used across
scanner and matcher tools.
"""

from tools.interfaces.scanner_args import (
    add_scanner_input_args,
    add_scanner_output_args,
    add_scanner_cleaning_args
)
from tools.interfaces.matcher_args import (
    add_matcher_input_args,
    add_matcher_output_args
)

__all__ = [
    "add_scanner_input_args",
    "add_scanner_output_args",
    "add_scanner_cleaning_args",
    "add_matcher_input_args",
    "add_matcher_output_args",
]
