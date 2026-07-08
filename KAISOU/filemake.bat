@echo off
setlocal

:: 作成したいファイル名を配列的に書く
set FILES=generate_drive_structure.py run_drive_structure.bat

for %%F in (%FILES%) do (
    if not exist "%%F" (
        echo Creating %%F...
        type NUL > "%%F"
    ) else (
        echo File %%F already exists. Skipping.
    )
)

echo Done.
endlocal
pause