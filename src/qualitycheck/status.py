"""The reminder before a push: is the last recorded check missing, failed or stale?"""

import datetime as dt

ADVICE = "run `uv run qualitycheck`."


def reminder(
    rows: list[dict[str, str]],
    commits_since: int | None,
    now: dt.datetime,
    limits: tuple[int, int],
) -> str | None:
    """Return the warning for the last recorded check, or None when it is fine.

    limits is (max_commits, max_days); commits_since is None when the tested
    commit is not in the current history.
    """
    if not rows:
        return f"no quality check recorded yet: {ADVICE}"
    last = rows[-1]
    if last.get("result") != "PASS":
        return f"the last quality check failed ({last['commit'][:10]}): {ADVICE}"
    max_commits, max_days = limits
    problems = []
    if commits_since is None:
        problems.append("the last quality check is on a commit not in this history")
    elif commits_since > max_commits:
        age = f"{commits_since} commits old (limit {max_commits})"
        problems.append(f"the last quality check is {age}")
    days = (now - dt.datetime.fromisoformat(last["date"])).days
    if days > max_days:
        problems.append(f"the last quality check is {days} days old (limit {max_days})")
    return f"{'; '.join(problems)}: {ADVICE}" if problems else None
