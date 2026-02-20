$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

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
    $choice = Read-Host "Enter number"

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
                & powershell -ExecutionPolicy Bypass -File "$ProjectRoot\scripts\deploy_toolkit.ps1" -TargetDir $target
            }
            Write-Host ""
            Read-Host "Press Enter to return to menu"
        }
        "9" {
            break
        }
        default {
            Write-Host "Invalid input. Use 1, 2, 3, or 9." -ForegroundColor Yellow
            Start-Sleep -Seconds 1
        }
    }
}
