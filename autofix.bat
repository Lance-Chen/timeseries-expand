@echo off
setlocal
cd /d "%~dp0"

set TZ=UTC

echo [1/4] Local checks...
python -m pytest tests/ -q >nul 2>&1 || (echo FAIL: tests& exit /b 1)
python -m ruff check src tests >nul 2>&1 || (echo FAIL: ruff check& exit /b 1)
python -m ruff format --check src tests >nul 2>&1 || (echo FAIL: ruff format& exit /b 1)
python -m mypy src >nul 2>&1 || (echo FAIL: mypy& exit /b 1)
echo       OK.

echo [2/4] Commit...
git add . >nul 2>&1
git diff --cached --quiet >nul 2>&1 && (echo       Nothing to commit.& goto :push) || (
    git commit -m "ci: drop Python 3.9 from CI matrix" >nul 2>&1
    if errorlevel 1 (echo FAIL: commit& exit /b 1)
    echo       OK.
)

:push
echo [3/4] Push...
git push origin main >nul 2>&1
if errorlevel 1 (echo FAIL: push& exit /b 1)
echo       OK.

echo [4/4] Done. Watch: https://github.com/Lance-Chen/timeseries-expand/actions
endlocal