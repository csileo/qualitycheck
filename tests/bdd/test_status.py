import datetime as dt

from conftest import committed_copy, git, run_check
from pytest_bdd import given, parsers, scenarios, then, when

from qualitycheck.history import COLUMNS, append

scenarios("status.feature")

BRANCH = "qualitycheck-report"


def record(project, result: str = "PASS", days: int = 0) -> None:
    """Put one recorded check of HEAD on the report branch, as the check would."""
    date = dt.datetime.now().astimezone() - dt.timedelta(days=days)
    row = {
        **dict.fromkeys(COLUMNS, "0"),
        "date": date.isoformat(timespec="minutes"),
        "commit": git(project, "rev-parse", "HEAD"),
        "result": result,
    }
    path = project / "history.csv"
    path.write_text(append("", row), encoding="utf-8")
    blob = git(project, "hash-object", "-w", str(path))
    path.unlink()
    tree = git(project, "mktree", stdin=f"100644 blob {blob}\thistory.csv\n")
    commit = git(project, "commit-tree", tree, "-m", "record")
    git(project, "update-ref", f"refs/heads/{BRANCH}", commit)


def commits(project, count: int) -> None:
    for index in range(count):
        git(project, "commit", "-q", "--allow-empty", "-m", f"work {index}")


def fresh(tmp_path):
    return committed_copy("clean", tmp_path / "p")


@given("a project never checked", target_fixture="project")
def never_checked(tmp_path):
    return fresh(tmp_path)


@given("a project whose last check failed", target_fixture="project")
def last_failed(tmp_path):
    project = fresh(tmp_path)
    record(project, result="FAIL")
    return project


@given(
    parsers.re(r"a project checked (?P<count>\d+) commits ago$"),
    target_fixture="project",
)
def commits_ago(tmp_path, count):
    project = fresh(tmp_path)
    record(project)
    commits(project, int(count))
    return project


@given(
    parsers.re(r"a project checked (?P<days>\d+) days ago$"),
    target_fixture="project",
)
def days_ago(tmp_path, days):
    project = fresh(tmp_path)
    record(project, days=int(days))
    return project


@given(
    parsers.re(
        r"a project checked (?P<count>\d+) commits ago, (?P<days>\d+) days ago$"
    ),
    target_fixture="project",
)
def recent(tmp_path, count, days):
    project = fresh(tmp_path)
    record(project, days=int(days))
    commits(project, int(count))
    return project


def configure(project, setting: str, table: str) -> None:
    with (project / "pyproject.toml").open("a", encoding="utf-8") as file:
        file.write(f"\n{table}\n{setting}\n")
    git(project, "commit", "-qam", "configure qualitycheck")


@given(
    parsers.parse(
        'a project checked {count:d} commits ago with "{setting}" in "{table}"'
    ),
    target_fixture="project",
)
def configured_and_old(tmp_path, count, setting, table):
    project = fresh(tmp_path)
    configure(project, setting, table)
    record(project)
    commits(project, count)
    return project


@given(
    parsers.parse('a project with "{setting}" in "{table}"'),
    target_fixture="project",
)
def misconfigured(tmp_path, setting, table):
    project = fresh(tmp_path)
    configure(project, setting, table)
    return project


@when("I run the quality check status", target_fixture="status")
def status(project):
    return run_check(project, "--status")


@then(parsers.parse("it {outcome}"))
def outcome_is(status, outcome):
    output = status.stdout + status.stderr
    expected = {
        "warns that no check exists": "no quality check recorded yet",
        "warns that the last check failed": "the last quality check failed",
        "prints nothing": "",
    }
    if outcome == "prints nothing":
        assert output == ""
    elif outcome in expected:
        assert expected[outcome] in output, output
    elif outcome.startswith("warns that the check is "):
        age = outcome.removeprefix("warns that the check is ").removesuffix(" old")
        assert f"the last quality check is {age} old" in output, output
    elif outcome.startswith("warns that the settings are invalid"):
        assert "max_commits" in output
        assert "max_days" in output
    else:
        raise AssertionError(outcome)


@then("the exit code is 0")
def exit_zero(status):
    assert status.returncode == 0, status.stderr
