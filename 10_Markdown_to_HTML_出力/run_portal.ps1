$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "=== Portal start ==="
Write-Host "Working directory: $ScriptDir"
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
