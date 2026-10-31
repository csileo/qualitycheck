# Feature Specification: A report readable at a glance, as on Sonar

**Feature Branch**: `main`

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "Make the report look as close as possible to Sonar's overview, readable on GitHub in public and private repositories alike: Markdown with SVG images (ADR 0003), Sonar's ratings for display only, radon's gate kept (ADR 0004). Validated on a mockup, branch `spike/visual-report-mockup`, to delete once this story is done."

## User Stories *(mandatory)*

### US-05 - Read the check at a glance on GitHub, as on Sonar (Priority: P2)

**As a** project owner **I want** the report to open on a dashboard like Sonar's overview, rendered by GitHub itself **so that** I see where the project stands in a few seconds, in public and private repositories alike, with no site to host.

**Business rules**:
- `report.md` keeps its header; right after it comes the dashboard, then the existing sections, unchanged.
- The dashboard is made of SVG images, in this order:
  - **Quality Gate**: "Passed" in green or "Failed" in red, the failed conditions with their value and requirement, and the lines of code. Its conditions are qualitycheck's gates.
  - Three rated tiles: **Reliability** (bugs), **Security** (medium and high vulnerabilities), **Maintainability** (smells and the technical debt ratio), each with its count and its rating A to E in Sonar's colours.
  - Three measure tiles: **Coverage** (percentage and ring), **Duplications** (percentage), **Security Hotspots** (low-severity vulnerabilities, to review).
  - **Activity**: one chart of issues (code smells, bugs, vulnerabilities) and one chart of coverage, over the last runs of `history.csv`, with `fail_under` drawn when it is set.
- A tile whose gate failed carries a "Failed" badge; a tile whose tool is missing shows "n/a" in grey, without rating.
- Each tile links to the section of the report that lists its findings.
- The ratings follow Sonar (ADR 0004) and never change the result:
  - Reliability: A without bug; C when the worst bug is of ruff's `B` family; D when it is of the `F` or `PLE` family.
  - Security: A without medium or high vulnerability; C when the worst is medium; D when it is high; E when it is high with high confidence.
  - Maintainability: technical debt ratio = smells × 5 min / (lines of code × 30 min); A up to 5 %, B up to 10 %, C up to 20 %, D up to 50 %, E above; n/a without lines of code.
  - Duplications: lines in duplicated blocks / lines of code, as a percentage, at most 100 %.
- The images are written to `docs/qualitycheck-report/images/` and published with the report on the `qualitycheck-report` branch; `report.md` links them by relative path.
- Each image is an SVG written by qualitycheck: no script, no external font or link; it draws its own white card, so it reads the same in GitHub's light and dark themes; it carries an alternative text with the same information.

**Acceptance scenarios**: `tests/bdd/features/visual-report.feature`

---

### Edge Cases

- First run: the activity charts show one point.
- More runs than shown: the activity charts show the last ones only, as the trend table does.
- A history row with an empty cell (a tool was missing then): that point is left out of its line.
- No `fail_under`: the coverage tile has no requirement, the coverage chart no threshold line.
- Coverage of 0 % or 100 %: the ring is all red or all green.
- No `src/`: maintainability and duplications are n/a.
- A tool missing (ruff, bandit, pylint, pytest): its tiles are n/a, the Quality Gate names the missing tool as a failed condition.
- Links not checked (offline): the Quality Gate shows the links condition as n/a, as the gates table does.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `report.md` MUST open, after its header, on the Quality Gate image, the six tiles and the activity image, in that order, before its existing sections.
- **FR-002**: The Quality Gate image MUST say "Passed" or "Failed" as the result does, and name each failed condition with its value and requirement.
- **FR-003**: The reliability, security and maintainability ratings MUST follow the rules of US-05 and MUST NOT change the result.
- **FR-004**: The images MUST be written to `docs/qualitycheck-report/images/`, published on `qualitycheck-report`, and linked by relative path.
- **FR-005**: Each image MUST contain no script and no external reference, and MUST carry an alternative text giving its information.
- **FR-006**: The activity image MUST draw the last runs of the history, the current one included.

## Success Criteria *(mandatory)*

- **SC-001**: On GitHub, the report of a private repository shows the dashboard to its members, with no site to set up.
- **SC-002**: The result, the failed conditions and the three ratings are visible without scrolling on a laptop screen.
- **SC-003**: The images read the same in GitHub's light and dark themes.
- **SC-004**: Each rating rule, given a case on its boundary, gives the rating Sonar would.

## Assumptions

- GitHub keeps rendering relative SVG images in Markdown, and links on images.
- The report stays in English; the tile names are Sonar's.
- The mockup on `spike/visual-report-mockup` is the visual reference; the branch is deleted once this story is done.

## Definition of Ready *(checked before /speckit-plan)*

- [x] Clear need (as a / I want / so that)
- [x] Gherkin scenarios written in `tests/bdd/features/`
- [x] Edge cases identified
- [x] No open [NEEDS CLARIFICATION] marker
- [x] Each story fits in one session

## Definition of Done *(checked before closing)*

- [ ] Tests written first and green (TDD)
- [ ] Tests structured as test cases (`test-cases/`)
- [ ] Every scenario verified (manual ones ticked here)
  - [ ] Manual: the report renders on GitHub, in the light and dark themes
- [ ] Documentation up to date
- [ ] `/code-review` done
- [ ] No unrecorded technical debt
- [ ] Commits reference the story (`Refs: US-05`)
- [ ] Mockup branch `spike/visual-report-mockup` deleted
