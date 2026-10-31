"""Run a program and keep its output as text, whatever it prints."""

import os
import subprocess
from pathlib import Path


def run(
    command: list[str], cwd: Path, env: dict | None = None
) -> subprocess.CompletedProcess:
    """Run command in cwd with extra env; a failure is a result, never an error."""
    return subprocess.run(
        command,
        cwd=cwd,
        env={**os.environ, **(env or {})},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
