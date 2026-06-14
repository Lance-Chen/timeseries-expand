# Pre-release Checklist — timeseries-expand v0.1.0

Use this checklist before publishing v0.1.0 to GitHub and PyPI. Each item has
a checkbox and a short rationale. Run them in order; the script block at the
end gives you a one-shot sequence.

---

## 1. Personalize the repo (placeholders)

The scaffold was generated with `<your-username>` placeholders. Replace them
with your actual GitHub username everywhere they appear.

- [ ] `pyproject.toml` — 5 occurrences of `<your-username>` in `[project.urls]`
- [ ] `README.md` — 2 occurrences (CI badge, documentation link)
- [ ] `CONTRIBUTING.md` — 1 occurrence (clone URL)
- [ ] `SECURITY.md` — 1 occurrence (security contact email)
- [ ] `pyproject.toml` — replace `authors` entry (currently `{ name = "Jiang" }`) with your real name and email

Quick check — should output nothing after replacement:

```bash
grep -rn "your-username\|your-security-contact" \
    --include="*.md" --include="*.toml" --include="*.yml" .
```

---

## 2. Local hygiene

- [ ] Delete local build / test caches: `rm -rf .pytest_cache .hypothesis .mypy_cache dist build *.egg-info`
- [ ] Confirm `.gitignore` is present and complete (already in place)
- [ ] Confirm no NUL bytes / garbage in source files:

```bash
for f in $(find . -name "*.py" -not -path "./.git/*"); do
    if grep -lP "\x00" "$f" >/dev/null 2>&1; then echo "BAD: $f"; fi
done
```

- [ ] Confirm source tree is clean: `find . -name "__pycache__" -type d -exec rm -rf {} +`

---

## 3. Code quality gates

Run from the project root.

- [ ] Lint passes: `ruff check src tests`
- [ ] Format check: `ruff format --check src tests`
- [ ] Type check: `mypy src`
- [ ] All tests pass: `TZ=UTC pytest tests/` (expect 122 passed)
- [ ] Slow test included: `TZ=UTC pytest tests/ -m slow` (T20, ~5 s)
- [ ] No test failures under random Hypothesis seed:

```bash
TZ=UTC pytest tests/test_property.py --hypothesis-seed=$(date +%s)
```

- [ ] Build artifacts cleanly:

```bash
python -m pip install --upgrade build
python -m build
twine check dist/*
```

- [ ] Install from local wheel and smoke test:

```bash
python -m pip install dist/timeseries_expand-0.1.0-py3-none-any.whl --force-reinstall
python -c "from timeseries_expand import expand; print(expand)"
ts-expand --help
```

---

## 4. Documentation review

- [ ] `README.md` opens cleanly on GitHub (preview rendered view)
- [ ] All 4 example CSV commands in README run successfully:

```bash
for cmd in \
    "coal_price_weekly.csv W-MON h UTC" \
    "annual_index.csv YE D UTC" \
    "monthly_index.csv ME W-MON Asia/Shanghai" \
    "semi_monthly.csv SME h UTC" \
; do
    set -- $cmd
    IFS=' ' read -r f src tgt tz <<< "$cmd"
    ts-expand "examples/$f" "/tmp/preview_$f" \
        --source-freq "$src" --target-freq "$tgt" --timezone "$tz"
done
```

- [ ] `CHANGELOG.md` has a 0.1.0 entry dated today
- [ ] `LICENSE` present and is MIT
- [ ] `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md` all filled in
- [ ] Issue templates render correctly in `.github/ISSUE_TEMPLATE/`

---

## 5. GitHub repo setup

- [ ] Create empty GitHub repo: <https://github.com/new>
  - Name: `timeseries-expand`
  - Description: "Publication-aware time-series frequency expansion"
  - Visibility: **Public**
  - **Do NOT** initialize with README / license / .gitignore (we have them)
- [ ] Add topics on the GitHub repo page: `time-series`, `pandas`, `python`,
      `resampling`, `forward-fill`, `commodity-pricing`, `coal-price`
- [ ] Configure repo settings:
  - [ ] Settings → General → Default branch: `main`
  - [ ] Settings → Pages → Source: `gh-pages` branch (after first `mkdocs gh-deploy`, optional)
  - [ ] Settings → Secrets → `PYPI_API_TOKEN` (only if publishing to PyPI)
  - [ ] Settings → Branches → Branch protection on `main`: require CI

