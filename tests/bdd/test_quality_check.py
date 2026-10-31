import re

from check_runs import REPORT, committed_copy, git, header, report, run_check
from pytest_bdd import given, parsers, scenarios, then

scenarios("quality-check.feature")


@given(
    parsers.re(r'the project "test-cases/projects/(?P<case>[^/]+)/input"$'),
    target_fixture="project_case",
)
def project_case(case):
    return {"case": case, "project": None}


@given(
    parsers.parse(
        'the project "test-cases/projects/{case}/input" '
        "with ruff's max-complexity set to {limit:d}"
    ),
    target_fixture="project_case",
)
def project_with_limit(tmp_path, case, limit):
    project = committed_copy(case, tmp_path / "p")
    with (project / "pyproject.toml").open("a", encoding="utf-8") as file:
        file.write(f"\n[tool.ruff.lint.mccabe]\nmax-complexity = {limit}\n")
    git(project, "commit", "-qam", "raise the complexity limit")
    return {"case": case, "project": project}


@given("a project whose last check passed", target_fixture="project_case")
def checked_once(tmp_path):
    project = committed_copy("clean", tmp_path / "p")
    assert run_check(project).returncode == 0
    return {
        "case": "clean",
        "project": project,
        "first": git(project, "rev-parse", "HEAD"),
    }


@given("a commit that breaks a test")
def break_a_test(project_case):
    project = project_case["project"]
    test = project / "tests" / "test_core.py"
    test.write_text(
        test.read_text(encoding="utf-8").replace("== 5", "== 6"), encoding="utf-8"
    )
    git(project, "commit", "-qam", "break a test")


@then(parsers.parse('"{folder}" holds {names}'))
def folder_holds(run, folder, names):
    project, _ = run
    for name in re.findall(r'"([^"]+)"', names):
        assert (project / folder / name).exists(), name


@then(
    parsers.parse(
        'the report header gives the tested commit, the date, "{result}" '
        "and the last passing commit"
    )
)
def header_gives(run, result):
    project, _ = run
    sha = git(project, "rev-parse", "HEAD")[:10]
    fields = header(project)
    assert fields["Tested commit"] == f"`{sha}`"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}[+-]\d{2}:\d{2}", fields["Date"])
    assert fields["Result"] == f"**{result}**"
    assert fields["Last passing commit"] == f"`{sha}`, {fields['Date']}"


@then(parsers.parse('the report names the failed gate "{gate}"'))
def failed_gate(run, gate):
    project, _ = run
    assert re.search(rf"^\| {gate} \| FAIL \|", report(project), re.MULTILINE)


@then("the report lists the smell")
def lists_smell(run):
    project, _ = run
    assert "E741" in report(project)


@then(
    parsers.parse(
        'the report header gives "{result}" '
        "and the earlier passing commit with its date"
    )
)
def keeps_last_pass(run, project_case, result):
    project, _ = run
    fields = header(project)
    assert fields["Result"] == f"**{result}**"
    commit, date = fields["Last passing commit"].split(", ")
    assert commit == f"`{project_case['first'][:10]}`"
    assert date != fields["Date"] or date
    history = (project / REPORT / "history.csv").read_text(encoding="utf-8")
    assert project_case["first"] in history


@then(parsers.parse('"{name}" has one more row'))
def one_more_row(run, name):
    project, _ = run
    rows = (project / REPORT / name).read_text(encoding="utf-8").splitlines()
    assert len(rows) == 3
