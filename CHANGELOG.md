# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-14

### Added
- Initial public release.
- `FrequencyExpander` core class with publication-aware forward fill.
- Support for 21 source→target frequency combinations across:
  YE / QE / ME / SME / W-MON / D / h.
- `gap_flag` column flags intervals exceeding `gap_threshold_multiplier × expected_days`.
- Configurable output timezone (internal UTC for DST-safety).
- CLI entry point `ts-expand`.
- 116 tests across 4 test files:
  - `test_expander.py` — core expander scenarios (T01-T20).
  - `test_frequencies.py` — full 21-combination × 4-property matrix.
  - `test_edge_cases.py` — DST, cross-boundary, NaN/NaT, duplicates.
  - `test_property.py` — Hypothesis property-based tests.

### Performance
- All 21 frequency combinations complete in under 15 ms for 10-year spans.
- 30-year weekly → hourly (>200k output rows) completes in under 5 s.