@echo off
REM Python 実行環境が通っている前提で、main.py を実行します

REM カレントディレクトリをスクリプトの場所に移動
cd /d "%~dp0"

REM 実行ログを表示しながら起動
echo 起動中...ウィンドウが開くまで少々お待ちください
python -m src.main

pause
