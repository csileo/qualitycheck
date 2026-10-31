# Tasks: One local quality check, published with the project

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: Setup

- [X] T001 Package skeleton: `src/qualitycheck/__init__.py`, `cli.py` with `main`, script `qualitycheck` and runtime dependencies in `pyproject.toml`, `uv.lock`
- [X] T002 Test support: byte snapshots in `tests/conftest.py`, fixtures copying a test project into a fresh repository with a bare remote, report normalization
- [X] T003 [P] ADR 0001 in `docs/adr/0001-publish-on-a-replaced-branch.md`, ADR 0002 in `docs/adr/0002-pinned-lychee-download.md`

## Phase 2: US-01 - Check the project's quality in one command

- [X] T004 [US1] Test projects `test-cases/projects/{clean,failing-test,bug,vulnerability,unmaintainable,duplication,complex,low-coverage,smell}/input/`
- [X] T005 [US1] Steps of `tests/bdd/features/quality-check.feature` in `tests/bdd/test_quality_check.py`; red
- [X] T006 [P] [US1] Unit tests and core: `gates.py`, `history.py`, `report.py` (`tests/unit/`)
- [X] T007 [US1] Shell: `settings.py`, `tools.py`, wiring in `cli.py`; report snapshots in `output/`; green

## Phase 3: US-02 - Publish each check without growing the repository

- [X] T008 [US2] Steps of `tests/bdd/features/publish.feature` in `tests/bdd/test_publish.py`; red
- [X] T009 [US2] `repository.py`: dirty tree, ignored outputs, fetch, replaced branch, push with warning; green

## Phase 4: US-03 - Check the links

- [ ] T010 [US3] Steps of `tests/bdd/features/links.feature` in `tests/bdd/test_links.py`; red
- [ ] T011 [US3] `lychee.py` and the links gate; green

## Phase 5: US-04 - Be reminded before pushing unchecked code

- [ ] T012 [US4] Steps of `tests/bdd/features/status.feature` in `tests/bdd/test_status.py`; red
- [ ] T013 [US4] `status.py`, `--status` in `cli.py`; green

## Phase 6: Polish

- [ ] T014 README usage and settings; `docs/architecture.md`
- [ ] T015 `/code-review`, then tick the DoD in `spec.md`
- [ ] T016 Release v0.1.0: `CHANGELOG.md` by git-cliff, tag `v0.1.0`, push

## Dependencies

Phase 1 first; US-01 before the others (they need a check to run); US-02, US-03 and US-04 then in any order.
