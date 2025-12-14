#!/usr/bin/env python3
"""
JSON Utilities
Common functions for JSON parsing with error handling.
"""

import json
import logging

logger = logging.getLogger(__name__)


def load_json_from_jar(jar, file_path: str, default=None):
    """
    Load and parse JSON from a JAR file.
    
    Args:
        jar: ZipFile object
        file_path: Path to JSON file within JAR
        default: Value to return on error (default: None)
    
    Returns:
        Parsed JSON data or default value on error
    """
    try:
        with jar.open(file_path) as f:
            content = f.read().decode('utf-8')
            return json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
        logger.debug(f"Failed to load JSON from {file_path}: {e}")
        return default
    except Exception as e:
        logger.warning(f"Unexpected error loading JSON from {file_path}: {e}")
        return default


def safe_json_load(content: str, default=None):
    """
    Safely parse JSON content with error handling.
    
    Args:
        content: JSON string to parse
        default: Value to return on error (default: None)
    
    Returns:
        Parsed JSON data or default value on error
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.debug(f"Failed to parse JSON: {e}")
        return default
    except Exception as e:
        logger.warning(f"Unexpected error parsing JSON: {e}")
        return default

