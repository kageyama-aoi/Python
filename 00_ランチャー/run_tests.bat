@echo off
cd /d "%~dp0"
python -m unittest discover -v tests
pause
