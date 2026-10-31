# Implementation Plan: One local quality check, published with the project

**Branch**: `main` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

## Summary

A Python package with one console script, `qualitycheck`, run in the checked project's environment. A functional core turns the tools' JSON outputs into gates, a result, a report and a history row; an imperative shell runs the tools, reads the settings and drives git. Adapted from SimToReal3's `run_audit.py`: same tools and ratings, English, whole-project gates, no new-code gate.

## Technical Context

- Python ≥ 3.10; `tomli` below 3.11 to read `pyproject.toml`.
- Runtime dependencies, as wide ranges so they follow the checked project's own: ruff, bandit[toml], radon, pylint, pytest, pytest-cov.
- Dev: pytest, pytest-bdd, syrupy, ruff.
- Tools are run as `sys.executable -m <tool>`: the checked project's environment, where `uv run qualitycheck` starts.

## Research

- **R1 Gates from the project's settings**: ruff runs with the project's configuration plus `--extend-select F,B,PLE,C901`, so the bug and complexity gates hold even when a project selects fewer rules; ruff reads `max-complexity` itself (default 10). Bandit runs with `-c pyproject.toml -r src tests`. Pylint reads `[tool.pylint]` itself. Coverage: pytest runs with `--cov=src --cov-fail-under=0`, so a failed test and a low coverage stay apart; the threshold is read from `[tool.coverage.report] fail_under`.
- **R2 Link check**: lychee is not on PyPI (the `lychee` package there is a blog generator). Like lychee's own pre-commit hook, qualitycheck downloads a pinned release binary for the platform into the user cache, once; lychee on `PATH` wins. Offline with no binary, or network errors only: a warning. HTTP 4xx (but 429) and missing local files: broken links. `.lycheeignore` is read by lychee itself.
- **R3 Publishing without touching the checked branch**: a temporary index (`GIT_INDEX_FILE`) and `--work-tree=docs/qualitycheck-report`: `git add -A`, `git write-tree`, `git commit-tree` (no parent), `git update-ref refs/heads/qualitycheck-report`, `git push --force origin qualitycheck-report`. The working tree, the index and HEAD of the checked branch never change. Before the check: `git fetch origin qualitycheck-report`; the history continues from the remote ref when fetched, else from the local branch.
- **R4 Dirty tree and ignored outputs**: `git status --porcelain` empty, untracked files included; `git check-ignore -q docs/qualitycheck-report/`.
- **R5 Status without network**: `git show qualitycheck-report:history.csv`, else `origin/qualitycheck-report:history.csv`; commits since the tested commit with `git rev-list --count <tested>..HEAD`, days from the run date.
- **R6 Settings errors**: unknown keys in `[tool.qualitycheck]` stop the check (exit 2); `--status` prints the error and still exits 0.
- **R7 Tests**: test projects in `test-cases/projects/<case>/input/` (pytest `pythonpath = ["src"]`, so no install), copied to a temporary folder and committed in a fresh repository; qualitycheck runs with the test environment's Python, which has every tool. A bare repository plays the remote. Reports are compared as syrupy snapshots in `output/`, with the commit and dates replaced by placeholders. Network-dependent link scenarios use local file links; the offline one runs lychee against an unreachable address.

## Design

| Module | Role |
|---|---|
| `settings.py` | read `[tool.qualitycheck]`, `fail_under`; reject unknown keys |
| `tools.py` | run ruff, bandit, radon, pylint, pytest, lychee; return parsed outputs (shell) |
| `lychee.py` | find or download the pinned binary (shell) |
| `gates.py` | findings → gates → result (core) |
| `report.py` | render `report.md` (core) |
| `history.py` | parse and append `history.csv`, last passing run (core) |
| `repository.py` | dirty tree, ignored outputs, fetch, publish, push (shell) |
| `status.py` | staleness from history and git (core + small shell) |
| `cli.py` | `qualitycheck`, `qualitycheck --status`; exit codes |

## Constitution Check

| Rule | Status |
|---|---|
| ADR before implementing | ADR 0001 (publish on a replaced branch), ADR 0002 (pinned lychee download) |
| TDD, BDD | each story's feature red first |
| Test cases | test projects and report snapshots in `test-cases/` |
| Complexity ≤ 15, 5 arguments | ruff settings in `pyproject.toml` |
| Functional core, imperative shell | `gates`, `report`, `history`, `status` hold no I/O |

## Complexity Tracking

None.
