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

$ScriptDir = Split-Path -Parent $scriptPath
if (-not $ScriptDir) { throw "Cannot resolve script directory." }

$ProjectRoot = Split-Path -Parent $ScriptDir
if (-not $ProjectRoot) { throw "Cannot resolve project root." }

Set-Location $ProjectRoot

function Normalize-Choice([string]$Text) {
    if ($null -eq $Text) { return "" }
    $s = $Text.Normalize([Text.NormalizationForm]::FormKC).Trim()
    return $s
}

while ($true) {
    Clear-Host
    Write-Host "====================================="
    Write-Host " Markdown to HTML - Start Menu"
    Write-Host "====================================="
    Write-Host "1) Build (update html/index.html)"
    Write-Host "2) Start portal (meta editor UI)"
    Write-Host "3) Deploy toolkit to another directory"
    Write-Host "9) Exit"
    Write-Host ""
    $choice = Normalize-Choice (Read-Host "Enter number")

    switch ($choice) {
        "1" {
            & powershell -ExecutionPolicy Bypass -File "$ProjectRoot\scripts\run_build.ps1"
            Write-Host ""
            Read-Host "Press Enter to return to menu"
        }
        "2" {
            & powershell -ExecutionPolicy Bypass -File "$ProjectRoot\scripts\run_portal.ps1"
            Write-Host ""
            Read-Host "Press Enter to return to menu"
        }
        "3" {
            $target = Read-Host "Target directory path"
            if ([string]::IsNullOrWhiteSpace($target)) {
                Write-Host "Target directory is required." -ForegroundColor Yellow
            } else {
                try {
                    & powershell -ExecutionPolicy Bypass -File "$ProjectRoot\scripts\deploy_toolkit.ps1" -TargetDir $target
                } catch {
                    Write-Host "[ERROR] Deploy failed: $($_.Exception.Message)" -ForegroundColor Red
                }
            }
            Write-Host ""
            Read-Host "Press Enter to return to menu"
        }
        "9" {
            break
        }
        default {
            Write-Host "Invalid input: '$choice' (use 1, 2, 3, or 9)." -ForegroundColor Yellow
            Start-Sleep -Seconds 1
        }
    }
}
