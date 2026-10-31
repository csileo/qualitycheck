import re

import pytest
from conftest import REPORT, git, measures_from, report
from pytest_bdd import given, parsers, scenarios, then, when

from qualitycheck import dashboard
from qualitycheck.gates import evaluate, result
from qualitycheck.report import Run, history_row

scenarios("visual-report.feature")

IMAGE = re.compile(r"!\[(?P<alt>[^\]]*)\]\(images/(?P<name>[^)]+)\.svg\)")
TILE = re.compile(r"\[!\[[^\]]*\]\(images/[^)]+\.svg\)\]\(#(?P<anchor>[^)]+)\)")
TITLE = re.compile(r"<title>(.*?)</title>", re.S)
NAME = 'the "(?P<name>[^"]+)"'
BUG_CODES = {"B": "B006", "F": "F401", "PLE": "PLE0101"}


def quoted(group: str) -> str:
    return f'"(?P<{group}>[^"]+)"'


def _items(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def _anchor(heading: str) -> str:
    """GitHub's anchor of a heading."""
    kept = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return kept.replace(" ", "-")


def _svg(request, name: str) -> str:
    try:
        drawn = request.getfixturevalue("drawn")
    except pytest.FixtureLookupError:
        project, _ = request.getfixturevalue("run")
        return (project / REPORT / "images" / f"{name}.svg").read_text("utf-8")
    return drawn[name].svg


def _title(request, name: str) -> str:
    return TITLE.search(_svg(request, name)).group(1)


def _dashboard(text: str) -> str:
    """The part of report.md between its header and its first section."""
    return text.split("\n## ", 1)[0].split("\n\n", 1)[1]


@given(
    parsers.re(r'bugs of the ruff families "(?P<families>[^"]*)"'),
    target_fixture="measures_data",
)
def bugs_of(families):
    codes = [BUG_CODES[family] for family in _items(families)]
    return {"lint": [["src/a.py", 1, code, "bug"] for code in codes]}


@given(
    parsers.re(r'vulnerabilities of severity and confidence "(?P<findings>[^"]*)"'),
    target_fixture="measures_data",
)
def vulnerabilities_of(findings):
    pairs = [item.split("/") for item in _items(findings)]
    found = [["src/a.py", 1, "B000", "x", severity, sure] for severity, sure in pairs]
    return {"vulnerabilities": found}


@given(
    parsers.parse("{smells:d} smells in {lines:d} lines of code"),
    target_fixture="measures_data",
)
def smells_in(smells, lines):
    return {"lint": [["src/a.py", 1, "E501", "long"]] * smells, "sloc": lines}


@given(
    parsers.parse(
        "duplicated blocks covering {duplicated:d} lines in {lines:d} lines of code"
    ),
    target_fixture="measures_data",
)
def duplicated_in(duplicated, lines):
    half = duplicated // 2
    block = (
        f"Similar lines in 2 files: demo.a:[0:{half}], demo.b:[0:{duplicated - half}]"
    )
    return {"duplicates": [block] if duplicated else [], "sloc": lines}


@given("measures where bandit is missing", target_fixture="measures_data")
def bandit_missing():
    return {"vulnerabilities": None}


@given(
    parsers.parse("measures with a coverage of {percent:g}% and no fail_under"),
    target_fixture="measures_data",
)
def coverage_without_threshold(percent):
    return {"coverage": percent, "fail_under": None}


@when("the report is drawn", target_fixture="drawn")
def draw(measures_data):
    measures = measures_from(measures_data)
    fail_under = measures_data.get("fail_under", 80)
    judged = evaluate(measures, fail_under)
    run = Run("a" * 40, "2026-10-31T10:00+01:00", result(judged))
    rows = [history_row(run, measures, judged)]
    images = dashboard.images(run, judged, measures, rows, fail_under)
    return {image.name: image for image in images}


@then(parsers.parse('"report.md" shows, right after its header, the images {names}'))
def dashboard_images(run, names):
    project, _ = run
    shown = [m["name"] for m in IMAGE.finditer(_dashboard(report(project)))]
    assert shown == re.findall(r'"([^"]+)"', names)


@then(parsers.parse('each of them is in "{folder}" and has an alternative text'))
def images_written(run, folder):
    project, _ = run
    for found in IMAGE.finditer(report(project)):
        svg = (project / folder / f"{found['name']}.svg").read_text("utf-8")
        assert found["alt"]
        assert TITLE.search(svg).group(1) == found["alt"]


@then(parsers.re(NAME + " image says " + quoted("word") + "$"))
def image_says(request, name, word):
    assert f">{word}<" in _svg(request, name)


@then(
    parsers.re(
        NAME
        + " image says "
        + quoted("word")
        + " and names "
        + quoted("condition")
        + "$"
    )
)
def image_says_and_names(request, name, word, condition):
    assert f">{word}<" in _svg(request, name)
    assert condition in _title(request, name)


@then(
    parsers.re(
        NAME + " image names " + quoted("condition") + " with " + quoted("reason") + "$"
    )
)
def image_names_with(request, name, condition, reason):
    assert f"{condition}: {reason}" in _title(request, name)


@then(
    parsers.re(
        NAME + " image shows the rating " + quoted("rating") + ' and a "Failed" badge$'
    )
)
def rating_and_badge(request, name, rating):
    assert f"rating {rating}" in _title(request, name)
    assert ">Failed<" in _svg(request, name)


@then(parsers.re(NAME + " image shows " + quoted("value") + " without rating$"))
def shows_without_rating(request, name, value):
    assert value in _title(request, name)
    assert "rating" not in _title(request, name)


@then(parsers.re(NAME + " image shows " + quoted("value") + ' without "Failed" badge$'))
def shows_without_badge(request, name, value):
    assert value in _title(request, name)
    assert ">Failed<" not in _svg(request, name)


@then(parsers.parse('the "{name}" image draws {count:d} checks'))
def draws_checks(request, name, count):
    assert f"last {count} checks" in _title(request, name)


@then(parsers.parse('the "{name}" image draws no threshold line'))
def no_threshold(request, name):
    assert "fail_under" not in _svg(request, name)


@then(parsers.parse('each tile of "{name}" links to a section of "{other}"'))
def tiles_link_to_sections(run, name, other):
    project, _ = run
    text = report(project)
    anchors = [m["anchor"] for m in TILE.finditer(text)]
    headings = re.findall(r"^## (.+)$", text, re.M)
    assert len(anchors) == 6
    assert set(anchors) <= {_anchor(heading) for heading in headings}


@then(parsers.parse('the branch "{branch}" holds "{folder}"'))
def branch_holds_folder(run, branch, folder):
    project, _ = run
    files = git(project, "ls-tree", "-r", "--name-only", branch).splitlines()
    assert any(f.startswith(folder) for f in files)


@then(parsers.parse('every image "{name}" links is on that branch'))
def linked_images_published(run, name):
    project, _ = run
    files = git(project, "ls-tree", "-r", "--name-only", "qualitycheck-report")
    text = git(project, "show", f"qualitycheck-report:{name}")
    for found in IMAGE.finditer(text):
        assert f"images/{found['name']}.svg" in files.splitlines()


@then(parsers.parse('the reliability rating is "{rating}"'))
def reliability_rating(request, rating):
    assert f"rating {rating}" in _title(request, "reliability")


@then(
    parsers.parse(
        'the security rating is "{rating}" and the security hotspots are {count:d}'
    )
)
def security_rating(request, rating, count):
    assert f"rating {rating}" in _title(request, "security")
    assert f"Security Hotspots: {count} to review" in _title(
        request, "security-hotspots"
    )


@then(
    parsers.parse(
        'the debt ratio is "{ratio}" and the maintainability rating "{rating}"'
    )
)
def maintainability_rating(request, ratio, rating):
    title = _title(request, "maintainability")
    assert f"rating {rating}" in title
    assert f"debt ratio {ratio}" in title


@then(parsers.parse('the duplications are "{percent}"'))
def duplications(request, percent):
    assert f"Duplications: {percent}" in _title(request, "duplications")
