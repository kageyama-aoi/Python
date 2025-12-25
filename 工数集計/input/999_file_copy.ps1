# UTF-8 with BOM で保存してください

# --- 設定 ---
# 検索対象のフォルダ
$downloadDir = "C:\Users\kageyama\Tools\Python\01_勤怠自動化\data\downloads"

# コピー先のフォルダ (このスクリプトがある場所)
$inputDir = $PSScriptRoot

# ターゲットのファイル名
$targetName = "timesheet.csv"
$targetPath = Join-Path -Path $inputDir -ChildPath $targetName

# --- 処理開始 ---

# 1. ダウンロードフォルダから最新のtimesheetファイルを探す
# Get-ChildItem で取得し、最終書込日時でソートして先頭を取得
$latestFile = Get-ChildItem -Path $downloadDir -Filter "timesheet_*.csv" -File 2>$null | 
              Sort-Object LastWriteTime -Descending | 
              Select-Object -First 1

# 2. ファイルが見つからなかった場合は、メッセージを表示して終了
if ($null -eq $latestFile) {
    Write-Host "[エラー] `"$downloadDir`" 内に timesheet_*.csv ファイルが見つかりませんでした。" -ForegroundColor Red
    pause
    exit
}

Write-Host "最新のファイルが見つかりました: $($latestFile.Name)"
Write-Host ""

# 3. コピー先に同名ファイルが存在する場合、上書きを確認する
if (Test-Path -Path $targetPath) {
    Write-Host "`"$targetName`" が既に存在します。"
    $confirm = Read-Host "上書きしますか？ (Y/N)"
    if ($confirm -notlike "Y*") {
        Write-Host ""
        Write-Host "操作がキャンセルされました。"
        pause
        exit
    }
    Write-Host ""
    Write-Host "上書きを実行します..."
}

# 4 & 5. ファイルをコピーする
try {
    # 既存ファイルがある場合は強制上書き (-Force)
    Copy-Item -Path $latestFile.FullName -Destination $targetPath -Force -ErrorAction Stop
    
    Write-Host ""
    Write-Host "ファイルをコピーし、`"$targetName`" にリネームしました。"
    Write-Host "保存先: $targetPath"
}
catch {
    Write-Host ""
    Write-Host "[エラー] ファイルのコピーに失敗しました。" -ForegroundColor Red
    Write-Host "コピー元: $($latestFile.FullName)"
    Write-Host "コピー先: $targetPath"
    Write-Host ""
    Write-Host "以下の点を確認してください:"
    Write-Host "   - コピー元ファイルが他のプログラムで開かれていないか"
    Write-Host "   - コピー先フォルダに書き込み権限があるか"
    Write-Host "詳細エラー: $($_.Exception.Message)"
}

Write-Host ""
pause