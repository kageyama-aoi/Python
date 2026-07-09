@echo off
cd /d "%~dp0"
python merge_pdfs_from_list.py -l inputs.txt -o output\merged.pdf
pause
