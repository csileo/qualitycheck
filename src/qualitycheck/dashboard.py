"""The dashboard of a check, as on Sonar: its SVG images and their Markdown."""

import re
from dataclasses import dataclass

from qualitycheck import gates as g
from qualitycheck import ratings, svg
from qualitycheck.report import SMELLS_SHOWN, TREND_ROWS, Run

MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
THOUSAND = 1000
# Each tile's title, row and section, in one place: a tile and its n/a
# variant must land in the same row, or the row breaks in two.
TILES = {
    "reliability": ("Reliability", 1, "Bugs"),
    "security": ("Security", 1, "Vulnerabilities (medium and high)"),
    "maintainability": ("Maintainability", 1, f"Smells (first {SMELLS_SHOWN})"),
    "coverage": ("Coverage", 2, "Gates"),
    "duplications": ("Duplications", 2, "Duplication"),
    "security-hotspots": ("Security Hotspots", 2, "Low-severity vulnerabilities"),
}


@dataclass(frozen=True)
class Image:
    """An image of the dashboard; images of the same row sit side by side."""

    name: str
    alt: str
    svg: str
    row: int
    link: str = ""


def anchor(heading: str) -> str:
    """GitHub's link to a heading of the report."""
    return "#" + re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")


def _plural(count: int, noun: str, many: str = "") -> str:
    return f"{count} {noun if count == 1 else many or noun + 's'}"


def _size(m: g.Measures) -> str:
    if m.maintainability is None:
        return "n/a"
    return str(m.sloc) if m.sloc < THOUSAND else f"{m.sloc / THOUSAND:.1f}k"


def _tile(name: str, content: svg.Tile, label: str) -> Image:
    _, row, heading = TILES[name]
    if content.failed:
        label = f"{label}, Failed"
    return Image(name, label, svg.tile(content, label), row, anchor(heading))


def _missing(name: str, tool: str) -> Image:
    title = TILES[name][0]
    content = svg.Tile(title, "n/a", f"{tool} is missing", svg.rating(None))
    return _tile(name, content, f"{title}: n/a, {tool} is missing")


def _gate(run: Run, judged: list[g.Gate], m: g.Measures) -> Image:
    conditions = [
        f"{gate.name}: {gate.detail}" for gate in judged if gate.status == "FAIL"
    ]
    passed = run.result == "PASS"
    summary = (
        "All conditions passed."
        if passed
        else f"{_plural(len(conditions), 'condition')} failed"
    )
    label = (
        "Quality Gate: Passed"
        if passed
        else f"Quality Gate: Failed, {summary}: {'; '.join(conditions)}"
    )
    banner = svg.Banner(passed, summary, conditions, _size(m))
    return Image("quality-gate", label, svg.gate(banner, label), 0)


def _reliability(m: g.Measures, failed: set[str]) -> Image:
    if m.lint is None:
        return _missing("reliability", "ruff")
    count, grade = len(g.bugs(m.lint)), ratings.reliability(m.lint)
    noun = _plural(count, "bug")
    figure = svg.rating(grade)
    content = svg.Tile(
        "Reliability", str(count), noun.split(" ", 1)[1], figure, "bugs" in failed
    )
    return _tile("reliability", content, f"Reliability: rating {grade}, {noun}")


def _security(m: g.Measures, failed: set[str]) -> Image:
    if m.vulnerabilities is None:
        return _missing("security", "bandit")
    count = len(g.severe(m.vulnerabilities))
    grade = ratings.security(m.vulnerabilities)
    noun = _plural(count, "vulnerability", "vulnerabilities")
    content = svg.Tile(
        "Security",
        str(count),
        noun.split(" ", 1)[1],
        svg.rating(grade),
        "vulnerabilities" in failed,
    )
    return _tile("security", content, f"Security: rating {grade}, {noun}")


def _maintainability(m: g.Measures, failed: set[str]) -> Image:
    if m.lint is None:
        return _missing("maintainability", "ruff")
    if m.maintainability is None:
        return _missing("maintainability", "radon")
    smells = g.smells(m.lint)
    ratio = ratings.debt_ratio(smells, m.sloc)
    grade = ratings.maintainability(ratio)
    debt = "n/a" if ratio is None else f"{ratio:.1f}%"
    content = svg.Tile(
        "Maintainability",
        str(len(smells)),
        f"code smells · {debt} debt",
        svg.rating(grade),
        bool({"maintainability", "complexity"} & failed),
    )
    label = (
        f"Maintainability: rating {grade or 'n/a'}, {len(smells)} code smells, "
        f"debt ratio {debt}"
    )
    return _tile("maintainability", content, label)


