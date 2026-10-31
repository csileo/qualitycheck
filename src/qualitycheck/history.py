"""history.csv: one row per check, `;` separator, rows never rewritten."""

COLUMNS = [
    "date",
    "commit",
    "result",
    "tests",
    "bugs",
    "vulnerabilities",
    "smells",
    "complex_functions",
    "duplicated_blocks",
    "broken_links",
    "coverage",
    "sloc",
]
SEPARATOR = ";"


def parse(text: str) -> list[dict[str, str]]:
    """Return the rows of a history, oldest first."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    header = lines[0].split(SEPARATOR)
    return [
        dict(zip(header, line.split(SEPARATOR), strict=False)) for line in lines[1:]
    ]


def append(text: str, row: dict[str, str]) -> str:
    """Return the history with row added; an empty history gets the header."""
    if not text.strip():
        text = SEPARATOR.join(COLUMNS) + "\n"
    elif not text.endswith("\n"):
        text += "\n"
    return text + SEPARATOR.join(str(row.get(column, "")) for column in COLUMNS) + "\n"


def last_pass(rows: list[dict[str, str]]) -> dict[str, str] | None:
    """Return the last passing row, or None."""
    return next((row for row in reversed(rows) if row.get("result") == "PASS"), None)
