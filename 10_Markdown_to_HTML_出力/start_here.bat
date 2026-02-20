@echo off
cd /d "%~dp0"

echo === Start Menu ===
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\start_here.ps1"
