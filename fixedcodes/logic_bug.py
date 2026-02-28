"""logic_bug.py

Module containing a simple countdown function that prints each number
on its own line.
"""


def count_down(n: int) -> None:
    """Print a countdown from n to 1, inclusive (one number per line).

    If n is 0 or negative, nothing is printed.

    Args:
        n: Starting integer for the countdown.
    """
    while n > 0:
        print(n)
        n -= 1