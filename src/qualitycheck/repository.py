"""Git: refuse what a result cannot describe, then publish the report on its branch."""

import os
import subprocess
import tempfile
from pathlib import Path

BRANCH = "qualitycheck-report"
MESSAGE = "chore: record qualitycheck report"
REMOTE = "origin"
LOCAL_REF = f"refs/heads/{BRANCH}"
REMOTE_REF = f"refs/remotes/{REMOTE}/{BRANCH}"


class PublishError(RuntimeError):
    """Git could not record the report on its branch."""


def _git(
    root: Path, *args: str, env: dict | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        env={**os.environ, **(env or {})},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def refusal(root: Path, report_dir: Path) -> str | None:
    """Return why the check cannot run on this tree, or None."""
    status = _git(root, "status", "--porcelain", "--untracked-files=all")
    if status.returncode:
        return "not a git repository: the result must describe a commit."
    if status.stdout.strip():
        return (
            "commit or stash these changes first, the result must describe a commit:\n"
            + status.stdout.rstrip()
        )
    folder = report_dir.as_posix() + "/"
    if _git(root, "check-ignore", "-q", folder + "report.md").returncode:
        return f"add {folder} to .gitignore: the report must not change the tree."
    return None


def _has_remote(root: Path) -> bool:
    return REMOTE in _git(root, "remote").stdout.split()


def _longest_history(root: Path) -> str:
    """Return the history with the most rows, local or last fetched.

    A check that could not be pushed lives only on the local branch, so the
    longer one holds every recorded check.
    """
    shown = [
        _git(root, "show", f"{ref}:history.csv") for ref in (LOCAL_REF, REMOTE_REF)
    ]
    found = [process.stdout for process in shown if not process.returncode]
    return max(found, key=lambda text: len(text.splitlines()), default="")


def recorded_history(root: Path) -> str:
    """Return the longest history recorded here, without touching the network."""
    return _longest_history(root)


def commits_since(root: Path, commit: str) -> int | None:
    """Return the commits on HEAD after commit, or None if HEAD does not hold it."""
    counted = _git(root, "rev-list", "--count", f"{commit}..HEAD")
    holds = not _git(root, "merge-base", "--is-ancestor", commit, "HEAD").returncode
    return int(counted.stdout) if holds and not counted.returncode else None


def previous_history(root: Path) -> str:
    """Fetch the remote branch when there is one; return the longest history."""
    if _has_remote(root):
        _git(root, "fetch", "-q", REMOTE, f"+{LOCAL_REF}:{REMOTE_REF}")
    return _longest_history(root)


def _checked(process: subprocess.CompletedProcess) -> str:
    if process.returncode:
        raise PublishError(not_done("the report was not recorded", process.stderr))
    return process.stdout.strip()


def publish(root: Path, out: Path) -> str:
    """Replace the branch with one commit, without parent, holding out."""
    git_dir = _checked(_git(root, "rev-parse", "--absolute-git-dir"))
    with tempfile.TemporaryDirectory() as temporary:
        env = {"GIT_INDEX_FILE": str(Path(temporary) / "index")}
        base = ["--git-dir", git_dir, "--work-tree", str(out)]
        _checked(_git(out, *base, "add", "-A", "-f", ".", env=env))
        tree = _checked(_git(out, *base, "write-tree", env=env))
    commit = _checked(_git(root, "commit-tree", tree, "-m", MESSAGE))
    _checked(_git(root, "update-ref", LOCAL_REF, commit))
    return commit


def push(root: Path) -> str | None:
    """Push the branch, replacing the remote one; return a warning, or None."""
    if not _has_remote(root):
        return f"no remote {REMOTE}: the report stays on the local branch {BRANCH}."
    pushed = _git(root, "push", "-q", "--force", REMOTE, LOCAL_REF)
    if pushed.returncode:
        return (
            not_done("the report was not pushed", pushed.stderr)
            + f"; it stays on the local branch {BRANCH}."
        )
    return None


def not_done(what: str, stderr: str) -> str:
    """Return what failed, with the last line git gave as the reason, if any."""
    lines = stderr.strip().splitlines()
    return f"{what} ({lines[-1].strip()})" if lines else what
