param(
    [Parameter(Mandatory = $true)]
    [string]$TargetDir,
    [switch]$IncludeDocs,
    [switch]$IncludeSupportTool,
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Resolve-ScriptPath {
    if ($PSCommandPath) { return $PSCommandPath }
    if ($MyInvocation -and $MyInvocation.MyCommand -and $MyInvocation.MyCommand.Path) {
        return $MyInvocation.MyCommand.Path
    }
    throw "Cannot resolve script path."
}

function Ensure-Dir([string]$PathText) {
    if (-not (Test-Path -LiteralPath $PathText)) {
        New-Item -ItemType Directory -Path $PathText -Force | Out-Null
    }
}

function Copy-IfNeeded([string]$SourcePath, [string]$DestPath, [switch]$ForceOverwrite, [switch]$DryRunMode) {
    $destParent = Split-Path -Parent $DestPath
    Ensure-Dir $destParent

    if ($DryRunMode) {
        if (Test-Path -LiteralPath $DestPath) {
            Write-Host "[DRYRUN] update $DestPath"
        } else {
            Write-Host "[DRYRUN] create $DestPath"
        }
        return
    }

    if ((Test-Path -LiteralPath $DestPath) -and (-not $ForceOverwrite)) {
        Write-Host "[SKIP] $DestPath already exists (use -Force to overwrite)" -ForegroundColor Yellow
        return
    }

    Copy-Item -LiteralPath $SourcePath -Destination $DestPath -Force:$ForceOverwrite
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
if ([System.IO.Path]::IsPathRooted($targetInput)) {
    $targetRoot = [System.IO.Path]::GetFullPath($targetInput)
} else {
    $targetRoot = [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $targetInput))
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
