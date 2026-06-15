# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-06-14

### Added
- `date_format` parameter on `expand()`, `ExpandConfig`, and `--date-format` CLI flag
  to format output timestamps as strings via strftime. Pandas strftime patterns supported
  (e.g. `%Y-%m-%d`, `%Y W%W`). Default `None` preserves backward-compatible
  `Timestamp` output.
- `start` / `end` parameters on `expand()`, `ExpandConfig`, and `--start` / `--end` CLI
  flags to clip the output timestamp range. Each must lie within the input data range;
  otherwise `ValueError`. Accepts ISO strings, pandas `Timestamp`, or `datetime.date`;
  naive values are assumed UTC. Source timestamps outside the clipped range are dropped
  (so no data is extrapolated past the boundaries).
- 173 tests (up from 116), covering 14 date_format tests and 23 time_range tests across
  all 7 supported source frequencies, boundary cases, error scenarios, and CLI.

### Fixed
- Pin `mypy>=1.10,<2` (mypy 2.x has known bugs on Python 3.9; dropped 3.9 from CI).
- Pin `requires-python >= 3.10` (no longer officially supports 3.9).
- CI: drop Python 3.9 from matrix; add mypy pin step to prevent version drift.
- Fix `gap_flag` NaN on non-matching rows (now defaults to `False`).
- Fix single-release expansion (produces 24-hour window instead of 1 row).
- Fix `release.yml` environment block (was triggering on every push, not just tag push).
- Add `--version` CLI flag.
- Harden `.gitignore` with `**/__pycache__/`, `.ruff_cache/`, `*/_version.py`.
- Add trailing newlines to all markdown and toml files.

## [0.1.0] - 2026-06-14

### Added
- Initial public release.
- `FrequencyExpander` core class with publication-aware forward fill.
- Support for 21 source→target frequency combinations across:
  YE / QE / ME / SME / W-MON / D / h.
- `gap_flag` column flags intervals exceeding `gap_threshold_multiplier × expected_days`.
- Configurable output timezone (internal UTC for DST-safety).
- CLI entry point `ts-expand`.
- 116 tests