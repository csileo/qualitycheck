"""SVG images of the dashboard, drawn as text: no script, no external reference.

Each image draws its own white card, so it reads the same in light and dark
themes; its title and aria-label hold its alternative text.
"""

import math
from dataclasses import dataclass
from xml.sax.saxutils import escape, quoteattr  # nosec B406 - escapes, parses nothing

FONT = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
TEXT, MUTED, BORDER, LINK, GRID = "#333333", "#6a737d", "#e1e4e8", "#236a97", "#eeeeee"
GREEN, RED, GREY, ORANGE = "#00aa00", "#d02f3a", "#9aa0a6", "#ed7d20"
RATING = {"A": GREEN, "B": "#b0d513", "C": "#eabe06", "D": ORANGE, "E": "#e00000"}
SMELLS, BUGS, VULNERABILITIES = "#236a97", "#24c6e0", RED
WIDE = 788
TILE_WIDTH, TILE_HEIGHT = 260, 128
GAUGE = (TILE_WIDTH - 40, 82)
LINE_HEIGHT = 18


@dataclass(frozen=True)
class Tile:
    """A tile: title, big value, detail line, figure on the right."""

    title: str
    value: str
    detail: str
    figure: str
    failed: bool = False


@dataclass(frozen=True)
class Series:
    """A line of a chart: name, colour, one value per run, None when unknown."""

    name: str
    color: str
    values: list[float | None]


def document(size: tuple[int, int], label: str, body: list[str]) -> str:
    """A complete SVG document with its alternative text."""
    width, height = size
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
            f"aria-label={quoteattr(label)} font-family={quoteattr(FONT)}>",
            f"<title>{escape(label)}</title>",
            *body,
            "</svg>",
            "",
        ]
    )


def card(width: int, height: int) -> str:
    """The white card behind an image."""
    return (
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="6" '
        f'fill="#ffffff" stroke="{BORDER}"/>'
    )


def text(at: tuple[float, float], value: str, size: int = 13, style: str = "") -> str:
    """A text at (x, y); style adds attributes, such as fill or text-anchor."""
    x, y = at
    attributes = style if "fill=" in style else f'fill="{TEXT}" {style}'.strip()
    return (
        f'<text x="{x:g}" y="{y:g}" font-size="{size}" {attributes}>'
        f"{escape(value)}</text>"
    )


def badge(width: int) -> str:
    """The red "Failed" badge at the top right of a card."""
    return (
        f'<rect x="{width - 70}" y="14" width="56" height="20" rx="10" fill="{RED}"/>'
        + text(
            (width - 42, 28),
            "Failed",
            11,
            'fill="#ffffff" font-weight="600" text-anchor="middle"',
        )
    )


def rating(grade: str | None) -> str:
    """A rating A to E in its colour; a grey n/a without rating."""
    cx, cy = GAUGE
    if grade is None:
        return (
            f'<circle cx="{cx}" cy="{cy}" r="20" fill="none" stroke="{GREY}" '
            'stroke-width="3"/>'
            + text((cx, cy + 4), "n/a", 11, f'fill="{GREY}" text-anchor="middle"')
        )
    return f'<circle cx="{cx}" cy="{cy}" r="20" fill="{RATING[grade]}"/>' + text(
        (cx, cy + 7),
        grade,
        20,
        'fill="#ffffff" font-weight="bold" text-anchor="middle"',
    )


def ring(percent: float | None, colors: tuple[str, str]) -> str:
    """A ring filled to percent with the first colour, the rest in the second."""
    cx, cy = GAUGE
    length = 2 * math.pi * 20
    filled = length * (percent or 0) / 100
    full, rest = colors if percent is not None else (GREY, GREY)
    return (
        f'<circle cx="{cx}" cy="{cy}" r="20" fill="none" stroke="{rest}" '
        f'stroke-width="7"/><circle cx="{cx}" cy="{cy}" r="20" fill="none" '
        f'stroke="{full}" stroke-width="7" stroke-dasharray="{filled:.1f} '
        f'{length:.1f}" transform="rotate(-90 {cx} {cy})"/>'
    )


def warning(count: int | None) -> str:
    """The hotspot sign: an exclamation mark in a ring, grey when unknown or none."""
    cx, cy = GAUGE
    color = RATING["B"] if count else GREY
    return (
        f'<circle cx="{cx}" cy="{cy}" r="20" fill="none" stroke="{color}" '
        f'stroke-width="3"/>'
        + text(
            (cx, cy + 7),
            "!",
            20,
            f'fill="{color}" font-weight="bold" text-anchor="middle"',
        )
    )


def tile(content: Tile, label: str) -> str:
    """A tile of the dashboard."""
    body = [
        card(TILE_WIDTH, TILE_HEIGHT),
        text((16, 28), content.title, 14, 'font-weight="600"'),
        *([badge(TILE_WIDTH)] if content.failed else []),
        text((16, 78), content.value, 30, f'fill="{LINK}" font-weight="600"'),
        text((16, 104), content.detail, 12, f'fill="{MUTED}"'),
        content.figure,
    ]
    return document((TILE_WIDTH, TILE_HEIGHT), label, body)


