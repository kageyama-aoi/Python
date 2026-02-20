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

Write-Host "=== Portal start ==="
Write-Host "Working directory: $projectRoot"
Write-Host "URL: http://127.0.0.1:5000/"
Write-Host ""

try {
    Start-Process "http://127.0.0.1:5000/" -ErrorAction Stop
} catch {
    Write-Host "[WARN] Could not auto-open browser. Open this URL manually: http://127.0.0.1:5000/" -ForegroundColor Yellow
}

python app.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] app.py failed." -ForegroundColor Red
    pause
    exit 1
}
