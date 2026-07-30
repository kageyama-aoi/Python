@echo off
cd /d "%~dp0"
python "src\gui.py" %*
if errorlevel 1 pause
