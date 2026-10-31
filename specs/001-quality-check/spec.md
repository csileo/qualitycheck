# Feature Specification: One local quality check, published with the project

**Feature Branch**: `main`

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "A separate public package, run with `uv run qualitycheck` in the checked project, replacing CI. Configuration `[tool.qualitycheck]` with only `max_commits` and `max_days`; complexity read from the ruff configuration. Outputs `report.md` in English (header: tested commit, date, result, last passing commit and its date), `history.csv`, `htmlcov`, `coverage.xml`, `bandit.html`. Refuses a dirty tree; offline, warns without failing. The link check moves into it, with a per-project `.lycheeignore`. A pre-push hook warns and never blocks. Adapted from SimToReal3's `run_audit.py`." Amended: the outputs are published on a branch replaced at each check, with no history; nothing is committed on the checked branch.

## User Stories *(mandatory)*

### US-01 - Check the project's quality in one command (Priority: P1)

**As a** project owner **I want** one local command that runs every quality check and writes one report **so that** I know where the project stands without CI, a server or an account.

**Business rules**:
- `uv run qualitycheck`, run at the root of the checked project, runs the tests with coverage, then the checks below, on the whole project.
- The result is PASS when every gate holds, FAIL otherwise:
  - the tests pass;
  - no bug (ruff's bug families: `F`, `B`, `PLE`);
  - no vulnerability of medium or high severity (bandit, with the project's bandit settings, on `src` and `tests`);
  - maintainability A in every file (radon);
  - no duplicated block (pylint, with the project's similarity settings);
  - no function above the complexity limit, read from `[tool.ruff.lint.mccabe] max-complexity` (ruff's default, 10, when absent);
  - coverage at least `[tool.coverage.report] fail_under`, when set; reported only when not.
- Coverage is judged on the whole project: there is no separate gate for new code.
- Smells (the other ruff findings) and low-severity vulnerabilities are reported, never gated.
- The outputs are written to `docs/qualitycheck-report/`, which the project ignores in git, so the local copy is always the last one:
  - `report.md`, in English. Its header gives the tested commit, the date, the result, and the last passing commit with its date (or "none yet"). It then gives one line per gate, the metrics, the findings, and the trend of the last runs;
  - `history.csv`, one row per run, `;` separator, rows never rewritten;
  - `coverage.xml`, `htmlcov/` and `bandit.html`.
- The command exits 0 on PASS and 1 on FAIL.

**Acceptance scenarios**: `tests/bdd/features/quality-check.feature`

---

### US-02 - Publish each check without growing the repository (Priority: P1)

**As a** project owner **I want** the last check published with the repository, without its past versions **so that** anyone reading the repository sees the last result and when the code last passed, while the checked branch and the repository size stay untouched.

**Business rules**:
- The command refuses to run on a tree with uncommitted or untracked changes: the result must describe a commit.
- It refuses to run when `docs/qualitycheck-report/` is not ignored by git, and says to add it to `.gitignore`.
- Before the check, it fetches the `qualitycheck-report` branch, to continue its `history.csv`; offline, it continues from the local branch.
- After the check, it replaces the `qualitycheck-report` branch with one commit without parent, `chore: record qualitycheck report`, holding the content of `docs/qualitycheck-report/`, and pushes it, replacing the remote one.
- Nothing is committed on the checked branch.
- Offline, or when the push fails: a warning, the branch stays local, and the exit code is the check's.

**Acceptance scenarios**: `tests/bdd/features/publish.feature`

---

### US-03 - Check the links (Priority: P2)

**As a** project owner **I want** broken links found by the quality check **so that** the docs stay usable, without slowing every commit.

**Business rules**:
- The check runs lychee on the project's Markdown files; a broken link fails the result.
- Links listed in the project's `.lycheeignore` are skipped.
- Offline, or without lychee: a warning in the report, not a failure.

**Acceptance scenarios**: `tests/bdd/features/links.feature`

---

### US-04 - Be reminded before pushing unchecked code (Priority: P2)

**As a** project owner **I want** a warning before a push when the last check is old or failed **so that** I run the check in time, without ever being blocked.

**Business rules**:
- `uv run qualitycheck --status`, run by a pre-push hook, reads the history from the local `qualitycheck-report` branch, else from its last fetched remote copy, without network access.
- It prints a warning when there is no recorded check, when the last one failed, or when it is older than `max_commits` commits or `max_days` days.
- It always exits 0: it never blocks a push.
- `[tool.qualitycheck]` holds only `max_commits` (default 20) and `max_days` (default 7); any other key is rejected with a message naming the known ones: the check stops, the reminder only warns.

**Acceptance scenarios**: `tests/bdd/features/status.feature`

---

### Edge Cases

- No test at all, or no `src/`: the gates that need them report "n/a"; the tests gate fails.
- Tests failing: FAIL, the report quotes the end of the pytest output.
- A tool missing from the project's environment: that gate fails, and the report names the tool.
- No `[tool.qualitycheck]`: the defaults apply.
- First run: no `qualitycheck-report` branch, "last passing commit: none yet".
- No remote: the branch is replaced locally, the push is skipped with a warning.
- A check run on two machines: each continues the history it fetched; offline runs may lose the other machine's rows, never their own.
- A check run twice on the same commit: two rows, the last one wins in the header.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `uv run qualitycheck` MUST run every gate of US-01 on the whole project and write the report and its companion files in `docs/qualitycheck-report/`.
- **FR-002**: The result MUST be PASS only when every gate holds; the exit code MUST be 0 on PASS, 1 on FAIL.
- **FR-003**: The thresholds MUST come from the project's own tool settings; `[tool.qualitycheck]` MUST hold only `max_commits` and `max_days`.
- **FR-004**: The command MUST refuse a dirty tree and a `docs/qualitycheck-report/` not ignored by git; it MUST publish the outputs as the single commit of the `qualitycheck-report` branch, and MUST NOT commit on the checked branch; a failed push MUST only warn.
- **FR-005**: Broken links MUST fail the result, except those in `.lycheeignore`; an unavailable link check MUST only warn.
- **FR-006**: `--status` MUST warn on a missing, failed or stale check and MUST never fail.

## Success Criteria *(mandatory)*

- **SC-001**: On a clean project, one command gives a PASS report, published on `qualitycheck-report`, with the checked branch unchanged.
- **SC-002**: Each gate, broken on purpose in a test case, turns the result to FAIL and names the cause in the report.
- **SC-003**: After any number of checks, the `qualitycheck-report` branch holds one commit, and its history keeps one row per check.
- **SC-004**: Offline, the command completes, with warnings and no failure due to the network.
- **SC-005**: A push is never blocked by the reminder.

## Assumptions

- The checked project has ruff, bandit, radon, pylint and pytest-cov in its dev dependencies; qualitycheck depends on them too, so installing it brings them.
- Projects install qualitycheck as a dev dependency pinned to a version, and run `--status` from a pre-push hook.
- Defaults `max_commits = 20` and `max_days = 7`.
- The replaced commits of `qualitycheck-report` are no longer referenced: clones no longer download them, and the host removes them later.

## Definition of Ready *(checked before /speckit-plan)*

- [x] Clear need (as a / I want / so that)
- [x] Gherkin scenarios written in `tests/bdd/features/`
- [x] Edge cases identified
- [x] No open [NEEDS CLARIFICATION] marker
- [x] Each story fits in one session

## Definition of Done *(checked before closing)*

- [X] Tests written first and green (TDD)
- [X] Tests structured as test cases (`test-cases/`)
- [X] Every scenario verified (manual ones ticked here)
- [X] Documentation up to date
- [X] `/code-review` done
- [X] No unrecorded technical debt (issue #1)
- [X] Commits reference the story (`Refs: US-XX`)
