@echo off
chcp 65001 > nul
setlocal

REM ========================================================
REM テスト実行スクリプト
REM 使い方: tests\run_tests.bat
REM 結果は .output\test_YYYYMMDD_HHMMSS.txt に保存される
REM ========================================================

REM プロジェクトルートに移動
cd /d "%~dp0.."

REM 出力先ディレクトリ
if not exist ".output" mkdir ".output"

REM タイムスタンプ生成
set TIMESTAMP=%DATE:~0,4%-%DATE:~5,2%-%DATE:~8,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set OUTPUT_FILE=.output\test_%TIMESTAMP%.txt

echo ===================================================
echo  テスト実行: %DATE% %TIME%
echo ===================================================
echo.

REM pytest 実行（コンソールに表示しつつファイルにも保存）
python -m pytest tests/ -v --tb=short > "%OUTPUT_FILE%" 2>&1
set EXIT_CODE=%ERRORLEVEL%

REM 結果をコンソールにも表示
type "%OUTPUT_FILE%"

echo.
echo ===================================================
if %EXIT_CODE% == 0 (
    echo  [PASS] 全テスト成功
) else (
    echo  [FAIL] 失敗したテストがあります
)
echo  結果を保存しました: %OUTPUT_FILE%
echo ===================================================

exit /b %EXIT_CODE%
