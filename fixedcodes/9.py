"""
This module provides utility functions for dictionary manipulation.
"""

from typing import Dict, Any


def merge_dicts(base_dict: Dict[Any, Any], update_dict: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Merges two dictionaries into a new dictionary without modifying the originals.

    If a key exists in both dictionaries, the value from 'update_dict' will
    overwrite the value from 'base_dict' in the resulting dictionary.

    Args:
        base_dict (Dict[Any, Any]): The initial dictionary to be merged.
        update_dict (Dict[Any, Any]): The dictionary containing values to merge
            into the base dictionary.

    Returns:
        Dict[Any, Any]: A new dictionary containing the merged result.
    """
    result = base_dict.copy()
    result.update(update_dict)
    return result
