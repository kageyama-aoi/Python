# Convert-MdToHtml.ps1
# カレントディレクトリの .md を一律変換して output フォルダへ配置

$Current = Get-Location
$OutDir = Join-Path $Current "output"

# フォルダが無ければ作る
if (!(Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

Get-ChildItem -Path $Current -Filter "*.md" | ForEach-Object {

    $InFile = $_.FullName
    $OutFile = Join-Path $OutDir ($_.BaseName + ".html")

    # pandoc 実行
    pandoc $InFile -o $OutFile --standalone

    Write-Host "変換: $($_.Name) → $($OutFile)"
}

Write-Host "完了: $($OutDir)"
