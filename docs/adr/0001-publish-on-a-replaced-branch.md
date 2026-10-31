---
status: accepted
date: 2026-10-31
---

# Publish the check on a replaced branch

## Context and Problem Statement

Each check writes a report, a history, coverage files and an HTML coverage site. Committed on the checked branch, they add a commit per check and every past version of files that change at each run (dates, coverage data): the repository grows forever, and its log fills with noise. Git cannot keep only the last version of a path. Where should the outputs go, so that the last result stays readable with the repository?

## Considered Options

* Commit the outputs on the checked branch
* Ignore every output in git, keep them local
* Publish the outputs as the single commit of a dedicated branch, replaced at each check

## Decision Outcome

Chosen option: "Publish the outputs as the single commit of a dedicated branch, replaced at each check", because the last result stays on the host, readable on its own branch, while the checked branch and the repository size stay untouched.

* The outputs are written to `docs/qualitycheck-report/`, ignored by git.
* The branch `qualitycheck-report` holds one commit without parent, built from that folder with a temporary index, then force-pushed; the checked branch, its index and its working tree never change.
* `history.csv` holds the history: each check continues the longer of the fetched and the local one, so a check that could not be pushed is kept.

### Consequences

* Good, because the repository holds one version of the outputs, and the checked branch's log holds code only.
* Good, because a host serving the branch as a site shows the HTML coverage too.
* Bad, because the branch is force-pushed, and the outputs are no longer tied to the commits they judged, except by the tested commit they name.
