# Changelog

All notable changes to this project are documented in this file.

## [0.1.0] - 2026-10-31

### Added

- Check the quality of a project in one command
- Publish each check on a replaced branch
- Check the links of the tracked Markdown files
- Remind before a push when the last check is missing, failed or stale

### Fixed

- Reject an invalid pyproject.toml or a non-numeric fail_under with a clear message
- Warn on an unreadable last check and read a date without offset as local time
- Stop when git cannot record the report and keep checks that were not pushed
- Count a tool as missing only when python cannot find the tool itself
- Leave a missing tool's cells empty in the history instead of 0
- Check Markdown files whose name has a space or an accent

### Changed

- Share the check-running helpers and steps between scenarios
- Read every unit test from test-cases and keep tests/ for modules in folders
