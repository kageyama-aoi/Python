# この .ps1 自身のあるディレクトリに移動
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "=== Markdown build 開始 ==="
Write-Host "作業ディレクトリ: $ScriptDir"
Write-Host ""

# Python 実行
python build.py

# 終了コード確認
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "⚠ build.py の実行に失敗しました" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "✅ build.py の実行が完了しました"
pause
