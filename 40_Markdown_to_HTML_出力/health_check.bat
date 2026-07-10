@echo off
cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -File "%~dp0scripts\health_check.ps1"

echo.
pause
