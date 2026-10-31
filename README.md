# qualitycheck

One local quality check of a Python project, published with the project itself: no CI, no server, no account.

Status: specified, not yet built ([spec](specs/001-quality-check/spec.md)).

```sh
uv run qualitycheck
```

It runs the tests with coverage, the linters and the link check, and writes the report to `docs/audit/` (ignored by git). It then publishes it on the `quality-report` branch, replaced at each check: one commit, no past versions, nothing committed on the checked branch.

## Configuration

In the checked project's `pyproject.toml`:

```toml
[tool.qualitycheck]
max_commits = 20  # warn before a push (qualitycheck --status) when the last check is older than this many commits
max_days = 7      # ... or than this many days
```

The thresholds come from the project's own tool settings: complexity from ruff, coverage from `[tool.coverage.report] fail_under`, duplication from pylint.

## License

[PolyForm Noncommercial 1.0.0](LICENSE).
