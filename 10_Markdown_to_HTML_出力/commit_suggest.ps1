$ErrorActionPreference = "Stop"

$promptFile = Join-Path $PSScriptRoot "commit_prompt.md"

if (-not (Test-Path $promptFile)) {
    Write-Error "commit_prompt.md not found: $promptFile"
    exit 1
}

if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    Write-Error "codex command not found. Check installation and PATH."
    exit 1
}

$stagedDiff = git diff --staged 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to run 'git diff --staged'. Run this inside a Git repository."
    exit 1
}

if ([string]::IsNullOrWhiteSpace(($stagedDiff | Out-String))) {
    Write-Error "No staged diff found. Run git add first."
    exit 1
}

$prompt = Get-Content -Raw -Encoding UTF8 $promptFile
$fullPrompt = $prompt + [Environment]::NewLine + [Environment]::NewLine + ($stagedDiff | Out-String)

$fullPrompt | codex exec -
