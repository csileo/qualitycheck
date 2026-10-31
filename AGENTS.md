# AGENTS.md

Permanent rules for coding agents working on qualitycheck. Taken from the rules of copierpythontemplate v0.15.0 (default answers), maintained by hand here.

## Collaboration
- **Go**: without the literal word "go" in the user's message, answer only; reading and searching are allowed. "go" = act: edit, write, run, commit.
- **Concision**: short answers, details on request; no recap of what was done except deviations and problems.
- **Language**: reply in the user's language; English for everything else (code, files, docs, comments, commit messages, interfaces, diagrams), unless the user asks for another language for a given file.
- **Focus**: stay on the task; never change approach without asking.
- **Plain explanations**: explain the role, not the jargon.
- **Costly mistake**: apologize first and own it; then explain, repair, and add a rule to `AGENTS.md` to prevent recurrence.
- **Scope**: work only inside the project folder.
- **Responsibilities**: the user decides and approves; the agent codes, tests and verifies.

## Workflow
- New feature: Feature → Story → DoR → Plan → Tasks → code → DoD, with Spec Kit (`/speckit-specify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-implement`). Without a story, propose one.
- DoR: clear need (as a / I want / so that), Gherkin written, edge cases identified, no open question, fits in one session.
- DoD: the task's tests green (the full suite runs only when the user asks), tests structured as test cases, scenarios verified, docs up to date, `/code-review` done, no unrecorded debt, commit references the story.
- Gherkin scenarios live in `tests/bdd/features/*.feature`, run by pytest-bdd; the spec links them, never copies them. A scenario that cannot be automated is checked by hand and ticked in the DoD.
- Fast track (no story, no plan): any commit type except `feat`, and spikes. `fix` → regression test first; `refactor` → tests green before and after; `perf` → measure before and after. Use the full workflow if visible behavior changes, the work exceeds one session, or an architecture decision is needed.
- Decisions: one ADR per decision in `docs/adr/`, MADR format, written before implementing; status "proposed" while options are studied.
- Technical debt: a GitHub issue labeled `tech-debt`, with reason and impact.
- Docs: always up to date; architecture in `docs/architecture.md` (light arc42, C4 levels 1-2 in Mermaid).
- Rule change: update every place that states the rule (`AGENTS.md`, the spec template, the README and other docs) in the same commit.

## Quality
- TDD: a red test before any production code (except spikes); Red → Green → Refactor.
- Test cases: every test reads its inputs from `test-cases/<group>/<case>/input/` and compares with expected outputs in `output/`, as syrupy snapshots regenerated with `--snapshot-update` and reviewed before commit. Inputs include CLI arguments, URLs and options; expected errors are outputs too. BDD scenarios keep their examples in the `.feature` file and take larger inputs from `test-cases/`. `test-cases/`, inputs and outputs, keeps its bytes: git, the hooks and the editor never rewrite it, and snapshots are written byte for byte (`.gitattributes`, `.editorconfig`).
- Tests depend on `src/`, never the reverse.
- PEP 8 and PEP 257 via ruff; cyclomatic complexity ≤ 15; at most 5 arguments per function.
- New code: 0 bugs, 0 vulnerabilities, maintainability A, no duplicated block (6 lines or more).
- Coverage ≥ 80% of the whole project (`src/`, branches included): the full test run with `--cov` fails below it.
- No CI: the quality check of this repository (`uv run qualitycheck`) runs only when the user asks.

## Design
- Simple Design rules, in order; nothing "for later".
- Explicit names, short functions, one responsibility each; comments explain why, never what.
- Object code: composition over inheritance; interfaces as `typing.Protocol`.
- Clean the files you touch, in a separate `refactor` commit before the behavior change.
- Business logic isolated from I/O: functional core, imperative shell; ports and adapters when an I/O has several implementations.

## Structure and naming
- `src/qualitycheck/` for code; `tests/{unit,integration,bdd,support}/` for test code only; `test-cases/` for test data; `docs/`; `specs/` for Spec Kit.
- Non-code names: lowercase kebab-case. Dates in names: ISO 8601.
- The product is one command, `uv run qualitycheck`, run at the root of the project it checks.
- Useful scripts live in `src/`, declared in `[project.scripts]`, run with `uv run <command>`.
- Tools that only produce test data live in `tests/support/`, write into `test-cases/<group>/<case>/input/` and run with `uv run python tests/support/<tool>.py`; never declared in `[project.scripts]`; named after what they produce, never `test_*.py` or `*_test.py`, which pytest would collect.
- Temporary files in `tmp/`, logs in `logs/`; never at the root.
- History lives in git only: code, comments and docs show the current state.

## Git
- Commit and push after each change, on `main`.
- Conventional Commits, one-line subject: `feat`, `fix`, `docs`, `refactor`, `test`, `perf`, `style`, `build`, `ci`, `chore`.
- Trailer `Refs: US-XX` mandatory when the commit belongs to a story.
- Never edit `CHANGELOG.md` by hand: git-cliff generates it at each release.

## Environment
- uv only: `uv sync`, `uv add`, `uv run`; never `pip install`.
- Runtime dependencies as version ranges, since qualitycheck is installed in other projects; dev tooling from `commonreqs` only, pinned to a tag or commit, at its exact versions; `uv.lock` is committed.
- A version changes only in a `build(deps)` commit, after the full test suite; never as a side effect.
- Secrets in `.env` (ignored); document variable names in `.env.example`.
- Relative paths only; LF line endings; UTF-8.
- Task impossible in the cloud (GPU, browser, network): flag it "local only".
- Web research: drive a real browser, start from Google, never guess URLs; space out requests; keep pages locally.
- CSV files use `;` as separator.
