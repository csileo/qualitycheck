"""Run the checked project's tools, in its own environment, and parse their outputs."""

import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET  # nosec B405 - parses the coverage.xml just written
from pathlib import Path

from qualitycheck.gates import Finding, Measures, PytestRun, Vulnerability

CODE_DIRS = ["src", "tests"]
TIMING = re.compile(r" in \d+(\.\d+)?s( \([^)]*\))?")
# pytest-cov's own lines: machine paths and platform, no test information.
COVERAGE_LINES = re.compile(
    r"^(=+ tests coverage =+|_+ coverage: .*|Coverage (HTML|XML) written .*)$"
)
TAIL = 3000


def _run(
    root: Path, *args: str, env: dict | None = None
) -> subprocess.CompletedProcess | None:
    """Run `python -m args` in root; None when the module is missing."""
    process = subprocess.run(
        [sys.executable, "-m", *args],
        cwd=root,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if process.returncode and "No module named" in process.stderr:
        return None
    return process


def _relative(root: Path, path: str) -> str:
    try:
        return Path(path).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def _loads(text: str, default):
    try:
        return json.loads(text) if text.strip() else default
    except json.JSONDecodeError:
        return default


def lint(root: Path, dirs: list[str]) -> list[Finding] | None:
    """Ruff with the project's rules, plus the bug and complexity families."""
    if not dirs:
        return []
    options = ["--no-cache", "--exit-zero", "--output-format", "json"]
    extra = ["--extend-select", "F,B,PLE,C901"]
    process = _run(root, "ruff", "check", *options, *extra, *dirs)
    if process is None:
        return None
    return [
        Finding(
            _relative(root, item["filename"]),
            item["location"]["row"],
            item.get("code") or "?",
            item["message"],
        )
        for item in _loads(process.stdout, [])
    ]


def vulnerabilities(
    root: Path, dirs: list[str], out: Path
) -> list[Vulnerability] | None:
    """Bandit with the project's settings; also writes bandit.html."""
    if not dirs:
        return []
    config = ["-c", "pyproject.toml"] if (root / "pyproject.toml").exists() else []
    command = ["bandit", "-q", *config, "-r", *dirs]
    process = _run(root, *command, "-f", "json")
    if process is None:
        return None
    _run(root, *command, "-f", "html", "-o", str(out / "bandit.html"))
    return [
        Vulnerability(
            _relative(root, item["filename"]),
            item["line_number"],
            item["test_id"],
            item["issue_text"],
            item["issue_severity"].upper(),
        )
        for item in _loads(process.stdout, {}).get("results", [])
    ]


def maintainability(root: Path) -> tuple[dict[str, str] | None, int]:
    """Radon: the maintainability rank of each source file, and the lines of code."""
    if not (root / "src").is_dir():
        return {}, 0
    ranks = _run(root, "radon", "mi", "-j", "src")
    raw = _run(root, "radon", "raw", "-j", "src")
    if ranks is None or raw is None:
        return None, 0
    files = _loads(ranks.stdout, {})
    sloc = sum(item.get("sloc", 0) for item in _loads(raw.stdout, {}).values())
    return {
        _relative(root, path): item["rank"]
        for path, item in files.items()
        if isinstance(item, dict) and "rank" in item
    }, sloc


def duplicates(root: Path) -> list[str] | None:
    """Pylint's duplicated blocks, with the project's similarity settings."""
    if not (root / "src").is_dir():
        return []
    options = ["--disable=all", "--enable=duplicate-code", "-f", "json"]
    process = _run(root, "pylint", "src", *options)
    if process is None:
        return None
    return [
        _duplicate(item["message"])
        for item in _loads(process.stdout, [])
        if item.get("symbol") == "duplicate-code"
    ]


def _duplicate(message: str) -> str:
    """Turn pylint's message into "Similar lines in 2 files: a:[1:8], b:[1:8]"."""
    lines = message.splitlines()
    places = [line[2:] for line in lines if line.startswith("==")]
    return f"{lines[0]}: {', '.join(places)}"


def _coverage_percent(xml: Path) -> float | None:
    if not xml.exists():
        return None
    root = ET.parse(xml).getroot()  # nosec B314 - written by coverage just before
    valid = int(root.get("lines-valid", 0)) + int(root.get("branches-valid", 0))
    covered = int(root.get("lines-covered", 0)) + int(root.get("branches-covered", 0))
    return round(covered / valid * 100, 1) if valid else None


def _untimed(text: str) -> str:
    lines = (TIMING.sub("", line) for line in text.splitlines())
    return "\n".join(line for line in lines if not COVERAGE_LINES.match(line))


def tests(root: Path, out: Path) -> tuple[PytestRun | None, float | None]:
    """Pytest with coverage of src/, writing coverage.xml and htmlcov/."""
    xml = out / "coverage.xml"
    reports = [f"--cov-report=xml:{xml}", f"--cov-report=html:{out / 'htmlcov'}"]
    with tempfile.TemporaryDirectory() as data:
        process = _run(
            root,
            *["pytest", "-q", "-p", "no:cacheprovider", "--cov=src", *reports],
            "--cov-fail-under=0",
            env={"COVERAGE_FILE": str(Path(data) / ".coverage")},
        )
    if process is None:
        return None, None
    output = _untimed(process.stdout)
    lines = [line for line in output.splitlines() if line.strip()]
    summary = lines[-1].strip("= ") if lines else "no output"
    return PytestRun(process.returncode, summary, output[-TAIL:]), _coverage_percent(
        xml
    )


def measure(root: Path, out: Path) -> Measures:
    """Run every tool on the project at root; outputs go to out."""
    dirs = [name for name in CODE_DIRS if (root / name).is_dir()]
    test_run, coverage = tests(root, out)
    ranks, sloc = maintainability(root)
    return Measures(
        tests=test_run,
        coverage=coverage,
        lint=lint(root, dirs),
        vulnerabilities=vulnerabilities(root, dirs, out),
        maintainability=ranks,
        duplicates=duplicates(root),
        sloc=sloc,
    )
