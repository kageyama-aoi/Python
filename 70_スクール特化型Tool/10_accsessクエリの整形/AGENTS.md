# Repository Guidelines

## Project Structure & Module Organization
This repository is a small data-processing utility centered on `seikei.py`.
- `seikei.py`: main script that reads Access-style SQL text from a CSV and outputs a sanitized CSV.
- `kennsyuu.csv`: default input dataset (CP932/Shift-JIS expected).
- `kennsyuu_sanitized.csv`: generated output (UTF-8 with BOM).

Keep additional logic in functions inside `seikei.py` unless the codebase grows enough to justify a `src/` split.

## Build, Test, and Development Commands
Use Python 3.10+ in a virtual environment.
- `python -m venv .venv` then `.\.venv\Scripts\Activate.ps1`: create and activate local env.
- `pip install pandas`: install runtime dependency.
- `python seikei.py`: run the conversion using `INPUT_CSV` and `OUTPUT_CSV` constants.

If you change file names, update `INPUT_CSV` / `OUTPUT_CSV` in `seikei.py`.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation.
- Use `snake_case` for functions and variables (for example, `clean_access_sql`, `process_queries`).
- Keep transformation rules explicit and grouped by step, as in the existing numbered blocks.
- Prefer small, side-effect-light helper functions for new conversion rules.

## Testing Guidelines
No automated test suite exists yet.
- Validate changes by running `python seikei.py` and diffing output CSVs.
- Check edge cases: empty SQL, bracketed identifiers, date markers (`#...#`), and boolean replacements.
- When adding non-trivial logic, create `tests/` with `pytest` and name files `test_*.py`.

## Commit & Pull Request Guidelines
Git history is not available in this folder, so no local commit convention can be inferred.
Use this baseline:
- Commit format: `type(scope): short summary` (example: `fix(sql): protect digit-leading identifiers`).
- Keep commits focused and include input/output examples in PR descriptions.
- For behavior changes, include before/after snippets of transformed SQL and note any compatibility impact.

## Data & Encoding Notes
Input CSV is read as CP932; output is written as UTF-8 BOM. Preserve these defaults unless all downstream consumers are migrated together.
