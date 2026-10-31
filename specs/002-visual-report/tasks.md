# Tasks: A report readable at a glance, as on Sonar

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: Setup

- [X] T001 Refactor: move the shared steps (`the project "..."`, `a clean project with a remote`, `..., checked twice`) to `tests/conftest.py`, with `with_remote`

## Phase 2: US-05 - Read the check at a glance on GitHub, as on Sonar

- [X] T002 [US5] Steps of `tests/bdd/features/visual-report.feature` in `tests/bdd/test_visual_report.py`; red
- [X] T003 [US5] `Vulnerability.confidence`, read from bandit in `tools.py`
- [X] T004 [US5] `ratings.py`: reliability, security, debt ratio, maintainability, duplicated lines, duplications, hotspots
- [X] T005 [US5] `svg.py` and `dashboard.py`; snapshots in `test-cases/dashboard/`
- [X] T006 [US5] `report.render` with the dashboard; report snapshots updated and reviewed
- [X] T007 [US5] `cli.py` writes `images/`; green
- [X] T008 [US5] Docs: README (outputs, ratings), `docs/architecture.md`
- [ ] T009 [US5] Manual: the report renders on GitHub, light and dark themes
- [ ] T010 [US5] DoD, `/code-review`, then delete `spike/visual-report-mockup`
