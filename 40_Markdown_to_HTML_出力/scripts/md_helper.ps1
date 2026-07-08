param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("link", "image")]
    [string]$Mode,

    [Parameter(Mandatory = $true)]
    [string]$TargetPath,

    [string]$Label = "",

    [string]$FromPath = "",

    [switch]$Copy
)

$ErrorActionPreference = "Stop"

function Get-FullPath([string]$PathText, [string]$BaseDir) {
    if ([System.IO.Path]::IsPathRooted($PathText)) {
        return [System.IO.Path]::GetFullPath($PathText)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $BaseDir $PathText))
}

function Get-RelativePathCompat([string]$BaseDir, [string]$TargetPath) {
    $basePath = [System.IO.Path]::GetFullPath($BaseDir)
    $targetFull = [System.IO.Path]::GetFullPath($TargetPath)

    if (-not $basePath.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $basePath += [System.IO.Path]::DirectorySeparatorChar
    }

    $baseUri = [System.Uri]$basePath
    $targetUri = [System.Uri]$targetFull
    $relativeUri = $baseUri.MakeRelativeUri($targetUri)
    $relativePath = [System.Uri]::UnescapeDataString($relativeUri.ToString())
    return $relativePath.Replace("\", "/")
}

function Resolve-BaseDir([string]$FromPathText, [string]$CurrentDir) {
    if ([string]::IsNullOrWhiteSpace($FromPathText)) {
        return $CurrentDir
    }

    if (Test-Path $FromPathText) {
        $resolved = (Resolve-Path $FromPathText).Path
        if (Test-Path $resolved -PathType Container) {
            return $resolved
        }
        return (Split-Path -Parent $resolved)
    }

    $full = Get-FullPath -PathText $FromPathText -BaseDir $CurrentDir
    if ([System.IO.Path]::HasExtension($full)) {
        return (Split-Path -Parent $full)
    }
    return $full
}

$currentDir = (Get-Location).Path
$baseDir = Resolve-BaseDir -FromPathText $FromPath -CurrentDir $currentDir
$targetFullPath = Get-FullPath -PathText $TargetPath -BaseDir $currentDir

$relativePath = Get-RelativePathCompat -BaseDir $baseDir -TargetPath $targetFullPath

$fallbackLabel = [System.IO.Path]::GetFileNameWithoutExtension($targetFullPath)
if ([string]::IsNullOrWhiteSpace($fallbackLabel)) {
    $fallbackLabel = "link"
}
$finalLabel = if ([string]::IsNullOrWhiteSpace($Label)) { $fallbackLabel } else { $Label }

$snippet = switch ($Mode) {
    "link" { "[$finalLabel]($relativePath)" }
    "image" { "![${finalLabel}]($relativePath)" }
}

if ($Copy) {
    Set-Clipboard -Value $snippet
    Write-Output $snippet
    Write-Output "Copied to clipboard."
    exit 0
}

Write-Output $snippet
