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
# The tiles of the second row; the rated tiles make the first.
MEASURES = {"coverage", "duplications", "security-hotspots"}


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


def _size(sloc: int) -> str:
    return str(sloc) if sloc < THOUSAND else f"{sloc / THOUSAND:.1f}k"


def _failed(label: str, failed: bool) -> str:
    return f"{label}, Failed" if failed else label


def _missing(name: str, title: str, tool: str, link: str) -> Image:
    content = svg.Tile(title, "n/a", f"{tool} is missing", svg.rating(None))
    label = f"{title}: n/a, {tool} is missing"
    return Image(name, label, svg.tile(content, label), 1 + (name in MEASURES), link)


def _gate(run: Run, judged: list[g.Gate], sloc: int) -> Image:
    conditions = [
        f"{gate.name}: {gate.detail}" for gate in judged if gate.status == "FAIL"
    ]
    passed = run.result == "PASS"
    label = (
        "Quality Gate: Passed"
        if passed
        else f"Quality Gate: Failed, {_plural(len(conditions), 'condition')} "
        f"failed: {'; '.join(conditions)}"
    )
    return Image(
        "quality-gate", label, svg.gate(passed, conditions, _size(sloc), label), 0
    )


def _reliability(m: g.Measures, failed: set[str]) -> Image:
    link = anchor("Bugs")
    if m.lint is None:
        return _missing("reliability", "Reliability", "ruff", link)
    count, grade = len(g.bugs(m.lint)), ratings.reliability(m.lint)
    noun = _plural(count, "bug")
    content = svg.Tile(
        "Reliability",
        str(count),
        noun.split(" ", 1)[1],
        svg.rating(grade),
        "bugs" in failed,
    )
    label = _failed(f"Reliability: rating {grade}, {noun}", "bugs" in failed)
    return Image("reliability", label, svg.tile(content, label), 1, link)


def _security(m: g.Measures, failed: set[str]) -> Image:
    link = anchor("Vulnerabilities (medium and high)")
    if m.vulnerabilities is None:
        return _missing("security", "Security", "bandit", link)
    count = len(g.severe(m.vulnerabilities))
    grade = ratings.security(m.vulnerabilities)
    noun = _plural(count, "vulnerability", "vulnerabilities")
    hit = "vulnerabilities" in failed
    content = svg.Tile(
        "Security", str(count), noun.split(" ", 1)[1], svg.rating(grade), hit
    )
    label = _failed(f"Security: rating {grade}, {noun}", hit)
    return Image("security", label, svg.tile(content, label), 1, link)


def _maintainability(m: g.Measures, failed: set[str]) -> Image:
    link = anchor(f"Smells (first {SMELLS_SHOWN})")
    if m.lint is None:
        return _missing("maintainability", "Maintainability", "ruff", link)
    smells = len(g.smells(m.lint))
    ratio = ratings.debt_ratio(smells, m.sloc)
    grade = ratings.maintainability(ratio)
    debt = "n/a" if ratio is None else f"{ratio:.1f}%"
    hit = bool({"maintainability", "complexity"} & failed)
    content = svg.Tile(
        "Maintainability",
        str(smells),
        f"code smells · {debt} debt",
        svg.rating(grade),
        hit,
    )
    label = _failed(
        f"Maintainability: rating {grade or 'n/a'}, {smells} code smells, "
        f"debt ratio {debt}",
        hit,
    )
    return Image("maintainability", label, svg.tile(content, label), 1, link)


def _coverage(m: g.Measures, failed: set[str], fail_under: float | None) -> Image:
    if m.coverage is None:
        value, detail = "n/a", "no coverage data"
    else:
        value = f"{m.coverage:.1f}%"
        detail = (
            "no fail_under" if fail_under is None else f"fail_under {fail_under:g}%"
        )
    hit = "coverage" in failed
    figure = svg.ring(m.coverage, (svg.GREEN, svg.RED))
    content = svg.Tile("Coverage", value, detail, figure, hit)
    label = _failed(f"Coverage: {value}, {detail}", hit)
    return Image("coverage", label, svg.tile(content, label), 2, anchor("Gates"))


def _duplications(m: g.Measures, failed: set[str]) -> Image:
    link = anchor("Duplication")
    if m.duplicates is None:
        return _missing("duplications", "Duplications", "pylint", link)
    percent = ratings.duplications(m.duplicates, m.sloc)
    value = "n/a" if percent is None else f"{percent:.1f}%"
    detail = "no lines of code" if percent is None else f"on {m.sloc} lines"
    hit = "duplication" in failed
    figure = svg.ring(percent, (svg.RATING["C"], svg.GRID))
    content = svg.Tile("Duplications", value, detail, figure, hit)
    label = _failed(f"Duplications: {value}, {detail}", hit)
    return Image("duplications", label, svg.tile(content, label), 2, link)


def _hotspots(m: g.Measures) -> Image:
    link = anchor("Low-severity vulnerabilities")
    if m.vulnerabilities is None:
        return _missing("security-hotspots", "Security Hotspots", "bandit", link)
    count = len(ratings.hotspots(m.vulnerabilities))
    content = svg.Tile(
        "Security Hotspots", str(count), "low severity, to review", svg.warning(count)
    )
    label = f"Security Hotspots: {count} to review"
    return Image("security-hotspots", label, svg.tile(content, label), 2, link)


def _day(date: str) -> str:
    try:
        return f"{MONTHS[int(date[5:7]) - 1]} {int(date[8:10])}"
    except (ValueError, IndexError):
        return date[:10]


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
        _gate(run, judged, m.sloc),
        _reliability(m, failed),
        _security(m, failed),
        _maintainability(m, failed),
        _coverage(m, failed, fail_under),
        _duplications(m, failed),
        _hotspots(m),
        _activity(rows, fail_under),
    ]


def _markdown(image: Image) -> str:
    alt = image.alt.replace("[", "\\[").replace("]", "\\]")
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
