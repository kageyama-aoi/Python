$ErrorActionPreference = "Stop"

# Force UTF-8 to avoid mojibake in prompt/diff piping.
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
try { chcp 65001 > $null } catch {}

$repoRoot = Split-Path -Parent $PSScriptRoot
$promptCandidates = @(
    (Join-Path $PSScriptRoot "commit_prompt.md"),
    (Join-Path $repoRoot "commit_prompt.md"),
    (Join-Path $repoRoot "docs\\COMMIT_MESSAGE_INSTRUCTIONS.md")
)
$promptFile = $promptCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $promptFile) {
    Write-Error "Prompt file not found. Expected one of: scripts\\commit_prompt.md, commit_prompt.md, docs\\COMMIT_MESSAGE_INSTRUCTIONS.md"
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
