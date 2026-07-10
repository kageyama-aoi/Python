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
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

$script:okCount = 0
$script:ngCount = 0
$script:warnCount = 0

function Write-Ok([string]$Message) {
    $script:okCount++
    Write-Host "[OK]   $Message" -ForegroundColor Green
}

function Write-Ng([string]$Message, [string]$Hint) {
    $script:ngCount++
    Write-Host "[NG]   $Message" -ForegroundColor Red
    if ($Hint) { Write-Host "       -> $Hint" -ForegroundColor Red }
}

function Write-Warn([string]$Message, [string]$Hint) {
    $script:warnCount++
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
    if ($Hint) { Write-Host "       -> $Hint" -ForegroundColor Yellow }
}

Write-Host "=== Health Check ==="
Write-Host "Project: $projectRoot"
Write-Host ""

# --- 1. Python ---
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $pythonVersion = (& python --version 2>&1) -join " "
    Write-Ok "Python found: $pythonVersion ($($pythonCmd.Source))"
} else {
    Write-Ng "Python not found in PATH." "Install Python or fix PATH, then re-run."
    Write-Host ""
    Write-Host "Result: NG=$script:ngCount (aborted: remaining checks need Python)" -ForegroundColor Red
    exit 1
}

# --- 2. Required modules ---
foreach ($module in @("markdown", "flask")) {
    & python -c "import $module" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Python module '$module' importable."
    } else {
        Write-Ng "Python module '$module' is missing." "Run: pip install $module"
    }
}

# --- 3. Required directories ---
foreach ($dir in @("md", "html", "picture")) {
    if (Test-Path -LiteralPath (Join-Path $projectRoot $dir) -PathType Container) {
        Write-Ok "Directory '$dir' exists."
    } else {
        Write-Ng "Directory '$dir' is missing." "Run: mkdir $dir (in $projectRoot)"
    }
}

# --- 4. app.py route check (in-process, no server needed) ---
$routeCheckScript = @'
import sys
try:
    from app import app
except Exception as exc:
    print(f"IMPORT_ERROR: {exc}")
    sys.exit(1)
client = app.test_client()
failed = False
for route in ("/", "/import", "/kb/"):
    status = client.get(route).status_code
    if route == "/kb/" and status == 404:
        print(f"ROUTE_WARN {route} {status}")
    elif status == 200:
        print(f"ROUTE_OK {route} {status}")
    else:
        print(f"ROUTE_NG {route} {status}")
        failed = True
sys.exit(1 if failed else 0)
'@
$routeOutput = & python -c $routeCheckScript 2>&1
foreach ($line in $routeOutput) {
    $text = "$line".Trim()
    if (-not $text) { continue }
    if ($text.StartsWith("ROUTE_OK")) {
        $parts = $text.Split(" ")
        Write-Ok "Route $($parts[1]) responded $($parts[2])."
    } elseif ($text.StartsWith("ROUTE_WARN")) {
        $parts = $text.Split(" ")
        Write-Warn "Route $($parts[1]) responded $($parts[2]) (html/index.html not built)." "Run: python build.py"
    } elseif ($text.StartsWith("ROUTE_NG")) {
        $parts = $text.Split(" ")
        Write-Ng "Route $($parts[1]) responded $($parts[2])." "Check app.py for errors."
    } elseif ($text.StartsWith("IMPORT_ERROR")) {
        Write-Ng "app.py could not be imported: $text" "Check dependencies and app.py syntax."
    } else {
        Write-Warn "Unexpected route-check output: $text"
    }
}
if ($LASTEXITCODE -ne 0 -and -not ("$routeOutput" -match "ROUTE_NG|IMPORT_ERROR")) {
    Write-Ng "Route check exited abnormally." "Run manually: python -c `"from app import app`""
}

# --- Summary ---
Write-Host ""
if ($script:ngCount -eq 0) {
    Write-Host "Result: all checks passed (OK=$script:okCount, WARN=$script:warnCount)" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Result: NG=$script:ngCount, WARN=$script:warnCount, OK=$script:okCount" -ForegroundColor Red
    exit 1
}
