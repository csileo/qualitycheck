"""Gates: the tools' measures judged against the project's thresholds."""

import re
from dataclasses import dataclass

BUG = re.compile(r"^(F|B|PLE)\d")
COMPLEXITY = "C901"
SEVERE = {"MEDIUM", "HIGH"}
NO_TESTS = 5


@dataclass(frozen=True)
class Finding:
    """A ruff finding."""

    path: str
    line: int
    code: str
    message: str


@dataclass(frozen=True)
class Vulnerability:
    """A bandit finding."""

    path: str
    line: int
    code: str
    message: str
    severity: str


@dataclass(frozen=True)
class PytestRun:
    """The outcome of the test run."""

    returncode: int
    summary: str
    tail: str


@dataclass(frozen=True)
class Measures:
    """What the tools measured; None when the tool is missing."""

    tests: PytestRun | None
    coverage: float | None
    lint: list[Finding] | None
    vulnerabilities: list[Vulnerability] | None
    maintainability: dict[str, str] | None
    duplicates: list[str] | None
    sloc: int


@dataclass(frozen=True)
class Gate:
    """One gate: PASS, FAIL or n/a, with what decided it."""

    name: str
    status: str
    detail: str


def is_bug(finding: Finding) -> bool:
    """Tell whether a ruff finding belongs to a bug family."""
    return bool(BUG.match(finding.code))


def smells(lint: list[Finding] | None) -> list[Finding]:
    """Return the ruff findings that are neither bugs nor complexity."""
    return [f for f in lint or [] if not is_bug(f) and f.code != COMPLEXITY]


def bugs(lint: list[Finding] | None) -> list[Finding]:
    """Return the ruff findings of the bug families."""
    return [f for f in lint or [] if is_bug(f)]


def complex_functions(lint: list[Finding] | None) -> list[Finding]:
    """Return the functions above the complexity limit."""
    return [f for f in lint or [] if f.code == COMPLEXITY]


def severe(vulnerabilities: list[Vulnerability] | None) -> list[Vulnerability]:
    """Return the vulnerabilities of medium or high severity."""
    return [v for v in vulnerabilities or [] if v.severity in SEVERE]


def unmaintainable(maintainability: dict[str, str] | None) -> list[str]:
    """Return the files rated below A."""
    return [path for path, rank in (maintainability or {}).items() if rank != "A"]


def _missing(name: str, tool: str) -> Gate:
    return Gate(name, "FAIL", f"{tool} is missing from the environment")


def _count(name: str, items: list, noun: str) -> Gate:
    return Gate(name, "FAIL" if items else "PASS", f"{len(items)} {noun}")


def _tests(run: PytestRun | None) -> Gate:
    if run is None:
        return _missing("tests", "pytest")
    if run.returncode == NO_TESTS:
        return Gate("tests", "FAIL", "no test collected")
    return Gate("tests", "PASS" if run.returncode == 0 else "FAIL", run.summary)


def _coverage(percent: float | None, fail_under: float | None) -> Gate:
    if percent is None:
        return Gate("coverage", "n/a", "no coverage data")
    if fail_under is None:
        return Gate("coverage", "n/a", f"{percent:.1f}% (no fail_under)")
    status = "PASS" if percent >= fail_under else "FAIL"
    return Gate("coverage", status, f"{percent:.1f}% (fail_under {fail_under:g}%)")


def _maintainability(ranks: dict[str, str] | None) -> Gate:
    if ranks is None:
        return _missing("maintainability", "radon")
    if not ranks:
        return Gate("maintainability", "n/a", "no source file")
    return _count("maintainability", unmaintainable(ranks), "file(s) below A")


def evaluate(m: Measures, fail_under: float | None) -> list[Gate]:
    """Judge the measures, gate by gate."""
    lint = m.lint
    return [
        _tests(m.tests),
        _missing("bugs", "ruff")
        if lint is None
        else _count("bugs", bugs(lint), "bug(s)"),
        _missing("vulnerabilities", "bandit")
        if m.vulnerabilities is None
        else _count("vulnerabilities", severe(m.vulnerabilities), "medium or high"),
        _maintainability(m.maintainability),
        _missing("duplication", "pylint")
        if m.duplicates is None
        else _count("duplication", m.duplicates, "duplicated block(s)"),
        _missing("complexity", "ruff")
        if lint is None
        else _count("complexity", complex_functions(lint), "function(s) too complex"),
        _coverage(m.coverage, fail_under),
    ]


def result(gates: list[Gate]) -> str:
    """PASS when no gate fails."""
    return "FAIL" if any(gate.status == "FAIL" for gate in gates) else "PASS"
