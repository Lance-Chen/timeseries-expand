@echo off
REM timeseries-expand v0.1.0 release script for Windows
REM Run from the project root: F:\ClaudeProject\Work_for_Jiang\timeseries-expand

setlocal

echo ==========================================
echo  timeseries-expand v0.1.0 Release Script
echo ==========================================
echo.

REM Step 1: Verify prerequisites
echo [1/8] Checking prerequisites...
where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: git not found. Install from https://git-scm.com/
    exit /b 1
)
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: python not found.
    exit /b 1
)
echo       OK: git and python found.
echo.

REM Step 2: Install dev dependencies if missing
echo [2/8] Checking dev dependencies...
python -c "import hypothesis" 2>nul
if errorlevel 1 (
    echo       Installing dev dependencies...
    pip install -e ".[dev]"
    if errorlevel 1 (
        echo ERROR: pip install failed.
        exit /b 1
    )
)
echo       OK: dependencies ready.
echo.

REM Step 3: Run tests
echo [3/8] Running tests...
set TZ=UTC
python -m pytest tests/ -q
if errorlevel 1 (
    echo ERROR: tests failed. Fix before releasing.
    exit /b 1
)
echo.

REM Step 4: Initialize git repository
echo [4/8] Initializing git repository...
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    REM No valid git repo - try to remove stale .git if it exists, then init fresh
    if exist .git (
        echo       Found stale .git directory, removing...
        rmdir /s /q .git
    )
    git init -b main
    if errorlevel 1 (
        echo ERROR: git init failed.
        exit /b 1
    )
    git config user.name "Lance-Chen"
    git config user.email "[email protected]"
    echo       Created new git repo on branch main.
) else (
    echo       Git repo already exists.
)
echo.

REM Step 5: Show what will be committed
echo [5/8] Files to be staged:
git status --short
echo.

REM Step 6: Create initial commit using a message file
echo [6/8] Creating initial commit...
git add .

REM Write commit message to a temp file (avoids batch escaping issues)
set MSG_FILE=%TEMP%\ts-expand-commit-msg.txt
> "%MSG_FILE%" echo feat: initial public release of timeseries-expand v0.1.0
>>"%MSG_FILE%" echo.
>>"%MSG_FILE%" echo - 21 frequency combinations (YE/QE/ME/SME/W-MON/D/h)
>>"%MSG_FILE%" echo - Publication-aware forward fill ([T, T_next) semantics)
>>"%MSG_FILE%" echo - Gap detection with configurable threshold
>>"%MSG_FILE%" echo - DST-safe (internal UTC, configurable display timezone)
>>"%MSG_FILE%" echo - 122 tests passing
>>"%MSG_FILE%" echo - 3 call patterns: functional, class-based, CLI

git commit -F "%MSG_FILE%"
if errorlevel 1 (
    echo ERROR: commit failed.
    del "%MSG_FILE%" 2>nul
    exit /b 1
)
del "%MSG_FILE%" 2>nul
echo       Commit created.
echo.

REM Step 7: Push to GitHub
echo [7/8] Pushing to GitHub...
set REMOTE_URL=https://github.com/Lance-Chen/timeseries-expand.git
git remote remove origin 2>nul
git remote add origin %REMOTE_URL%
echo       Remote URL: %REMOTE_URL%
echo.
echo       !! IMPORTANT !!
echo       Before continuing, create the empty GitHub repo at:
echo         https://github.com/new
echo         Repository name: timeseries-expand
echo         Visibility: Public
echo         DO NOT check any initialization boxes
echo.
set /p CONFIRM="Have you created the GitHub repo? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo Aborted. After creating the repo, run this script again.
    exit /b 1
)
echo.
git push -u origin main
if errorlevel 1 (
    echo ERROR: push failed. Check your GitHub credentials.
    exit /b 1
)
echo.

REM Step 8: Tag and create release notes
echo [8/8] Creating v0.1.0 tag...
git tag -a v0.1.0 -m "Release v0.1.0 - Initial public release"
git push origin v0.1.0
if errorlevel 1 (
    echo ERROR: tag push failed.
    exit /b 1
)
echo.
echo ==========================================
echo  SUCCESS! Repository pushed.
echo ==========================================
echo.
echo Next steps:
echo   1. Open https://github.com/Lance-Chen/timeseries-expand/releases
echo   2. Click "Draft a new release"
echo   3. Choose tag: v0.1.0
echo   4. Title: "v0.1.0 - Initial public release"
echo   5. Description: copy from CHANGELOG.md
echo   6. Click "Publish release"
echo.
echo Verify at: https://github.com/Lance-Chen/timeseries-expand
echo.

endlocal
