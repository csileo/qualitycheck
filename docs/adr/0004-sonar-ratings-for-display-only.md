---
status: accepted
date: 2026-10-31
---

# Rate the project as Sonar does, for display only

## Context and Problem Statement

The visual report (ADR 0003) shows ratings from A to E, as Sonar's overview does. qualitycheck has no rating yet: each gate is PASS or FAIL on a count. SimToReal3's `run_audit.py`, which qualitycheck was adapted from, rates by counts (bugs, high vulnerabilities, smells per 1,000 lines, duplicated blocks). Which ratings, and do they change the result?

## Considered Options

* SimToReal3's ratings, by counts
* Sonar's ratings: worst severity for reliability and security, technical debt ratio for maintainability, duplicated lines as a percentage
* Either one, with the maintainability rating replacing radon's gate

## Decision Outcome

Chosen option: "Sonar's ratings", for display only, with radon's gate kept, because the report must read as close as possible to Sonar, and a gate on Sonar's maintainability rating would almost never fail: with Sonar's defaults, losing the A takes more than 300 smells per 1,000 lines.

* Reliability: A without bug; C when the worst bug is of ruff's `B` family; D when it is of the `F` or `PLE` family. ruff gives no severity: the family stands for it, and B and E stay unused.
* Security: A without medium or high vulnerability; C when the worst is medium; D when it is high; E when it is high with high confidence. Low-severity findings are shown as Security Hotspots, without rating, and B stays unused.
* Maintainability: technical debt ratio = smells of `src/` × 5 min / (lines of code of `src/` × 30 min), as radon counts lines in `src/` only; A up to 5 %, B up to 10 %, C up to 20 %, D up to 50 %, E above.
* Duplications: duplicated lines / lines of code, as a percentage, without rating; coverage as a percentage, without rating.
* The Quality Gate keeps qualitycheck's gates as its conditions; the ratings never change PASS or FAIL.

### Consequences

* Good, because the ratings mean what they mean on Sonar.
* Good, because radon still fails a file grown too long or too complex, which no rating catches.
* Bad, because the maintainability rating is almost always A, as on Sonar with its defaults.
* Bad, because a rating and the result can disagree: a maintainability rated C does not fail the check, while a file below radon's A does; the Quality Gate, not the ratings, gives the result.