def gate(passed: bool, conditions: list[str], size: str, label: str) -> str:
    """The Quality Gate banner: Passed or Failed, the failed conditions, the size."""
    # The conditions start at y=78, one per line, above an 18-pixel margin.
    height = 96 + max(0, len(conditions) - 1) * LINE_HEIGHT
    color, word = (GREEN, "Passed") if passed else (RED, "Failed")
    mark = (
        '<path d="M38 62 L44 68 L55 56" fill="none" stroke="#ffffff" '
        'stroke-width="3.5" stroke-linecap="round"/>'
        if passed
        else '<path d="M40 56 L52 68 M52 56 L40 68" stroke="#ffffff" '
        'stroke-width="3.5" stroke-linecap="round"/>'
    )
    count = len(conditions)
    summary = (
        "All conditions passed."
        if passed
        else f"{count} condition{'' if count == 1 else 's'} failed"
    )
    body = [
        card(WIDE, height),
        f'<rect x="0" y="0" width="8" height="{height}" rx="4" fill="{color}"/>',
        text((28, 30), "Quality Gate", 13, f'fill="{MUTED}" font-weight="600"'),
        f'<circle cx="46" cy="62" r="16" fill="{color}"/>',
        mark,
        text((72, 72), word, 30, f'fill="{color}" font-weight="bold"'),
        text((210, 58), summary, 14, 'font-weight="600"'),
        *[
            text((210, 78 + i * LINE_HEIGHT), condition, 12, f'fill="{MUTED}"')
            for i, condition in enumerate(conditions)
        ],
        text(
            (WIDE - 20, 40),
            size,
            22,
            f'fill="{LINK}" font-weight="600" text-anchor="end"',
        ),
        text(
            (WIDE - 20, 60),
            "lines of code · Python",
            12,
            f'fill="{MUTED}" text-anchor="end"',
        ),
    ]
    return document((WIDE, height), label, body)


@dataclass(frozen=True)
class Chart:
    """A chart: its frame (x, y, width, height), the run dates, its top value."""

    frame: tuple[int, int, int, int]
    dates: list[str]
    top: float
    unit: str = ""

    def x(self, index: int) -> float:
        """The x of the run at index; one run is drawn at the middle."""
        left, _, width, _ = self.frame
        if len(self.dates) == 1:
            return left + width / 2
        return left + index * width / (len(self.dates) - 1)

    def y(self, value: float) -> float:
        """The y of a value."""
        _, top, _, height = self.frame
        return top + height - height * value / self.top


def _axes(chart: Chart) -> list[str]:
    left, top, width, height = chart.frame
    parts = []
    for step in range(5):
        value = chart.top * step / 4
        y = chart.y(value)
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{left + width}" y2="{y:.1f}" '
            f'stroke="{GRID}"/>'
        )
        parts.append(
            text(
                (left - 6, y + 4),
                f"{value:g}{chart.unit}",
                10,
                f'fill="{MUTED}" text-anchor="end"',
            )
        )
    for index, date in enumerate(chart.dates):
        parts.append(
            text(
                (chart.x(index), top + height + 16),
                date,
                10,
                f'fill="{MUTED}" text-anchor="middle"',
            )
        )
    return parts


def _line(chart: Chart, series: Series) -> list[str]:
    points = [
        (chart.x(index), chart.y(value))
        for index, value in enumerate(series.values)
        if value is not None
    ]
    if not points:
        return []
    joined = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return [
        f'<polyline points="{joined}" fill="none" stroke="{series.color}" '
        'stroke-width="2"/>',
        *(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="{series.color}"/>'
            for x, y in points
        ),
    ]


def _legend(at: tuple[int, int], series: list[Series]) -> list[str]:
    x, y = at
    parts = []
    for one in series:
        parts.append(
            f'<rect x="{x}" y="{y - 9}" width="10" height="10" rx="2" '
            f'fill="{one.color}"/>'
        )
        parts.append(text((x + 15, y), one.name, 11))
        x += 30 + 7 * len(one.name)
    return parts


def issues_top(series: list[Series]) -> int:
    """The top of the issues scale: the highest value rounded up to 4, at least 4."""
    highest = max((v for s in series for v in s.values if v is not None), default=0)
    return max(4, math.ceil(highest / 4) * 4)


def activity(
    dates: list[str],
    issues: list[Series],
    coverage: Series,
    fail_under: float | None,
    label: str,
) -> str:
    """The activity card: issues and coverage over the last runs."""
    left = Chart((50, 74, 320, 130), dates, issues_top(issues))
    right = Chart((450, 74, 310, 130), dates, 100, "%")
    body = [
        card(WIDE, 228),
        text((20, 30), "Activity", 15, 'font-weight="600"'),
        text((20, 58), "Issues", 12, f'fill="{MUTED}" font-weight="600"'),
        *_legend((80, 58), issues),
        *_axes(left),
        *(part for series in issues for part in _line(left, series)),
        text((420, 58), "Coverage", 12, f'fill="{MUTED}" font-weight="600"'),
        *_axes(right),
        *_line(right, coverage),
    ]
    if fail_under is not None:
        y = right.y(fail_under)
        body += [
            f'<line x1="450" y1="{y:.1f}" x2="760" y2="{y:.1f}" stroke="{ORANGE}" '
            'stroke-dasharray="4 3"/>',
            text(
                (760, y - 5),
                f"fail_under {fail_under:g}%",
                10,
                f'fill="{ORANGE}" text-anchor="end"',
            ),
        ]
    return document((WIDE, 228), label, body)
