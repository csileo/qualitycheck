"""Command line: `qualitycheck` runs the check, `qualitycheck --status` reminds."""

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

from qualitycheck import dashboard, gates, history, repository, settings, status, tools
from qualitycheck.report import Run, history_row, render

REPORT_DIR = Path("docs") / "qualitycheck-report"
# Invalid settings, a tree the result could not describe, or a report git
# could not record.
CANNOT_RUN = 2


def _head(root: Path) -> str:
    process = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return process.stdout.strip() or "unknown"


def _warn(message: str) -> None:
    print(f"qualitycheck: {message}", file=sys.stderr)


def _settings(root: Path) -> settings.Settings | None:
    try:
        own = settings.load(root)
    except settings.SettingsError as error:
        _warn(str(error))
        return None
    refused = repository.refusal(root, REPORT_DIR)
    if refused:
        _warn(refused)
        return None
    return own


def _fresh_output(root: Path) -> Path:
    out = root / REPORT_DIR
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    return out


def _write_images(folder: Path, images: list[dashboard.Image]) -> None:
    folder.mkdir()
    for image in images:
        (folder / f"{image.name}.svg").write_bytes(image.svg.encode("utf-8"))


def check(root: Path) -> int:
    """Run the check of the project at root, publish it; return the exit code."""
    own = _settings(root)
    if own is None:
        return CANNOT_RUN
    previous = repository.previous_history(root)
    out = _fresh_output(root)
    measures = tools.measure(root, out)
    judged = gates.evaluate(measures, own.fail_under)
    date = dt.datetime.now().astimezone().isoformat(timespec="minutes")
    run = Run(_head(root), date, gates.result(judged))
    text = history.append(previous, history_row(run, measures, judged))
    rows = history.parse(text)
    images = dashboard.images(run, judged, measures, rows, own.fail_under)
    _write_images(out / "images", images)
    report = render(run, judged, measures, rows, dashboard.markdown(images))
    (out / "report.md").write_bytes(report.encode("utf-8"))
    (out / "history.csv").write_bytes(text.encode("utf-8"))
    try:
        repository.publish(root, out)
    except repository.PublishError as error:
        _warn(str(error))
        return CANNOT_RUN
    warning = repository.push(root)
    if warning:
        _warn(warning)
    print(f"qualitycheck: {run.result} - {REPORT_DIR.as_posix()}/report.md")
    return 0 if run.result == "PASS" else 1


def remind(root: Path) -> int:
    """Warn when the last recorded check is missing, failed or stale; never fail."""
    try:
        own = settings.load(root)
    except settings.SettingsError as error:
        _warn(str(error))
        return 0
    rows = history.parse(repository.recorded_history(root))
    since = repository.commits_since(root, rows[-1]["commit"]) if rows else 0
    now = dt.datetime.now().astimezone()
    warning = status.reminder(rows, since, now, (own.max_commits, own.max_days))
    if warning:
        _warn(warning)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the command and return its exit code."""
    parser = argparse.ArgumentParser(prog="qualitycheck", description=__doc__)
    parser.add_argument(
        "--status",
        action="store_true",
        help="warn, before a push, when the last check is missing, failed or stale",
    )
    arguments = parser.parse_args(argv)
    root = Path.cwd()
    return remind(root) if arguments.status else check(root)


if __name__ == "__main__":
    sys.exit(main())
