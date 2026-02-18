@echo off
cd /d "%~dp0"

echo === Portal start ===
echo Working directory: %cd%
echo URL: http://127.0.0.1:5000/
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0run_portal.ps1"
