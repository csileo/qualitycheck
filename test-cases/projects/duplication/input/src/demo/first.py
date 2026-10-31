"""First."""


def first(values: list[int]) -> int:
    """Sum one way."""
    total = 0
    for value in values:
        if value > 0:
            total += value * 2
        else:
            total -= value
    return total
