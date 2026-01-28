"""
This module provides utility functions for mathematical calculations.
"""

from typing import Sequence, Union


def calc_avg(nums: Sequence[Union[int, float]]) -> float:
    """
    Calculates the arithmetic mean of a sequence of numbers.

    Args:
        nums: A sequence (list, tuple, etc.) containing integers or floats.

    Returns:
        float: The average of the numbers. Returns 0.0 if the sequence is empty
               to maintain compatibility with existing test requirements.

    Raises:
        TypeError: If the input sequence contains non-numeric values.
    """
    if not nums:
        return 0.0

    try:
        # Convert to float to ensure precision and consistent return type
        return float(sum(nums) / len(nums))
    except TypeError as exc:
        raise TypeError("All elements in 'nums' must be integers or floats.") from exc
