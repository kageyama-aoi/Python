@echo off
cd /d %~dp0

for /F "tokens=2" %%i in ("date /t") do set mydate=%%i
set mydate=%mydate:/=%
set mydate=%date:/=%
REM set mytime=%time::=-%
set mytime=%time::=%
set filename=error_%mydate%_%mytime%.txt
dir > %filename%
SET output=%filename%
REM SET output=kageyama.txt

@echo on
python main.py 2> ./error_log/%output%
REM python ./00_MAIN/summary_kousuu_2024_1106.py 1>%output% 2>&1
REM python bugreport.py
parse
exit 0
