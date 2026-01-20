@echo off
rem This batch file executes the PowerShell test runner script.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0run_tests.ps1"
pause
