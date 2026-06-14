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
- 116 tests
