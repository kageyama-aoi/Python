@echo off
:: ↑ 余計なコマンド表示を消す（画面がスッキリ）

powershell ^
  -NoProfile ^
  -ExecutionPolicy Bypass ^
  -File "%~dp0run.ps1"
:: ↑ PowerShellを起動して run.ps1 を実行する
::   -NoProfile            = ユーザーのプロファイルを読み込まない（高速・安全）
::   -ExecutionPolicy Bypass = 実行ポリシーを一時的に無視する（警告回避）
::   -File "%~dp0run.ps1"  = このbatと同じ場所の run.ps1 を指定して実行
::     %~dp0 = batファイルがあるフォルダの絶対パス

pause
:: ↑ 実行が終わったあとに「続行するには何かキーを押してください...」で止まる
