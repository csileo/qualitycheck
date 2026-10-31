"""report.md: the result, the gates, the metrics, the findings and the trend."""

from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from qualitycheck import gates as g
from qualitycheck.history import last_pass

SHORT = 10
SMELLS_SHOWN = 30
TREND_ROWS = 6
TREND_COLUMNS = [
    "date",
    "commit",
    "result",
    "bugs",
    "vulnerabilities",
    "smells",
    "coverage",
]


@dataclass(frozen=True)
class Run:
    """The check being reported: tested commit, date and result."""

    commit: str
    date: str
    result: str


def _last_pass(run: Run, rows: list[dict[str, str]]) -> str:
    row = (
        {"commit": run.commit, "date": run.date}
        if run.result == "PASS"
        else last_pass(rows)
    )
    if row is None:
        return "none yet"
    return f"`{row['commit'][:SHORT]}`, {row['date']}"


def _header(run: Run, rows: list[dict[str, str]]) -> list[str]:
    return [
        "# Quality check report",
        "",
        f"- Tested commit: `{run.commit[:SHORT]}`",
        f"- Date: {run.date}",
        f"- Result: **{run.result}**",
        f"- Last passing commit: {_last_pass(run, rows)}",
    ]


def _gates(gates: list[g.Gate]) -> list[str]:
    lines = ["", "## Gates", "", "| Gate | Result | Detail |", "|---|---|---|"]
    return lines + [
        f"| {gate.name} | {gate.status} | {gate.detail} |" for gate in gates
    ]


def _metrics(m: g.Measures) -> list[str]:
    low = [v for v in m.vulnerabilities or [] if v.severity not in g.SEVERE]
    coverage = "n/a" if m.coverage is None else f"{m.coverage:.1f}%"
    return [
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Lines of code | {m.sloc} |",
        f"| Smells | {len(g.smells(m.lint))} |",
        f"| Low-severity vulnerabilities | {len(low)} |",
        f"| Coverage | {coverage} |",
    ]


def _section(title: str, items: Iterable, line: Callable) -> list[str]:
    shown = [f"- {line(item)}" for item in items]
    return ["", f"## {title}", "", *(shown or ["- none"])]


def _finding(f: g.Finding | g.Vulnerability) -> str:
    return f"`{f.path}:{f.line}` {f.code} {f.message}"


def _frequent_first(findings: list[g.Finding]) -> list[g.Finding]:
    counts = Counter(f.code for f in findings)
    return sorted(findings, key=lambda f: (-counts[f.code], f.code, f.path, f.line))


def _findings(m: g.Measures) -> list[str]:
    low = [v for v in m.vulnerabilities or [] if v.severity not in g.SEVERE]
    smells = _frequent_first(g.smells(m.lint))
    return [
        *_section("Bugs", g.bugs(m.lint), _finding),
        *_section(
            "Vulnerabilities (medium and high)", g.severe(m.vulnerabilities), _finding
        ),
        *_section("Complexity", g.complex_functions(m.lint), _finding),
        *_section("Maintainability below A", g.unmaintainable(m.maintainability), str),
        *_section("Duplication", m.duplicates or [], str),
        *_section(f"Smells (first {SMELLS_SHOWN})", smells[:SMELLS_SHOWN], _finding),
        *_section("Low-severity vulnerabilities", low, _finding),
        *_section("Broken links", m.links or [], _finding),
    ]


def _tests_output(m: g.Measures) -> list[str]:
    if m.tests is None or m.tests.returncode == 0:
        return []
    return ["", "## Tests output", "", "```", m.tests.tail.strip(), "```"]


def _trend(rows: list[dict[str, str]]) -> list[str]:
    lines = ["", "## Trend", "", "| " + " | ".join(TREND_COLUMNS) + " |"]
    lines.append("|" + "---|" * len(TREND_COLUMNS))
    for row in rows[-TREND_ROWS:]:
        values = [row.get(column, "") for column in TREND_COLUMNS]
        values[1] = values[1][:SHORT]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def render(
    run: Run, gates: list[g.Gate], m: g.Measures, rows: list[dict[str, str]]
) -> str:
    """Return the report; rows is the history, the current run included."""
    parts = [
        _header(run, rows),
        _gates(gates),
        _metrics(m),
        _findings(m),
        _tests_output(m),
        _trend(rows),
        ["", "Regenerate: `uv run qualitycheck`."],
    ]
    return "\n".join(line for part in parts for line in part) + "\n"