---

## 6. Push to GitHub

From the project root:

```bash
git init
git add .
git commit -m "chore: initial public release of timeseries-expand v0.1.0"
git branch -M main
git remote add origin https://github.com/<your-username>/timeseries-expand.git
git push -u origin main
```

- [ ] Repository is reachable at `https://github.com/<your-username>/timeseries-expand`
- [ ] `README.md` renders correctly on the GitHub home page
- [ ] CI workflow (`.github/workflows/ci.yml`) runs on the push and turns green

---

## 7. PyPI publication (optional but recommended)

Two options.

### Option A: Trusted Publishing via GitHub Actions (recommended)

- [ ] PyPI: <https://pypi.org/manage/account/publishing/> → add a pending publisher
  - Owner: `<your-username>`
  - Repository: `timeseries-expand`
  - Workflow: `release.yml`
  - Environment name: `pypi`
- [ ] PyPI account has 2FA enabled (required for API tokens)
- [ ] (No `PYPI_API_TOKEN` secret needed; trusted publishing uses OIDC)

### Option B: Manual upload

```bash
python -m pip install --upgrade twine
twine upload dist/*
```

- [ ] Enter `__token__` as username and your PyPI token as password
- [ ] Verify on <https://pypi.org/project/timeseries-expand/> after upload

---

## 8. Cut the v0.1.0 release

- [ ] Tag the release:

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

- [ ] `release.yml` workflow runs (if Option A above is configured)
- [ ] Verify on <https://pypi.org/project/timeseries-expand/#history> that v0.1.0 appears
- [ ] On GitHub → Releases → "Draft a new release" → choose tag `v0.1.0`
  - Title: `v0.1.0 — Initial public release`
  - Description: copy the 0.1.0 section of `CHANGELOG.md`
  - Attach: `dist/timeseries-expand-0.1.0-py3-none-any.whl` and `.tar.gz`
  - Mark as latest

---

## 9. Post-release smoke test

From a fresh virtualenv (verifies that the published artifact actually works):

```bash
python -m venv /tmp/verify
source /tmp/verify/bin/activate
pip install timeseries-expand

python -c "
import pandas as pd
from timeseries_expand import expand
df = pd.DataFrame({
    'timestamp': pd.to_datetime(['2024-01-01', '2024-01-08', '2024-01-15']),
    'value': [100.0, 101.0, 102.0],
})
print(expand(df, 'W-MON', 'h').head(3))
"

ts-expand examples/coal_price_weekly.csv /tmp/final_check.csv \
    --source-freq W-MON --target-freq h --timezone UTC
wc -l /tmp/final_check.csv  # expect 8738
```

- [ ] Library installs cleanly from PyPI
- [ ] Functional API works
- [ ] CLI works
- [ ] Output row count matches the expected `8738` for the weekly coal price file
- [ ] `pip show timeseries-expand` shows the correct version

---

## 10. Announce

- [ ] Star your own repo (kidding, but a useful self-bookmark)
- [ ] (Optional) Post to relevant communities:
  - [ ] r/Python, r/datascience on Reddit
  - [ ] Hacker News (Show HN)
  - [ ] Chinese dev communities (掘金, 知乎) given the coal-price origin story
- [ ] (Optional) Add to awesome-pandas lists
- [ ] (Optional) Tweet / share

---

## One-shot release script

If you've already done steps 1–6 and just want to cut a release:

```bash
# Tag, push, watch CI
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0

# Watch the release workflow
gh run watch
```

---

## Rollback

If v0.1.0 has a critical bug after release:

1. Yank from PyPI: <https://pypi.org/project/timeseries-expand/#history> → yank
2. Delete the GitHub release
3. Delete the tag locally and remotely: `git tag -d v0.1.0 && git push origin :refs/tags/v0.1.0`
4. Fix the bug, cut v0.1.1

---

## Versioning policy

This project follows [Semantic Versioning](https://semver.org/):

- **Patch** (0.1.x): bug fixes, doc fixes, no API change
- **Minor** (0.x.0): backwards-compatible features (e.g., new frequency added)
- **Major** (x.0.0): breaking API changes

Until 1.0.0, any backward-incompatible change bumps the minor version.
