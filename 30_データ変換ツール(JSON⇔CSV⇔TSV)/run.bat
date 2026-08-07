@echo off
cd /d "%~dp0"
python "src\launcher_gui.py"
if errorlevel 1 pause
