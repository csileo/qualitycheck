# Implementation Plan: A report readable at a glance, as on Sonar

**Branch**: `main` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

## Summary

A functional core rates the measures as Sonar does and draws the dashboard as SVG text; `report.md` links the images right after its header; the shell writes them to `docs/qualitycheck-report/images/`, published with the rest. No new dependency, no new tool run.

## Technical Context

- Python ≥ 3.10, standard library only: SVG is written as text, escaped with `xml.sax.saxutils`.
- The mockup of `spike/visual-report-mockup` gives the layout, sizes and colours: tiles of 260 × 128, a gate banner and an activity card of 788 wide, Sonar's classic rating colours (A `#00aa00`, B `#b0d513`, C `#eabe06`, D `#ed7d20`, E `#e00000`).

## Research

- **R1 Bandit confidence**: bandit's JSON gives `issue_confidence`; `Vulnerability` gains a `confidence` field, last and defaulting to `"HIGH"`, so the existing test cases stay valid.
- **R2 Duplicated lines**: pylint names each copy as `module:[start:end]`, start counted from 0 and end excluded (`demo.first:[5:12]` covers 7 lines). The duplicated lines are the union of these ranges per module, summed; the percentage divides them by radon's lines of code of `src/`, capped at 100 %.
- **R3 Debt ratio**: smells × 5 / (lines of code × 30), as a percentage; n/a without lines of code. Rating bounds 5, 10, 20, 50, included in the better rating.
- **R4 Rendering on GitHub**: relative images in Markdown and links on images render in private repositories; GitHub ignores scripts and external references in an image anyway, and none is written. Each SVG has a `<title>` and an `aria-label` equal to the alternative text, which the tests read.
- **R5 Anchors**: a tile links to its section with GitHub's heading anchors: lowercase, punctuation dropped, spaces turned into hyphens (`Smells (first 30)` → `#smells-first-30`).
- **R6 Activity**: the last `TREND_ROWS` rows of the history; empty cells are left out of their line; one run is drawn at the middle; the issues scale rounds up to a multiple of 4 (at least 4), the coverage scale is 0-100 %; dates as `Oct 31`, from a fixed English month list.

## Design

| Module | Role |
|---|---|
| `ratings.py` | Sonar's ratings, debt ratio, duplicated lines, hotspots (core) |
| `svg.py` | SVG primitives and the four kinds of image: gate banner, rated tile, measure tile, activity (core) |
| `dashboard.py` | the dashboard of a run: `Image` (name, alternative text, link, SVG), its images, its Markdown lines (core) |
| `report.py` | `render` gains the images and writes the dashboard after the header (core) |
| `tools.py` | reads bandit's confidence (shell) |
| `cli.py` | writes `images/*.svg` as bytes, LF, before publishing (shell) |

The tiles map to the gates for their "Failed" badge: reliability ← bugs, security ← vulnerabilities, maintainability ← maintainability and complexity, coverage ← coverage, duplications ← duplication; Security Hotspots has none.

## Constitution Check

| Rule | Status |
|---|---|
| ADR before implementing | ADR 0003 (Markdown with SVG images), ADR 0004 (Sonar's ratings for display only) |
| TDD, BDD | `visual-report.feature` red first; dashboard snapshots in `test-cases/dashboard/` |
| Test cases | measures, run and history as inputs; the SVGs and reports as byte snapshots |
| Complexity ≤ 15, 5 arguments | `dashboard.images` takes 5: run, gates, measures, history rows, `fail_under` |
| Functional core, imperative shell | `ratings`, `svg`, `dashboard`, `report` hold no I/O |

## Complexity Tracking

None.
