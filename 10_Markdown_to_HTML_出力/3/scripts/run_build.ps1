$ErrorActionPreference = "Stop"

function Resolve-ScriptPath {
    if ($PSCommandPath) { return $PSCommandPath }
    if ($MyInvocation -and $MyInvocation.MyCommand -and $MyInvocation.MyCommand.Path) {
        return $MyInvocation.MyCommand.Path
    }
    throw "Cannot resolve script path."
}

$scriptPath = Resolve-ScriptPath
if (-not [System.IO.Path]::IsPathRooted($scriptPath)) {
    $scriptPath = (Resolve-Path $scriptPath).Path
}

$scriptDir = Split-Path -Parent $scriptPath
if (-not $scriptDir) { throw "Cannot resolve script directory." }

$projectRoot = Split-Path -Parent $scriptDir
if (-not $projectRoot) { throw "Cannot resolve project root." }

Set-Location $projectRoot

Write-Host "=== Markdown build start ==="
Write-Host "Working directory: $projectRoot"
Write-Host ""

python build.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] build.py failed." -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "[OK] build.py completed."
pause
