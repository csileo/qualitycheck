"""Run qualitycheck on test projects, copied into fresh repositories."""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

TEST_CASES = Path(__file__).resolve().parents[1] / "test-cases"
DATE = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?([+-]\d{2}:\d{2}|Z)?")
GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def git(cwd: Path, *args: str) -> str:
    """Run git in cwd with a test identity; return its output."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env={**os.environ, **GIT_IDENTITY},
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def run_check(project: Path, *args: str) -> subprocess.CompletedProcess:
    """Run qualitycheck in project with this environment's Python and tools."""
    return subprocess.run(
        [sys.executable, "-m", "qualitycheck", *args],
        cwd=project,
        env={**os.environ, **GIT_IDENTITY},
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
