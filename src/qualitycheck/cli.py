"""Command line: `qualitycheck` runs the check, `qualitycheck --status` reminds."""

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

from qualitycheck import gates, history, repository, settings, tools
from qualitycheck.report import Run, render

REPORT_DIR = Path("docs") / "qualitycheck-report"
# Invalid settings, or a tree the result could not describe.
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


def _row(run: Run, m: gates.Measures, judged: list[gates.Gate]) -> dict[str, str]:
    status = {gate.name: gate.status for gate in judged}
    return {
        "date": run.date,
        "commit": run.commit,
        "result": run.result,
        "tests": status["tests"],
        "bugs": str(len(gates.bugs(m.lint))),
        "vulnerabilities": str(len(gates.severe(m.vulnerabilities))),
        "smells": str(len(gates.smells(m.lint))),
        "complex_functions": str(len(gates.complex_functions(m.lint))),
        "duplicated_blocks": str(len(m.duplicates or [])),
        "coverage": "" if m.coverage is None else f"{m.coverage:.1f}",
        "sloc": str(m.sloc),
    }


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
    text = history.append(previous, _row(run, measures, judged))
    report = render(run, judged, measures, history.parse(text))
    (out / "report.md").write_bytes(report.encode("utf-8"))
    (out / "history.csv").write_bytes(text.encode("utf-8"))
    repository.publish(root, out)
    warning = repository.push(root)
    if warning:
        _warn(warning)
    print(f"qualitycheck: {run.result} - {REPORT_DIR.as_posix()}/report.md")
    return 0 if run.result == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    """Run the command and return its exit code."""
    parser = argparse.ArgumentParser(prog="qualitycheck", description=__doc__)
    parser.parse_args(argv)
    return check(Path.cwd())


if __name__ == "__main__":
    sys.exit(main())
