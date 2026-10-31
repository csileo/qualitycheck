# qualitycheck

One local quality check of a Python project, published with the project itself: no CI, no server, no account.

## Install

In the checked project, as a dev dependency pinned to a tag:

```toml
[dependency-groups]
dev = ["qualitycheck @ git+https://github.com/csileo/qualitycheck@v0.1.0"]
```

The project ignores the report folder in git: add `docs/qualitycheck-report/` to `.gitignore`.

## Use

```sh
uv run qualitycheck           # run the check and publish it
uv run qualitycheck --status  # before a push: warn when the last check is missing, failed or stale
```

`uv run qualitycheck`, on a tree with no uncommitted change:

1. runs the tests with coverage, ruff, bandit, radon, pylint and the link check (lychee) on the whole project;
2. judges each gate: tests pass, no bug, no medium or high vulnerability, maintainability A in every file, no duplicated block, no function above the complexity limit, coverage at least `fail_under`, no broken link;
3. writes `report.md`, `images/`, `history.csv`, `coverage.xml`, `htmlcov/` and `bandit.html` to `docs/qualitycheck-report/`. `report.md` opens on a dashboard like Sonar's overview, drawn as SVG images that GitHub renders in public and private repositories alike ([ADR 0003](docs/adr/0003-report-as-markdown-with-svg-images.md)): the Quality Gate, the reliability, security and maintainability ratings, coverage, duplications, security hotspots and the activity of the last checks. The ratings follow Sonar and never change the result ([ADR 0004](docs/adr/0004-sonar-ratings-for-display-only.md));
4. publishes them on the `qualitycheck-report` branch, replaced at each check: one commit, no past versions, nothing committed on the checked branch ([ADR 0001](docs/adr/0001-publish-on-a-replaced-branch.md)). Offline, it only warns.

Exit codes: 0 PASS, 1 FAIL, 2 the check did not run or was not recorded (invalid settings, uncommitted changes, report folder not ignored, git unable to commit the report). `--status` always exits 0: it never blocks a push.

lychee is taken from `PATH`, else a pinned release is downloaded once into the user cache and checked against its SHA-256 ([ADR 0002](docs/adr/0002-pinned-lychee-download.md)); links listed in `.lycheeignore` are skipped.

## Configuration

The thresholds come from the project's own tool settings: rules and complexity limit from ruff (`max-complexity`, 10 by default), coverage from `[tool.coverage.report] fail_under`, duplication from pylint, security from `[tool.bandit]`. qualitycheck adds two settings of its own:

```toml
[tool.qualitycheck]
max_commits = 20  # --status warns when the last check is older than this many commits
max_days = 7      # ... or than this many days
```

## Development

Specs: [quality check](specs/001-quality-check/spec.md), [visual report](specs/002-visual-report/spec.md); [architecture](docs/architecture.md). Dev tooling from [commonreqs](https://github.com/csileo/commonreqs).

## License

[PolyForm Noncommercial 1.0.0](LICENSE).
