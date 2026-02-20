$ErrorActionPreference = "Stop"

function Resolve-ScriptPath {
    if ($PSCommandPath) { return $PSCommandPath }
    if ($MyInvocation -and $MyInvocation.MyCommand -and $MyInvocation.MyCommand.Path) {
        return $MyInvocation.MyCommand.Path
    }
    throw "Cannot resolve script path."
}

function Test-PortAvailable([int]$Port) {
    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), $Port)
        $listener.Start()
        return $true
    } catch {
        return $false
    } finally {
        if ($listener -ne $null) {
            try { $listener.Stop() } catch {}
        }
    }
}

function Find-FreePort([int]$StartPort, [int]$MaxPort) {
    for ($p = $StartPort; $p -le $MaxPort; $p++) {
        if (Test-PortAvailable -Port $p) {
            return $p
        }
    }
    throw "No free port found in range $StartPort-$MaxPort."
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

$startPort = 5000
$maxPort = 5010
$selectedPort = Find-FreePort -StartPort $startPort -MaxPort $maxPort
$url = "http://127.0.0.1:$selectedPort/"

Write-Host "=== Portal start ==="
Write-Host "Working directory: $projectRoot"
Write-Host "URL: $url"
if ($selectedPort -ne 5000) {
    Write-Host "[WARN] Port 5000 is already in use. Using port $selectedPort." -ForegroundColor Yellow
}
Write-Host ""

try {
    Start-Process $url -ErrorAction Stop
} catch {
    Write-Host "[WARN] Could not auto-open browser. Open this URL manually: $url" -ForegroundColor Yellow
}

$env:PORT = [string]$selectedPort
python app.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] app.py failed." -ForegroundColor Red
    pause
    exit 1
}
