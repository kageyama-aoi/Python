@echo off
cd /d "%~dp0"
python launcher_gui.py
if errorlevel 1 pause
