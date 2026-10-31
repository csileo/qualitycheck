"""Test cases, test projects run in fresh repositories, and the shared steps.

Inputs in test-cases/<group>/<case>/input/, snapshots in output/.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from pytest_bdd import parsers, then, when
from syrupy.extensions.single_file import SingleFileSnapshotExtension, WriteMode

from qualitycheck.gates import Finding, Measures, PytestRun, Vulnerability

TEST_CASES = Path(__file__).resolve().parents[1] / "test-cases"
DATE = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?([+-]\d{2}:\d{2}|Z)?")
GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def git(cwd: Path, *args: str, stdin: str = "") -> str:
    """Run git in cwd with a test identity; return its output.

    stdin goes as bytes: text mode would turn its LF into CRLF on Windows.
    """
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env={**os.environ, **GIT_IDENTITY},
        input=stdin.encode("utf-8"),
        capture_output=True,
        check=True,
    )
    return result.stdout.decode("utf-8").strip()


def run_check(
    project: Path, *args: str, env: dict | None = None
) -> subprocess.CompletedProcess:
    """Run qualitycheck in project with this environment's Python and tools."""
    return subprocess.run(
        [sys.executable, "-m", "qualitycheck", *args],
        cwd=project,
        env={**os.environ, **GIT_IDENTITY, **(env or {})},
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def committed_copy(case: str, destination: Path) -> Path:
    """Copy the test project of case into destination, as a fresh repository."""
    shutil.copytree(TEST_CASES / "projects" / case / "input", destination)
    git(destination, "init", "-q", "-b", "main")
    git(destination, "add", "-A")
    git(destination, "commit", "-qm", "initial")
    return destination


def normalized(report: str, project: Path) -> str:
    """Replace the commit, the dates and Windows separators with fixed forms."""
    sha = git(project, "rev-parse", "HEAD")
    report = report.replace(sha, "<commit>").replace(sha[:10], "<commit>")
    return DATE.sub("<date>", report).replace("\\", "/")


REPORT = "docs/qualitycheck-report"


def report(project) -> str:
    return (project / REPORT / "report.md").read_text(encoding="utf-8")


def header(project) -> dict[str, str]:
    lines = report(project).split("\n## ", 1)[0].splitlines()
    pairs = (line[2:].split(": ", 1) for line in lines if line.startswith("- "))
    return dict(pairs)


def measures_from(data: dict) -> Measures:
    """Build Measures from a test case: a missing key means a clean project."""

    def items(key: str, kind: type) -> list | None:
        found = data.get(key, [])
        return None if found is None else [kind(*item) for item in found]

    tests = data.get("tests", {"returncode": 0, "summary": "1 passed"})
    return Measures(
        tests=None
        if tests is None
        else PytestRun(tests["returncode"], tests["summary"], tests.get("tail", "")),
        coverage=data.get("coverage", 90.0),
        lint=items("lint", Finding),
        vulnerabilities=items("vulnerabilities", Vulnerability),
        maintainability=data.get("maintainability", {"src/a.py": "A"}),
        duplicates=data.get("duplicates", []),
        sloc=data.get("sloc", 10),
        links=items("links", Finding),
        unchecked_links=data.get("unchecked_links", 0),
    )


def read(input_dir: Path, name: str) -> str:
    """Return a test case input as text."""
    return (input_dir / name).read_bytes().decode("utf-8")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "test_cases(group): run once per case in test-cases/<group>/"
    )


def pytest_generate_tests(metafunc):
    marker = metafunc.definition.get_closest_marker("test_cases")
    if marker:
        group = TEST_CASES / marker.args[0]
        case_dirs = sorted(path for path in group.iterdir() if path.is_dir())
        ids = [path.name for path in case_dirs]
        metafunc.parametrize("case_dir", case_dirs, ids=ids)


def _output_extension(output_dir: Path) -> type:
    class OutputFile(SingleFileSnapshotExtension):
        # Bytes, not text: written and compared exactly, LF on every OS.
        _write_mode = WriteMode.BINARY
        file_extension = "txt"

        def serialize(self, data, **kwargs) -> bytes:
            raw = data.encode("utf-8") if isinstance(data, str) else data
            return super().serialize(raw, **kwargs)

        def diff_lines(self, serialized_data, snapshot_data):
            # Compared as bytes, shown as text: a failure lists the changed lines.
            texts = (
                data.decode("utf-8", errors="replace")
                if isinstance(data, bytes)
                else data
                for data in (serialized_data, snapshot_data)
            )
            return super().diff_lines(*texts)

        @classmethod
        def dirname(cls, *, test_location) -> str:
            return str(output_dir)

        @classmethod
        def get_snapshot_name(cls, *, test_location, index=0) -> str:
            return "result"

    return OutputFile


@pytest.fixture
def case(case_dir, snapshot):
    """Return (input_dir, snapshot) of this case; the snapshot is output/result.txt."""
    extension = _output_extension(case_dir / "output")
    return case_dir / "input", snapshot.use_extension(extension)


@pytest.fixture(scope="session")
def checked(tmp_path_factory):
    """Return a function running the check once per case: (project, result)."""
    runs = {}

    def check(case: str) -> tuple[Path, subprocess.CompletedProcess]:
        if case not in runs:
            project = committed_copy(case, tmp_path_factory.mktemp(case) / "p")
            runs[case] = (project, run_check(project))
        return runs[case]

    return check


@when("I run the quality check", target_fixture="run")
def run(project_case, checked):
    if project_case["project"] is None:
        return checked(project_case["case"])
    project = project_case["project"]
    return project, run_check(project, env=project_case.get("env"))


@then(parsers.parse('the result is "{result}" and the exit code {code:d}'))
def result_and_code(run, result, code):
    project, process = run
    assert header(project)["Result"] == f"**{result}**"
    assert process.returncode == code, process.stdout + process.stderr
