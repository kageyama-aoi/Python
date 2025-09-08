@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM --- 設定 ---
REM 検索対象のフォルダ
set "download_dir=%USERPROFILE%\Downloads"
REM コピー先のフォルダ (このバッチファイルから見て一つ上の階層のinputフォルダ)
set "input_dir=%~dp0..\\input\\"


REM --- 処理開始 ---

REM 1. ダウンロードフォルダから最新のtimesheetファイルを探す
set "latest_file="
for /f "delims=" %%i in ('dir /b /a-d /o-d "%download_dir%\timesheet_*.csv" 2^>nul') do (
    if not defined latest_file set "latest_file=%%i"
)

REM 2. ファイルが見つからなかった場合は、メッセージを表示して終了
if not defined latest_file (
    echo [エラー] "%download_dir%" 内に timesheet_*.csv ファイルが見つかりませんでした。
    goto :end
)

echo 最新のファイルが見つかりました: !latest_file!
echo.

REM 3. コピー先に同名ファイルが存在する場合、上書きを確認する
if not exist "%input_dir%timesheet.csv" goto :do_copy

REM --- ファイルが存在する場合の確認処理 ---
echo "timesheet.csv" が既に存在します。
<nul set /p "=.上書きしますか？ (Y/N): "
set /p "confirm="
if /i not "!confirm!"=="Y" (
    echo.
    echo 操作がキャンセルされました。
    goto :end
)
echo.
echo 上書きを実行します...


:do_copy
REM 4. ファイルをコピーする
copy /y "%download_dir%\!latest_file!" "%input_dir%timesheet.csv" >nul 2>&1

REM 5. コピー処理の結果を確認する
if !errorlevel! neq 0 (
  echo.
  echo [エラー] ファイルのコピーに失敗しました。
  echo コピー元: "%download_dir%\!latest_file!"
  echo コピー先: "%input_dir%timesheet.csv"
  echo.
  echo 以下の点を確認してください:
  echo   - コピー元ファイルが他のプログラムで開かれていないか
  echo   - コピー先フォルダに書き込み権限があるか
  goto :end
)

echo.
echo ファイルをコピーし、"timesheet.csv" にリネームしました。
echo 保存先: "%input_dir%timesheet.csv"


:end
echo.
endlocal
pause
