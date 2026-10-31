"""Git: refuse what a result cannot describe, then publish the report on its branch."""

import os
import subprocess
import tempfile
from pathlib import Path

BRANCH = "qualitycheck-report"
MESSAGE = "chore: record qualitycheck report"
REMOTE = "origin"
REMOTE_REF = f"refs/remotes/{REMOTE}/{BRANCH}"


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


def previous_history(root: Path) -> str:
    """Return the history to continue: the remote's when fetched, else the local one."""
    fetched = (
        _has_remote(root)
        and not _git(
            root, "fetch", "-q", REMOTE, f"+refs/heads/{BRANCH}:{REMOTE_REF}"
        ).returncode
    )
    for ref in ([REMOTE_REF] if fetched else []) + [f"refs/heads/{BRANCH}"]:
        shown = _git(root, "show", f"{ref}:history.csv")
        if not shown.returncode:
            return shown.stdout
    return ""


def publish(root: Path, out: Path) -> str:
    """Replace the branch with one commit, without parent, holding out."""
    git_dir = _git(root, "rev-parse", "--absolute-git-dir").stdout.strip()
    with tempfile.TemporaryDirectory() as temporary:
        env = {"GIT_INDEX_FILE": str(Path(temporary) / "index")}
        base = ["--git-dir", git_dir, "--work-tree", str(out)]
        _git(out, *base, "add", "-A", "-f", ".", env=env)
        tree = _git(out, *base, "write-tree", env=env).stdout.strip()
    commit = _git(root, "commit-tree", tree, "-m", MESSAGE).stdout.strip()
    _git(root, "update-ref", f"refs/heads/{BRANCH}", commit)
    return commit


def push(root: Path) -> str | None:
    """Push the branch, replacing the remote one; return a warning, or None."""
    if not _has_remote(root):
        return f"no remote {REMOTE}: the report stays on the local branch {BRANCH}."
    pushed = _git(root, "push", "-q", "--force", REMOTE, f"refs/heads/{BRANCH}")
    if pushed.returncode:
        return (
            f"the report was not pushed ({pushed.stderr.strip().splitlines()[-1]}); "
            f"it stays on the local branch {BRANCH}."
        )
    return None
