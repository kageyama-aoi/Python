@echo off
setlocal

REM エラーログのパスを指定 (新しいlogsディレクトリ内を指すように変更)
set LOG_DIR=logs\batch_error_logs
set LOG_FILE=%LOG_DIR%\validation_error_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log

REM ログディレクトリが存在しない場合は作成
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Pythonスクリプトのパスを変更
python src\main.py kensho 2>> %LOG_FILE%
@REM python 00_MAIN\create_task_report.py kensho 2>> %LOG_FILE%

endlocal
pause