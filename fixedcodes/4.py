"""
This module provides an implementation of the Bubble Sort algorithm.
"""

from typing import List


def bubble_sort(arr: List) -> List:
    """
    Sorts a list of elements in ascending order using the Bubble Sort algorithm.

    Bubble Sort is a simple comparison-based sorting algorithm that repeatedly
    steps through the list, compares adjacent elements and swaps them if they
    are in the wrong order. This implementation includes an optimization
    to terminate early if the list is already sorted.

    Args:
        arr (List): The list of comparable elements to be sorted.

    Returns:
        List: The sorted list (modified in-place).
    """
    n = len(arr)
    for i in range(n):
        # Track if any swaps were made in this iteration to allow early exit
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                # Fix: Replace comparison '==' with assignment '=' for the swap operation
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True

        # Optimization: If no elements were swapped by the inner loop, the array is sorted
        if not swapped:
            break

    return arr
