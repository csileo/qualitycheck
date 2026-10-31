"""Settings: `[tool.qualitycheck]` and the thresholds of the project's own tools."""

import sys
from dataclasses import dataclass
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - Python 3.10
    import tomli as tomllib

DEFAULTS = {"max_commits": 20, "max_days": 7}


class SettingsError(ValueError):
    """An invalid `[tool.qualitycheck]`."""


@dataclass(frozen=True)
class Settings:
    """What the check reads from the project's `pyproject.toml`."""

    max_commits: int
    max_days: int
    fail_under: float | None


def _pyproject(root: Path) -> dict:
    path = root / "pyproject.toml"
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise SettingsError(f"pyproject.toml is not valid TOML: {error}.") from None


def _own(tool: dict) -> dict[str, int]:
    own = tool.get("qualitycheck", {})
    unknown = sorted(set(own) - set(DEFAULTS))
    if unknown:
        known = " and ".join(DEFAULTS)
        raise SettingsError(
            f"Unknown setting in [tool.qualitycheck]: {', '.join(unknown)}. "
            f"Use {known} only."
        )
    for key, value in own.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise SettingsError(
                f"[tool.qualitycheck] {key} must be a whole number above 0."
            )
    return {**DEFAULTS, **own}


def load(root: Path) -> Settings:
    """Read the settings of the project at root."""
    tool = _pyproject(root).get("tool", {})
    own = _own(tool)
    return Settings(
        max_commits=own["max_commits"],
        max_days=own["max_days"],
        fail_under=_fail_under(tool),
    )


def _fail_under(tool: dict) -> float | None:
    fail_under = tool.get("coverage", {}).get("report", {}).get("fail_under")
    if fail_under is None:
        return None
    try:
        return float(fail_under)
    except (TypeError, ValueError):
        raise SettingsError(
            "[tool.coverage.report] fail_under must be a number."
        ) from None
