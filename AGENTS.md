# Repository Guidelines

## Project Structure & Module Organization
- `main.py`: Entry point for the sales performance analysis; reads an input Excel file and writes results to a new worksheet in the output file.
- Data files (e.g., `raw_data_1103.xlsx`, `raw_data_1104.xlsx`, `report.xlsx`) live in the repository root for easy local runs.
- `.venv/` contains the local virtual environment and must not be committed or modified manually.
- Future test modules should live under `tests/` (for example, `tests/test_aggregation.py`).

## Build, Test, and Development Commands
- Create environment (PowerShell): `python -m venv .venv; .\.venv\Scripts\Activate.ps1`.
- Install dependencies using `uv`: `uv sync`.
- Run the analysis: `uv run python main.py raw_data_1103.xlsx report.xlsx`.
- When tests are added: `uv run pytest` from the repository root.

## Coding Style & Naming Conventions
- Python 3.12+, PEP 8–style, 4-space indentation, and UTF-8 encoding.
- Use `snake_case` for variables and functions, `CapWords` for classes, and descriptive names (e.g., `compute_geo_top10`).
- Keep data loading/writing, transformation logic, and configuration clearly separated into small, testable functions.

## Testing Guidelines
- Use `pytest` for unit and integration tests; place them under `tests/` and name files `test_*.py`.
- Focus on verifying aggregation by Geo group and correctness of the top-10 rankings per region.
- Include at least one test that exercises reading from a small sample Excel file and writing to an output workbook.

## Commit & Pull Request Guidelines
- Write concise, imperative commit messages (e.g., `Add geo aggregation helper`).
- For pull requests, include: goal, approach, notes on edge cases (e.g., missing Geo), and how you tested (`uv run pytest`, sample Excel used).
- Attach example input/output file names or screenshots of key Excel output where helpful.

## Agent-Specific Instructions
- Do not edit `.venv/` or Excel artifacts (`*.xlsx`) by hand; prefer regenerating them via `main.py`.
- Keep changes minimal, focused, and consistent with these guidelines; update this document when workflows or tools change.

