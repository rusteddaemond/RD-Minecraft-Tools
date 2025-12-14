#!/usr/bin/env python3
"""
Process from Disk
Reads raw data files from disk to build namespace collections and other derived data.
This avoids loading everything into memory.
"""

import logging
from pathlib import Path
from collections import defaultdict
from core.utils.item import extract_namespace
from core.utils.file import read_item_lines

logger = logging.getLogger(__name__)


def collect_namespaces_from_disk(output_dir):
    """
    Read tag and recipe files from disk to build namespace collections.
    Processes files incrementally to minimize memory usage.
    """
    output_path = Path(output_dir)
    tags_dir = output_path / 'tags'
    tag_to_items_dir = output_path / 'tag_to_items'
    recipes_dir = output_path / 'recipes'
    item_inputs_dir = recipes_dir / 'item_inputs'
    item_outputs_dir = recipes_dir / 'item_outputs'
    
    blocks_by_namespace = defaultdict(set)
    items_by_namespace = defaultdict(set)
    fluids_by_namespace = defaultdict(set)
    all_referenced_items_by_ns = defaultdict(set)
    
    logger.info("Reading tags from disk to build namespace collections...")
    
    # Process tags by type
    for tag_type_dir in sorted(tags_dir.iterdir()):
        if not tag_type_dir.is_dir():
            continue
        
        tag_type = tag_type_dir.name
        target_dict = {
            'block': blocks_by_namespace,
            'item': items_by_namespace,
            'fluid': fluids_by_namespace
        }.get(tag_type, items_by_namespace)  # Default to items if unknown type
        
        for tag_file in sorted(tag_type_dir.glob('*.txt')):
            for item in read_item_lines(tag_file, skip_comments=True, skip_tag_refs=True):
                namespace = extract_namespace(item)
                if namespace:
                    target_dict[namespace].add(item)
                    all_referenced_items_by_ns[namespace].add(item)
    
    logger.info("Reading recipes from disk to build namespace collections...")
    
    # Process recipe inputs/outputs
    for inputs_file in sorted(item_inputs_dir.glob('*.txt')):
        for item in read_item_lines(inputs_file, skip_comments=True, skip_tag_refs=True):
            namespace = extract_namespace(item)
            if namespace:
                items_by_namespace[namespace].add(item)
                all_referenced_items_by_ns[namespace].add(item)
    
    for outputs_file in sorted(item_outputs_dir.glob('*.txt')):
        for item in read_item_lines(outputs_file, skip_comments=True, skip_tag_refs=True):
            namespace = extract_namespace(item)
            if namespace:
                items_by_namespace[namespace].add(item)
                all_referenced_items_by_ns[namespace].add(item)
    
    return blocks_by_namespace, items_by_namespace, fluids_by_namespace, all_referenced_items_by_ns

