"""
CLI utility functions.
"""

from typing import List

from core.builder.models import DatapackType


def determine_datapack_types(args) -> List[DatapackType]:
    """
    Determine which datapack types to process based on CLI arguments.
    
    Args:
        args: ArgumentParser namespace with items, blocks, fluids flags
        
    Returns:
        List of DatapackType enums to process. If no flags specified,
        returns all types.
    """
    types_to_process = []
    
    if args.items or args.blocks or args.fluids:
        if args.items:
            types_to_process.append(DatapackType.ITEMS)
        if args.blocks:
            types_to_process.append(DatapackType.BLOCKS)
        if args.fluids:
            types_to_process.append(DatapackType.FLUIDS)
    else:
        # Default: process all types
        types_to_process = [DatapackType.ITEMS, DatapackType.BLOCKS, DatapackType.FLUIDS]
    
    return types_to_process

