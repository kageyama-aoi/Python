param(
    [Parameter(Mandatory = $true)]
    [string]$TargetDir,
    [switch]$IncludeDocs,
    [switch]$IncludeSupportTool,
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Throw-PathError([string]$Action, [string]$PathText, [System.Exception]$ErrorObj) {
    $reason = if ($ErrorObj) { $ErrorObj.Message } else { "unknown error" }
    throw "[ERROR] $Action failed.`nPath: $PathText`nReason: $reason`nNext: Check path format, access permission, and drive availability."
}

function Resolve-ScriptPath {
    if ($PSCommandPath) { return $PSCommandPath }
    if ($MyInvocation -and $MyInvocation.MyCommand -and $MyInvocation.MyCommand.Path) {
        return $MyInvocation.MyCommand.Path
    }
    throw "Cannot resolve script path."
}

function Ensure-Dir([string]$PathText) {
    try {
        if (-not (Test-Path -LiteralPath $PathText)) {
            New-Item -ItemType Directory -Path $PathText -Force | Out-Null
        }
    } catch {
        Throw-PathError -Action "Ensure directory" -PathText $PathText -ErrorObj $_.Exception
    }
}

function Copy-IfNeeded([string]$SourcePath, [string]$DestPath, [switch]$ForceOverwrite, [switch]$DryRunMode) {
    $destParent = Split-Path -Parent $DestPath
    Ensure-Dir $destParent

    if ($DryRunMode) {
        $exists = $false
        try {
            $exists = Test-Path -LiteralPath $DestPath
        } catch {
            Throw-PathError -Action "Check destination in dry-run" -PathText $DestPath -ErrorObj $_.Exception
        }
        if ($exists) {
            Write-Host "[DRYRUN] update $DestPath"
        } else {
            Write-Host "[DRYRUN] create $DestPath"
        }
        return
    }

    $destExists = $false
    try {
        $destExists = Test-Path -LiteralPath $DestPath
    } catch {
        Throw-PathError -Action "Check destination" -PathText $DestPath -ErrorObj $_.Exception
    }

    if ($destExists -and (-not $ForceOverwrite)) {
        Write-Host "[SKIP] $DestPath already exists (use -Force to overwrite)" -ForegroundColor Yellow
        return
    }

    try {
        Copy-Item -LiteralPath $SourcePath -Destination $DestPath -Force:$ForceOverwrite
    } catch {
        Throw-PathError -Action "Copy file" -PathText $DestPath -ErrorObj $_.Exception
    }
    Write-Host "[OK]   copied $DestPath"
}

$scriptPath = Resolve-ScriptPath
$scriptDir = Split-Path -Parent $scriptPath
$projectRoot = Split-Path -Parent $scriptDir
$manifestPath = Join-Path $scriptDir "toolkit_manifest.json"

if (-not (Test-Path -LiteralPath $manifestPath)) {
    throw "Manifest not found: $manifestPath"
}

$manifest = Get-Content -Raw -Encoding UTF8 $manifestPath | ConvertFrom-Json
$targetInput = "$TargetDir"
$targetInput = $targetInput.Trim().Trim('"')
if ([string]::IsNullOrWhiteSpace($targetInput)) {
    throw "TargetDir is empty."
}
try {
    if ([System.IO.Path]::IsPathRooted($targetInput)) {
        $targetRoot = [System.IO.Path]::GetFullPath($targetInput)
    } else {
        $targetRoot = [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $targetInput))
    }
} catch {
    Throw-PathError -Action "Resolve target path" -PathText $targetInput -ErrorObj $_.Exception
}

Write-Host "=== Deploy Toolkit ==="
Write-Host "Source: $projectRoot"
Write-Host "Target: $targetRoot"
Write-Host "Mode  : $(if ($DryRun) { 'DRYRUN' } else { 'COPY' })"
Write-Host ""

Ensure-Dir $targetRoot

foreach ($dir in $manifest.create_dirs) {
    $destDir = Join-Path $targetRoot $dir
    if ($DryRun) {
        Write-Host "[DRYRUN] ensure dir $destDir"
    } else {
        Ensure-Dir $destDir
        Write-Host "[OK]   ensured dir $destDir"
    }
}

$filesToCopy = @()
$filesToCopy += $manifest.files
if ($IncludeDocs) { $filesToCopy += $manifest.docs_files }
if ($IncludeSupportTool) { $filesToCopy += $manifest.support_files }

foreach ($rel in $filesToCopy) {
    $src = Join-Path $projectRoot $rel
    if (-not (Test-Path -LiteralPath $src)) {
        Write-Host "[WARN] missing source: $rel" -ForegroundColor Yellow
        continue
    }
    $dst = Join-Path $targetRoot $rel
    Copy-IfNeeded -SourcePath $src -DestPath $dst -ForceOverwrite:$Force -DryRunMode:$DryRun
}

Write-Host ""
Write-Host "Done."
Write-Host "Next: open '$targetRoot' and run 'start_here.bat'."
