"""
Shared utilities for JAR, JSON, file, and item operations.
"""

from core.utils.jar import open_jar_safe, extract_namespaces_from_jar
from core.utils.json import load_json_from_jar, safe_json_load
from core.utils.item import (
    extract_namespace,
    get_base_name,
    is_tag_reference,
    is_valid_item_id,
    sanitize_filename
)
from core.utils.file import (
    read_item_lines,
    read_items_from_file
)

__all__ = [
    # JAR utilities
    'open_jar_safe',
    'extract_namespaces_from_jar',
    # JSON utilities
    'load_json_from_jar',
    'safe_json_load',
    # Item utilities
    'extract_namespace',
    'get_base_name',
    'is_tag_reference',
    'is_valid_item_id',
    'sanitize_filename',
    # File utilities
    'read_item_lines',
    'read_items_from_file',
]
