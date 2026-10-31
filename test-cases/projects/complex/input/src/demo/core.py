"""Arithmetic."""


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def grade(x: int) -> int:
    """Map a value to a grade."""
    if x == 0:
        return 0
    if x == 1:
        return 10
    if x == 2:
        return 20
    if x == 3:
        return 30
    if x == 4:
        return 40
    if x == 5:
        return 50
    if x == 6:
        return 60
    if x == 7:
        return 70
    if x == 8:
        return 80
    if x == 9:
        return 90
    if x == 10:
        return 100
    return -1
