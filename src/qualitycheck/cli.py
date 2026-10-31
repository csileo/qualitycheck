"""Command line: `qualitycheck` runs the check, `qualitycheck --status` reminds."""

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

from qualitycheck import gates, history, settings, tools
from qualitycheck.report import Run, render

REPORT_DIR = Path("docs") / "qualitycheck-report"
SETTINGS_ERROR = 2


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


def check(root: Path) -> int:
    """Run the check of the project at root; return the exit code."""
    try:
        own = settings.load(root)
    except settings.SettingsError as error:
        print(f"qualitycheck: {error}", file=sys.stderr)
        return SETTINGS_ERROR
    out = root / REPORT_DIR
    out.mkdir(parents=True, exist_ok=True)
    measures = tools.measure(root, out)
    judged = gates.evaluate(measures, own.fail_under)
    date = dt.datetime.now().astimezone().isoformat(timespec="minutes")
    run = Run(_head(root), date, gates.result(judged))
    path = out / "history.csv"
    previous = path.read_bytes().decode("utf-8") if path.exists() else ""
    text = history.append(previous, _row(run, measures, judged))
    report = render(run, judged, measures, history.parse(text))
    (out / "report.md").write_bytes(report.encode("utf-8"))
    path.write_bytes(text.encode("utf-8"))
    print(f"qualitycheck: {run.result} - {REPORT_DIR.as_posix()}/report.md")
    return 0 if run.result == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    """Run the command and return its exit code."""
    parser = argparse.ArgumentParser(prog="qualitycheck", description=__doc__)
    parser.parse_args(argv)
    return check(Path.cwd())


if __name__ == "__main__":
    sys.exit(main())
