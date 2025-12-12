@echo off
cd /d %~dp0

REM --- 安定した方法で日付と時刻からファイル名を作成 (YYYYMMDD_HHMMSS形式) ---
set "DATETIME=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "DATETIME=%DATETIME: =0%"
set "filename=error_%DATETIME%.txt"

SET output=%filename%

@echo on
REM --- Pythonスクリプトを実行し、エラー出力をerror_logフォルダにリダイレクト ---
python ./main.py 2> "./error_log/%output%"

REM --- ユーザーが結果を確認できるように一時停止 ---
pause
exit
