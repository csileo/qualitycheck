from qualitycheck.gates import (
    Finding,
    Measures,
    PytestRun,
    Vulnerability,
    evaluate,
    result,
)


def measures(**changes) -> Measures:
    base = {
        "tests": PytestRun(returncode=0, summary="1 passed", tail=""),
        "coverage": 90.0,
        "lint": [],
        "vulnerabilities": [],
        "maintainability": {"src/a.py": "A"},
        "duplicates": [],
        "sloc": 10,
    }
    return Measures(**{**base, **changes})


def statuses(m: Measures, fail_under: float | None = 80) -> dict[str, str]:
    return {gate.name: gate.status for gate in evaluate(m, fail_under)}


def test_clean_measures_pass():
    gates = evaluate(measures(), 80)
    assert all(gate.status == "PASS" for gate in gates)
    assert result(gates) == "PASS"


def test_bug_families_fail_but_not_their_lookalikes():
    lint = [Finding("src/a.py", 1, code, "") for code in ["BLE001", "E741", "PLR0913"]]
    assert statuses(measures(lint=lint))["bugs"] == "PASS"
    for code in ["F401", "B006", "PLE0101"]:
        bug = [Finding("src/a.py", 1, code, "")]
        assert statuses(measures(lint=bug))["bugs"] == "FAIL", code


def test_complexity_comes_from_ruff_c901():
    lint = [Finding("src/a.py", 1, "C901", "`f` is too complex (12 > 10)")]
    assert statuses(measures(lint=lint))["complexity"] == "FAIL"


def test_only_medium_and_high_vulnerabilities_fail():
    low = [Vulnerability("src/a.py", 1, "B101", "", "LOW")]
    medium = [Vulnerability("src/a.py", 1, "B307", "", "MEDIUM")]
    assert statuses(measures(vulnerabilities=low))["vulnerabilities"] == "PASS"
    assert statuses(measures(vulnerabilities=medium))["vulnerabilities"] == "FAIL"


def test_coverage_without_threshold_is_reported_only():
    assert statuses(measures(coverage=10.0), fail_under=None)["coverage"] == "n/a"
    assert statuses(measures(coverage=79.9))["coverage"] == "FAIL"
    assert statuses(measures(coverage=80.0))["coverage"] == "PASS"


def test_no_test_collected_fails():
    tests = PytestRun(returncode=5, summary="no tests ran", tail="")
    assert statuses(measures(tests=tests, coverage=None))["tests"] == "FAIL"


def test_a_missing_tool_fails_its_gate_and_names_it():
    gates = {gate.name: gate for gate in evaluate(measures(lint=None), 80)}
    assert gates["bugs"].status == "FAIL"
    assert "ruff" in gates["bugs"].detail


def test_maintainability_below_a_fails():
    m = measures(maintainability={"src/a.py": "A", "src/b.py": "C"})
    assert statuses(m)["maintainability"] == "FAIL"
    assert statuses(measures(maintainability={}))["maintainability"] == "n/a"
