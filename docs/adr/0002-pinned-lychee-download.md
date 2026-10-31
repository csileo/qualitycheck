---
status: accepted
date: 2026-10-31
---

# Download a pinned lychee for the link check

## Context and Problem Statement

The link check uses lychee, a Rust program: it is not on PyPI (the `lychee` package there is a blog generator), so installing qualitycheck cannot bring it. Asking every project owner to install it, or to keep it in pre-commit, defeats the one-command check. How does qualitycheck get lychee?

## Considered Options

* Require lychee on `PATH`
* Run lychee through pre-commit
* Download a pinned release binary for the platform, once, into the user cache; lychee on `PATH` wins

## Decision Outcome

Chosen option: "Download a pinned release binary", as lychee's own pre-commit hook does, because the check then needs no setup, and a pinned version gives the same result on every machine.

* The binary is downloaded on the first check that needs it, then reused.
* Offline with no binary: the link check is skipped with a warning, never a failure.

### Consequences

* Good, because one command checks the links, on Linux, macOS and Windows.
* Bad, because qualitycheck downloads and runs a binary: it comes from lychee's GitHub releases only, pinned to one version.
