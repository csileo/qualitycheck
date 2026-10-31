"""Sonar's ratings of the measures, for display only (ADR 0004)."""

import re

from qualitycheck import gates as g

SMELL_MINUTES = 5
LINE_MINUTES = 30
DEBT_BOUNDS = [(5.0, "A"), (10.0, "B"), (20.0, "C"), (50.0, "D")]
# A copy in pylint's message: module:[start:end], start from 0, end excluded.
COPY = re.compile(r"([\w.]+):\[(\d+):(\d+)\]")


def reliability(lint: list[g.Finding]) -> str:
    """A without bug; C when the worst is of ruff's B family; D for F or PLE."""
    found = g.bugs(lint)
    if not found:
        return "A"
    return "C" if all(f.code.startswith("B") for f in found) else "D"


def security(vulnerabilities: list[g.Vulnerability]) -> str:
    """A without medium or high; C when the worst is medium; D high; E high and sure."""
    found = g.severe(vulnerabilities)
    if not found:
        return "A"
    high = [v for v in found if v.severity == "HIGH"]
    if any(v.confidence == "HIGH" for v in high):
        return "E"
    return "D" if high else "C"


def debt_ratio(smells: list[g.Finding], sloc: int) -> float | None:
    """The time to fix the smells over the time to write the code, in percent.

    Only the smells of src/ count: the lines of code are those of src/.
    """
    if not sloc:
        return None
    count = sum(1 for smell in smells if smell.path.startswith("src/"))
    # Multiplied first: a ratio on a bound, such as 5 %, stays exact.
    return count * SMELL_MINUTES * 100 / (sloc * LINE_MINUTES)


def maintainability(ratio: float | None) -> str | None:
    """A up to 5 %, B up to 10 %, C up to 20 %, D up to 50 %, E above."""
    if ratio is None:
        return None
    return next((rating for bound, rating in DEBT_BOUNDS if ratio <= bound), "E")


def duplicated_lines(duplicates: list[str]) -> int:
    """The lines in pylint's duplicated blocks, each line of a module counted once."""
    lines: dict[str, set[int]] = {}
    for block in duplicates:
        for module, start, end in COPY.findall(block):
            lines.setdefault(module, set()).update(range(int(start), int(end)))
    return sum(len(numbers) for numbers in lines.values())


def duplications(duplicates: list[str], sloc: int) -> float | None:
    """The duplicated lines over the lines of code, in percent, at most 100."""
    if not sloc:
        return None
    return min(duplicated_lines(duplicates) * 100 / sloc, 100.0)
