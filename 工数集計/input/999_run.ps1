Set-Location $PSScriptRoot

$datetime = Get-Date -Format "yyyyMMdd_HHmmss"
$filename = "error_$datetime.txt"

Set-Location "C:\Users\kageyama\Tools\Python\工数集計"

$logPath = Join-Path "error_log" $filename

python main.py 2> $logPath

Write-Host "処理完了"
Write-Host "エラーログ: $logPath"
Pause
