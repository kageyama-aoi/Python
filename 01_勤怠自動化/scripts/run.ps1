# UTF-8 with BOM で保存してください

# スクリプトの実行場所を基準にプロジェクトルート（1つ上の階層）を特定
$ProjectRoot = Split-Path -Path $PSScriptRoot -Parent
Set-Location -Path $ProjectRoot

# ログディレクトリとファイル名の設定 (yyyyMMdd_HHmmss形式)
$LogDir = Join-Path -Path $ProjectRoot -ChildPath "logs\batch_error_logs"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path -Path $LogDir -ChildPath "validation_error_${Timestamp}.log"

# ログディレクトリが存在しない場合は作成
if (-not (Test-Path -Path $LogDir)) {
    New-Item -Path $LogDir -ItemType Directory -Force | Out-Null
}

# Pythonスクリプトの実行とエラー出力(2>)のログ記録
# $LASTEXITCODE で Python の終了ステータスを確認可能
try {
    python src\main.py kensho 2>> $LogFile
}
catch {
    Write-Error "Pythonの実行中に予期せぬエラーが発生しました。"
    $_ | Out-File -FilePath $LogFile -Append
}

# 終了待機
Write-Host "処理が完了しました。Enterキーを押すと終了します..."
$null = [Console]::ReadKey()