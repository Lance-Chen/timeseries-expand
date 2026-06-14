# Contributing

Thanks for your interest in contributing to `timeseries-expand`! This document covers the basics.

## Development setup

```bash
git clone https://github.com/Lance-Chen/timeseries-expand.git
cd timeseries-expand
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -e ".[dev,polars]"
```

## Code style

- Formatter & linter: [ruff](https://docs.astral.sh/ruff/)
- Type checker: [mypy](https://mypy.readthedocs.io/) with `strict = true`
- Python 3.9+ syntax

Run before committing:

```bash
ruff check src tests
ruff format --check src tests
mypy src
```

## Testing

We use `pytest` plus `hypothesis` for property-based tests. All new code must include tests.

```bash
pytest                              # full suite
pytest tests/test_expander.py       # one file
pytest -m "not slow"                # skip slow benchmarks
pytest --benchmark-only             # only benchmarks
```

Tests run with `TZ=UTC` set; this matters for any timezone-aware test.

## Adding a new frequency

1. Add the alias to `src/timeseries_expand/frequencies.py`.
2. Add at least 5 unit tests covering: simple case, gap, cross-boundary, DST (if applicable), large input.
3. Add one property-based test in `tests/property/`.
4. Update `README.md` frequency table and `docs/api.md`.
5. Update `CHANGELOG.md` under `[Unreleased]`.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: add semi-monthly frequency`
- `fix: handle DST spring-forward in asia/shanghai`
- `docs: clarify gap_flag semantics`
- `test: add property test for forward-fill monotonicity`
- `chore: bump pandas minimum to 2.2.1`

## Pull requests

- Open a draft PR early for design feedback.
- Make sure CI is green before requesting review.
- Reference any related issues (`Fixes #42`).

## Releases

Maintainers cut releases by tagging `vX.Y.Z`. `release.yml` will publish to PyPI automatically. Make sure `CHANGELOG.md` is updated before tagging.