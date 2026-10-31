# qualitycheck

One local quality check of a Python project, recorded in the project itself: no CI, no server, no account.

Status: specified, not yet built ([spec](specs/001-quality-check/spec.md)).

```sh
uv run qualitycheck
```

It runs the tests with coverage, the linters and the link check, writes `docs/audit/report.md`, appends a row to `docs/audit/history.csv`, then commits and pushes the result.

## Configuration

In the checked project's `pyproject.toml`:

```toml
[tool.qualitycheck]
max_commits = 20  # warn before a push when the last check is older than this many commits
max_days = 7      # ... or than this many days
```

The thresholds come from the project's own tool settings: complexity from ruff, coverage from `[tool.coverage.report] fail_under`, duplication from pylint.

## License

[PolyForm Noncommercial 1.0.0](LICENSE).
