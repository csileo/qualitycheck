from conftest import REPORT, committed_copy, git, run_check
from pytest_bdd import given, parsers, scenarios, then

scenarios("publish.feature")

BRANCH = "qualitycheck-report"


def with_remote(tmp_path, url: str | None = None):
    project = committed_copy("clean", tmp_path / "p")
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(remote))
    git(project, "remote", "add", "origin", url or str(remote))
    if url is None:
        git(project, "push", "-q", "origin", "main")
    return {
        "case": "clean",
        "project": project,
        "head": git(project, "rev-parse", "HEAD"),
    }


def branch_rows(project, ref: str = BRANCH) -> int:
    return len(git(project, "show", f"{ref}:history.csv").splitlines()) - 1


@given("a clean project with a remote", target_fixture="project_case")
def clean_with_remote(tmp_path):
    return with_remote(tmp_path)


@given("a clean project with a remote, checked twice", target_fixture="project_case")
def checked_twice(tmp_path):
    case = with_remote(tmp_path)
    for _ in range(2):
        assert run_check(case["project"]).returncode == 0
    return case


@given(
    parsers.parse(
        'a clean project whose remote "{branch}" holds {rows:d} rows, unknown locally'
    ),
    target_fixture="project_case",
)
def remote_only_history(tmp_path, branch, rows):
    case = with_remote(tmp_path)
    project = case["project"]
    for _ in range(rows):
        assert run_check(project).returncode == 0
    git(project, "branch", "-q", "-D", branch)
    git(project, "update-ref", "-d", f"refs/remotes/origin/{branch}")
    return case


@given(
    parsers.re(r"a clean project with (?P<change>a modified file|an untracked file)$"),
    target_fixture="project_case",
)
def dirty(tmp_path, change):
    case = with_remote(tmp_path)
    project = case["project"]
    if change == "a modified file":
        (project / "src/demo/core.py").write_text("x = 1\n", encoding="utf-8")
        case["changed"] = "src/demo/core.py"
    else:
        (project / "notes.txt").write_text("draft\n", encoding="utf-8")
        case["changed"] = "notes.txt"
    case["status"] = git(project, "status", "--porcelain")
    return case


@given(
    parsers.parse('a clean project that does not ignore "{folder}"'),
    target_fixture="project_case",
)
def not_ignored(tmp_path, folder):
    case = with_remote(tmp_path)
    project = case["project"]
    ignore = project / ".gitignore"
    kept = [
        line
        for line in ignore.read_text(encoding="utf-8").splitlines()
        if line != folder
    ]
    ignore.write_text("\n".join(kept) + "\n", encoding="utf-8")
    git(project, "commit", "-qam", "stop ignoring the report")
    return case


@given("a clean project whose remote cannot be reached", target_fixture="project_case")
def unreachable(tmp_path):
    return with_remote(tmp_path, url=str(tmp_path / "missing.git"))


@then(
    parsers.re(
        r'the branch "(?P<branch>[^"]+)" holds one commit'
        r'(, "(?P<message>[^"]+)", without parent)?$'
    )
)
def one_commit(run, branch, message):
    project, process = run
    assert git(project, "rev-list", "--count", branch) == "1", process.stderr
    if message:
        assert git(project, "log", "-1", "--format=%s", branch) == message
        assert git(project, "log", "-1", "--format=%P", branch) == ""


@then(parsers.parse("it holds {names}"))
def branch_holds(run, names):
    project, _ = run
    files = git(project, "ls-tree", "-r", "--name-only", BRANCH).splitlines()
    for name in [n.strip('"') for n in names.replace(" and ", ", ").split(", ")]:
        assert any(f == name or f.startswith(name) for f in files), name


@then(parsers.parse('the remote "{branch}" is that commit'))
def remote_is_local(run, branch):
    project, _ = run
    remote = git(project, "ls-remote", "origin", f"refs/heads/{branch}").split()[0]
    assert remote == git(project, "rev-parse", branch)


@then("the checked branch is unchanged")
def checked_branch_unchanged(run, project_case):
    project, _ = run
    assert git(project, "rev-parse", "HEAD") == project_case["head"]
    assert git(project, "status", "--porcelain") == ""


@then(parsers.parse('its "history.csv" has {rows:d} rows'))
def history_rows(run, rows):
    project, _ = run
    assert branch_rows(project) == rows


@then("it refuses to run, naming the uncommitted changes")
def refuses_dirty(run, project_case):
    _, process = run
    assert process.returncode == 2
    assert project_case["changed"] in process.stderr


@then("no file changed")
def nothing_written(run, project_case):
    project, _ = run
    assert git(project, "status", "--porcelain") == project_case["status"]
    assert not (project / REPORT).exists()


@then(parsers.parse('it refuses to run, saying to add "{folder}" to "{name}"'))
def refuses_not_ignored(run, folder, name):
    _, process = run
    assert process.returncode == 2
    assert folder in process.stderr
    assert name in process.stderr


@then("a warning says the result was not pushed")
def warns_not_pushed(run):
    _, process = run
    assert "not pushed" in process.stderr


@then(parsers.parse('the local branch "{branch}" holds the result'))
def local_branch_holds(run, branch):
    project, _ = run
    files = git(project, "ls-tree", "-r", "--name-only", branch).splitlines()
    assert "report.md" in files


@given(
    "a clean project with a remote, checked once online and once offline",
    target_fixture="project_case",
)
def checked_online_then_offline(tmp_path):
    case = with_remote(tmp_path)
    project = case["project"]
    assert run_check(project).returncode == 0
    url = git(project, "remote", "get-url", "origin")
    git(project, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    assert run_check(project).returncode == 0
    git(project, "remote", "set-url", "origin", url)
    return case


@given(
    "a clean project with a remote and no git identity", target_fixture="project_case"
)
def no_identity(tmp_path):
    case = with_remote(tmp_path)
    empty = {"GIT_AUTHOR_NAME": "", "GIT_COMMITTER_NAME": ""}
    case["env"] = {**empty, "GIT_AUTHOR_EMAIL": "", "GIT_COMMITTER_EMAIL": ""}
    return case


@then("it cannot run, saying the report was not recorded")
def not_recorded(run):
    _, process = run
    assert process.returncode == 2, process.stderr
    assert "report was not recorded" in process.stderr
