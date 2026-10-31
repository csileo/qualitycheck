from qualitycheck.gates import Gate, Measures
from qualitycheck.report import Run, render

MEASURES = Measures(
    tests=None,
    coverage=None,
    lint=[],
    vulnerabilities=[],
    maintainability={},
    duplicates=[],
    sloc=0,
)
GATES = [Gate("tests", "FAIL", "pytest is missing from the environment")]


def test_first_run_has_no_last_pass():
    text = render(Run("a" * 40, "2026-10-31T10:00+01:00", "FAIL"), GATES, MEASURES, [])
    assert "- Last passing commit: none yet\n" in text
    assert "| tests | FAIL | pytest is missing from the environment |" in text


def test_last_pass_comes_from_the_history():
    rows = [{"commit": "b" * 40, "date": "2026-10-30T09:00+01:00", "result": "PASS"}]
    text = render(
        Run("a" * 40, "2026-10-31T10:00+01:00", "FAIL"), GATES, MEASURES, rows
    )
    assert f"- Last passing commit: `{'b' * 10}`, 2026-10-30T09:00+01:00\n" in text
