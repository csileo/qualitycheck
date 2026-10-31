import datetime as dt

from qualitycheck.status import reminder

NOW = dt.datetime(2026, 10, 31, 12, 0, tzinfo=dt.timezone.utc)
LIMITS = (20, 7)


def row(result: str = "PASS", days: int = 0) -> dict[str, str]:
    date = (NOW - dt.timedelta(days=days)).isoformat(timespec="minutes")
    return {"date": date, "commit": "a" * 40, "result": result}


def test_fresh_passing_check_says_nothing():
    assert reminder([row(days=7)], 20, NOW, LIMITS) is None


def test_missing_failed_and_stale_checks_warn():
    assert "no quality check recorded yet" in reminder([], 0, NOW, LIMITS)
    assert "failed" in reminder([row("FAIL")], 0, NOW, LIMITS)
    assert "21 commits old" in reminder([row()], 21, NOW, LIMITS)
    assert "8 days old" in reminder([row(days=8)], 0, NOW, LIMITS)
    assert "not in this history" in reminder([row()], None, NOW, LIMITS)


def test_only_the_last_row_counts():
    assert reminder([row("FAIL"), row()], 0, NOW, LIMITS) is None
