# Architecture

## Context

```mermaid
flowchart LR
    owner([Project owner]) -->|uv run qualitycheck| qc[qualitycheck]
    qc -->|python -m| tools[ruff, bandit, radon, pylint, pytest]
    qc -->|downloads once| lychee[lychee release]
    qc -->|reads, publishes| repo[(Checked repository)]
    repo -->|push --force| host[(Git host)]
```

qualitycheck runs inside the checked project's environment: the tools are the project's own, at the versions its lock fixes.

## Containers

```mermaid
flowchart TB
    cli[cli: check, --status] --> settings
    cli --> tools
    cli --> repository
    cli --> core
    subgraph core[Functional core, no I/O]
        gates --> report
        history --> report
        status
    end
    tools --> lychee
    tools -->|python -m| bandit_scan
```

| Module | Role |
|---|---|
| `cli` | the two commands and their exit codes |
| `settings` | `[tool.qualitycheck]` and `fail_under` |
| `tools` | runs the tools, parses their outputs into `Measures` |
| `bandit_scan` | runs bandit once, writing its JSON and `bandit.html` from the same scan |
| `lychee` | finds or downloads the pinned lychee; sorts its findings |
| `gates` | judges the measures: one gate each, PASS, FAIL or n/a |
| `report` | renders `report.md` |
| `history` | reads and appends `history.csv` |
| `status` | the reminder before a push |
| `repository` | refuses a dirty tree, continues the history, publishes the branch |

## Decisions

- [ADR 0001](adr/0001-publish-on-a-replaced-branch.md): publish on a replaced branch.
- [ADR 0002](adr/0002-pinned-lychee-download.md): download a pinned lychee.
