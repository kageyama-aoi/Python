# Repository Guidelines

## Project Structure & Module Organization
- `build.py`: Core build script that converts Markdown to HTML and generates `html/index.html`.
- `md/`: Source Markdown files (`*.md`) to be converted.
- `html/`: Build output, including per-file HTML, `index.html`, and `style.css`.
- `run_build.ps1` / `run_build.bat`: Convenience wrappers to run the build from PowerShell or CMD.
- `PROMPT.md`: Prompt template for rewriting plain Markdown into “styled” Markdown with CSS classes.
- `README.md`: Usage overview and dependencies.

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
- This folder is not under Git control (no `.git` present), so there is no commit history to follow.
- If you initialize Git later, use concise, imperative commit messages (e.g., “Add task list support”).
- For PRs, include: summary of changes, verification steps (e.g., “ran `python build.py`”), and screenshots if HTML output changed.

## Security & Configuration Tips
- The build writes to `html/` and creates a temporary `.write_test` file during permission checks.
- Ensure `html/` is writable before running builds, especially on shared or synced drives.
