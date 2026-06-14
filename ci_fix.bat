@echo off
REM One-shot CI fix: clean, verify, commit, push, watch
REM Run from project root: F:\ClaudeProject\Work_for_Jiang\timeseries-expand

setlocal enabledelayedexpansion

echo ==========================================
echo  One-shot CI fix
echo ==========================================
echo.

echo [1/4] Running all 4 checks locally first...
set TZ=UTC
python -m pytest tests/ -q
if errorlevel 1 (
    echo FAIL: tests failed locally. STOP - fix code first.
    exit /b 1
)
python -m ruff check src tests
if errorlevel 1 (
    echo FAIL: ruff check failed.
    exit /b 1
)
python -m ruff format --check src tests
if errorlevel 1 (
    echo FAIL: ruff format check failed.
    exit /b 1
)
python -m mypy src
if errorlevel 1 (
    echo FAIL: mypy check failed.
    exit /b 1
)
echo       All 4 checks pass.
echo.

echo [2/4] Committing changes...
git add .
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "fix: CI reliability hardening (mypy pin, .gitignore, trailing newlines)"
    if errorlevel 1 (
        echo FAIL: git commit failed.
        exit /b 1
    )
) else (
    echo       Nothing to commit.
)
echo.

echo [3/4] Pushing to GitHub...
git push origin main
if errorlevel 1 (
    echo FAIL: git push failed.
    exit /b 1
)
echo.

echo [4/4] Open this URL to watch CI:
echo       https://github.com/Lance-Chen/timeseries-expand/actions
echo.
echo Done.

endlocal