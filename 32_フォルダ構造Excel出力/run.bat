@echo off
cd /d "%~dp0"
python "src\generate_drive_structure.py"
if errorlevel 1 pause
