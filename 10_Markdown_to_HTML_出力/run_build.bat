@echo off
REM Move to this .bat directory
cd /d "%~dp0"

echo === Markdown build start ===
echo Working directory: %cd%
echo.

REM Run PowerShell wrapper
powershell -ExecutionPolicy Bypass -File "%~dp0run_build.ps1"

REM Check exit code
if errorlevel 1 (
    echo.
    echo [ERROR] build.py failed.
    pause
    exit /b 1
)

echo.
echo [OK] build.py completed.

REM Open generated index.html automatically
if exist "%~dp0html\index.html" (
    start "" "%~dp0html\index.html"
) else (
    echo [WARN] html\index.html was not found.
)

pause
