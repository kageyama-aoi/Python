@echo off
REM この bat 自身のあるディレクトリに移動
cd /d "%~dp0"

echo === Markdown build 開始 ===
echo 作業ディレクトリ: %cd%
echo.

REM PowerShell を呼び出す
powershell -ExecutionPolicy Bypass -File "%~dp0run_build.ps1"

REM 終了コード確認
if errorlevel 1 (
    echo.
    echo ? build.py の実行に失敗しました
    pause
    exit /b 1
)

echo.
echo ? build.py の実行が完了しました
pause
