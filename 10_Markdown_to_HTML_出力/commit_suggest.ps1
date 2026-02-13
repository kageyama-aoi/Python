$ErrorActionPreference = "Stop"

# Force UTF-8 to avoid mojibake in prompt/diff piping.
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
try { chcp 65001 > $null } catch {}

$promptFile = Join-Path $PSScriptRoot "commit_prompt.md"

if (-not (Test-Path $promptFile)) {
    Write-Error "commit_prompt.md not found: $promptFile"
    exit 1
}

if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    Write-Error "codex command not found. Check installation and PATH."
    exit 1
}

$stagedDiff = git -c core.quotepath=false diff --staged --no-color 2>&1
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
