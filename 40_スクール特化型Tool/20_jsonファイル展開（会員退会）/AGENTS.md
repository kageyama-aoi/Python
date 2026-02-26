# Repository Guidelines

## Project Structure & Module Organization
This repository is intentionally small and focused on visualizing membership-withdrawal JSON logic.
- `json_logic_viewer_mock.html`: Single-page viewer (HTML/CSS/vanilla JavaScript).
- `json/`: Sample input files such as `kaiin_taikai_YYYYMMDD_HHMMSS.JSON`.

Keep UI logic in the existing script block unless the project is split into modules. Store new sample data in `json/` and preserve the timestamp-based filename pattern for traceability.

## Build, Test, and Development Commands
No build step is required.
- `python -m http.server 8000`
Runs a local server to test file loading in a browser (`http://localhost:8000`).
- `python -m json.tool json\\kaiin_taikai_20260223_180140.JSON > $null`
Quickly validates JSON syntax.
- `rg --files`
Lists tracked files quickly when checking repository scope.

## Coding Style & Naming Conventions
- Use 2-space indentation in HTML/CSS/JS blocks to match current formatting.
- Prefer clear camelCase for JavaScript variables/functions (`renderCourse`, `expandAll`).
- Keep UI class names semantic and short (`.card`, `.tab`, `.badge-*`).
- Use UTF-8 encoding and maintain Japanese UI labels where already used.

If formatting is needed, keep changes minimal and consistent with existing style (no framework-specific rewrites).

## Testing Guidelines
There is no automated test suite yet.
- Perform manual verification in browser after each change:
1. Load a sample JSON from `json/`.
2. Switch tabs and confirm state persists.
3. Validate expand/collapse behavior for rule and child logic blocks.

When adding logic-heavy functions, include at least one reproducible sample JSON case in `json/`.

## Commit & Pull Request Guidelines
Follow the commit style used in history:
- `feat(scope): ...`
- `fix(scope): ...`
- `refactor(scope): ...`
- `docs(scope): ...`

Use concise, intent-first subjects. In PRs, include:
- Purpose and user-visible impact.
- Before/after screenshots for UI changes.
- Sample JSON used for validation and manual test notes.
