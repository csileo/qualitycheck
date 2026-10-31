from conftest import committed_copy, git, header, report
from pytest_bdd import given, parsers, scenarios, then

scenarios("links.feature")


def with_readme(tmp_path, ignored: str | None = None) -> dict:
    project = committed_copy("clean", tmp_path / "p")
    readme = "# Demo\n\n[Guide](missing.md)\n"
    (project / "README.md").write_text(readme, encoding="utf-8")
    if ignored:
        (project / ignored).write_text("missing\\.md\n", encoding="utf-8")
    git(project, "add", "-A")
    git(project, "commit", "-qm", "add a README")
    return {"case": "clean", "project": project}


@given(
    "a clean project whose README links to a missing page",
    target_fixture="project_case",
)
def broken_link(tmp_path):
    return with_readme(tmp_path)


@given(
    parsers.parse(
        'a clean project whose README links to a missing page listed in "{name}"'
    ),
    target_fixture="project_case",
)
def ignored_link(tmp_path, name):
    return with_readme(tmp_path, ignored=name)


@given("no network, with lychee not downloaded yet")
def no_network(project_case, tmp_path):
    unreachable = "http://127.0.0.1:9"
    project_case["env"] = {
        "QUALITYCHECK_CACHE": str(tmp_path / "empty-cache"),
        "HTTPS_PROXY": unreachable,
        "HTTP_PROXY": unreachable,
    }


@then(
    parsers.parse(
        'the result is "{result}" and the report names the failed gate "{gate}"'
    )
)
def fails_on(run, result, gate):
    project, _ = run
    assert header(project)["Result"] == f"**{result}**"
    assert f"| {gate} | FAIL |" in report(project)


@then(parsers.parse('the result is "{result}"'))
def result_only(run, result):
    project, process = run
    assert header(project)["Result"] == f"**{result}**", process.stderr


@then(
    parsers.parse(
        'the result is "{result}" and the report warns that links were not checked'
    )
)
def warns_unchecked(run, result):
    project, _ = run
    assert header(project)["Result"] == f"**{result}**"
    assert "| links | n/a | lychee unavailable" in report(project)