def _coverage(m: g.Measures, failed: set[str], fail_under: float | None) -> Image:
    if m.coverage is None:
        value, detail = "n/a", "no coverage data"
    else:
        value = f"{m.coverage:.1f}%"
        detail = (
            "no fail_under" if fail_under is None else f"fail_under {fail_under:g}%"
        )
    figure = svg.ring(m.coverage, (svg.GREEN, svg.RED))
    content = svg.Tile("Coverage", value, detail, figure, "coverage" in failed)
    return _tile("coverage", content, f"Coverage: {value}, {detail}")


def _duplications(m: g.Measures, failed: set[str]) -> Image:
    if m.duplicates is None:
        return _missing("duplications", "pylint")
    if m.maintainability is None:
        return _missing("duplications", "radon")
    percent = ratings.duplications(m.duplicates, m.sloc)
    value = "n/a" if percent is None else f"{percent:.1f}%"
    detail = "no lines of code" if percent is None else f"on {m.sloc} lines"
    figure = svg.ring(percent, (svg.RATING["C"], svg.GRID))
    content = svg.Tile("Duplications", value, detail, figure, "duplication" in failed)
    return _tile("duplications", content, f"Duplications: {value}, {detail}")


def _hotspots(m: g.Measures) -> Image:
    if m.vulnerabilities is None:
        return _missing("security-hotspots", "bandit")
    count = len(g.low(m.vulnerabilities))
    content = svg.Tile(
        "Security Hotspots", str(count), "low severity, to review", svg.warning(count)
    )
    return _tile("security-hotspots", content, f"Security Hotspots: {count} to review")


def _day(date: str) -> str:
    try:
        month, day = int(date[5:7]), int(date[8:10])
    except ValueError:
        return date[:10]
    return f"{MONTHS[month - 1]} {day}" if 1 <= month <= len(MONTHS) else date[:10]


def _number(cell: str | None) -> float | None:
    try:
        return float(cell or "")
    except ValueError:
        return None


def _last(cell: str | None, unit: str = "") -> str:
    return f"{cell}{unit}" if cell else "n/a"


def _activity(rows: list[dict[str, str]], fail_under: float | None) -> Image:
    shown = rows[-TREND_ROWS:]

    def series(name: str, column: str, color: str) -> svg.Series:
        return svg.Series(name, color, [_number(row.get(column)) for row in shown])

    issues = [
        series("Code Smells", "smells", svg.SMELLS),
        series("Bugs", "bugs", svg.BUGS),
        series("Vulnerabilities", "vulnerabilities", svg.VULNERABILITIES),
    ]
    last = shown[-1] if shown else {}
    label = (
        f"Activity over the last {_plural(len(shown), 'check')}: at the last one, "
        f"code smells {_last(last.get('smells'))}, bugs {_last(last.get('bugs'))}, "
        f"vulnerabilities {_last(last.get('vulnerabilities'))}, "
        f"coverage {_last(last.get('coverage'), '%')}"
    )
    chart = svg.activity(
        [_day(row.get("date", "")) for row in shown],
        issues,
        series("Coverage", "coverage", svg.GREEN),
        fail_under,
        label,
    )
    return Image("activity", label, chart, 3)


def images(
    run: Run,
    judged: list[g.Gate],
    m: g.Measures,
    rows: list[dict[str, str]],
    fail_under: float | None,
) -> list[Image]:
    """The dashboard of a run; rows is the history, the run included."""
    failed = {gate.name for gate in judged if gate.status == "FAIL"}
    return [
        _gate(run, judged, m),
        _reliability(m, failed),
        _security(m, failed),
        _maintainability(m, failed),
        _coverage(m, failed, fail_under),
        _duplications(m, failed),
        _hotspots(m),
        _activity(rows, fail_under),
    ]


def _markdown(image: Image) -> str:
    # A new line would end the image; a bracket or a backslash would cut it.
    alt = " ".join(image.alt.split())
    for special in "\\[]":
        alt = alt.replace(special, "\\" + special)
    shown = f"![{alt}](images/{image.name}.svg)"
    return f"[{shown}]({image.link})" if image.link else shown


def markdown(shown: list[Image]) -> list[str]:
    """The report's lines showing the images, one paragraph per row."""
    lines: list[str] = []
    for index, image in enumerate(shown):
        if index and image.row != shown[index - 1].row:
            lines.append("")
        lines.append(_markdown(image))
    return lines
