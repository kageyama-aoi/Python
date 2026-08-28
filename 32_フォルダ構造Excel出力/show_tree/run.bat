@echo off
cd /d "%~dp0"
python show_tree_gui.py
if errorlevel 1 pause
