"""Steps shared by the scenarios: run the check, read its result."""

from check_runs import header, run_check
from pytest_bdd import parsers, then, when


@when("I run the quality check", target_fixture="run")
def run(project_case, checked):
    if project_case["project"] is None:
        return checked(project_case["case"])
    project = project_case["project"]
    return project, run_check(project)


@then(parsers.parse('the result is "{result}" and the exit code {code:d}'))
def result_and_code(run, result, code):
    project, process = run
    assert header(project)["Result"] == f"**{result}**"
    assert process.returncode == code, process.stdout + process.stderr
