# Repository Guidelines

## Project Structure & Module Organization
- `build.py`: Core build script that converts Markdown to HTML and generates `html/index.html`.
- `md/`: Source Markdown files (`*.md`) to be converted.
- `html/`: Build output, including per-file HTML, `index.html`, and `style.css`.
- `docs/`: Stable/official documentation for long-term reference.
- `notes/`: Working notes and interim documents.
  - `notes/issue/`: Issue drafts and issue-operation notes.
  - `notes/operations/`: Operation memos, proposals, and implementation logs.
  - `notes/archive/`: Archived notes.
- `run_build.ps1` / `run_build.bat`: Convenience wrappers to run the build from PowerShell or CMD.
- `PROMPT.md`: Prompt template for rewriting plain Markdown into “styled” Markdown with CSS classes.
- `README.md`: Usage overview and dependencies.

## Documentation Placement Rules
- Put long-lived user-facing docs in `docs/`.
- Put temporary/interim working memos in `notes/`.
- Do not mix interim notes into `docs/`; move completed-but-nonofficial records to `notes/archive/` when needed.

## Build, Test, and Development Commands
- `python build.py`: Runs environment checks and converts all `md/*.md` into `html/`.
- `.\run_build.ps1`: PowerShell wrapper that calls `python build.py`.
- `run_build.bat`: CMD wrapper that launches the PowerShell script.
- `pip install markdown pymdown-extensions`: Installs required Markdown libraries. The `pymdown-extensions` package enables task list (`- [ ]`) rendering.

## Coding Style & Naming Conventions
- Python: 4-space indentation, PEP 8 style.
- Directory names `md` and `html` are hardcoded in `build.py`; do not rename them.
- Markdown filenames become HTML titles and output filenames (e.g., `md/Example.md` → `html/Example.html`).
- Use CSS classes in Markdown for emphasis: `warn`, `alert`, `danger`, `note` (see `html/style.css`).

## Testing Guidelines
- No automated tests are currently defined.
- If tests are added, document the framework, naming convention (e.g., `test_*.py`), and execution command here.

## Commit & Pull Request Guidelines
- Use concise, imperative commit messages (e.g., “Add task list support”).
- For PRs, include: summary of changes, verification steps (e.g., “ran `python build.py`”), and screenshots if HTML output changed.

## Issue-First Workflow (Required)
- Before starting implementation, always create a GitHub Issue first.
- Use the templates under `.github/ISSUE_TEMPLATE/` and select the closest type (`bug_report`, `feature_request`, `question`, `task_memo`).
- Define scope and completion criteria in the Issue, then start development.
- Link related commits/PRs to the Issue (include issue number in commit message or PR description).
- If work starts as an ad-hoc task, create the Issue before the first code commit.

## Security & Configuration Tips
- The build writes to `html/` and creates a temporary `.write_test` file during permission checks.
- Ensure `html/` is writable before running builds, especially on shared or synced drives.
