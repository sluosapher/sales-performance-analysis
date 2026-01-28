# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sales Performance Analysis tool that reads raw sales data from Excel workbooks and generates geo-based "Top 10" summary reports. The tool processes data by geographic regions (AP, BRAZIL, EMEA, LAS, MX, NA) and creates multiple worksheets showing top performers across all offerings and ThinkShield Security specifically.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
uv sync
```

### Running the Tool
```bash
# Full command with explicit input file
uv run python main.py --input raw_data_1103.xlsx --output report.xlsx

# Auto-select latest raw_data_YYMMDD.xlsx from input/ folder
uv run python main.py --output report.xlsx

# With custom sheet names
uv run python main.py --input raw_data_1104.xlsx --output output\report.xlsx \
  --all-sheet-name "Custom Top 10" \
  --thinkshield-sheet-name "Custom ThinkShield"

# View all options
uv run python main.py --help
```

### When Tests Exist
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_aggregation.py

# Run with verbose output
uv run pytest -v
```

## Code Architecture

### File Structure
- **main.py** (641 lines): Single-file application containing all logic
- **input/**: Directory for raw Excel data files (auto-created)
- **output/**: Directory for generated reports (auto-created)
- **tests/**: Test files (planned, not yet created)

### High-Level Architecture (main.py)

The application follows a clear data flow from input to output:

1. **Argument Parsing** (main.py:87-133)
   - `parse_args()`: Handles CLI arguments with custom Windows popup error handling
   - Supports auto-discovery of latest input file when `--input` omitted

2. **Data Loading** (main.py:136-186)
   - `load_sales_data()`: Reads Excel workbook and extracts sales records
   - Automatically finds worksheet with required columns (Geo, FTF_Name, Quarter, Revenue ($M), oh_l3_sub_offering)
   - Filters to target geos and builds quarter ordering
   - Returns: (quarters list, SalesRow list)

3. **Data Transformation** (main.py:310-336)
   - `summarize_sales()`: Aggregates revenue by geo → salesperson → quarter
   - `sort_salespeople()`: Sorts and selects top 10 per geo
   - Uses nested dictionaries: `Dict[str, Dict[str, Dict[str, float]]]`

4. **Report Generation** (main.py:452-496)
   - `write_report()`: Creates top 10 tables per geo with quarterly breakdown
   - `write_top_percent_sheet()`: Creates percentage analysis (Top 10 vs Total)
   - `write_summary_sheet()`: Creates overview tab with metadata

5. **Excel Workbook Handling** (main.py:339-354)
   - `load_or_create_workbook()`: Loads existing or creates new workbook
   - `ensure_report_sheet()`: Creates/replaces worksheet for reports
   - Saves to both output path and history path with timestamp

### Key Data Structures

- **SalesRow** (main.py:38-44): NamedTuple with geo, salesperson, quarter, offering, revenue
- **TARGET_GEOS** (main.py:18): ["AP", "BRAZIL", "EMEA", "LAS", "MX", "NA"]
- **Quarter parsing** (main.py:220-227): Supports FY2024Q1 format with fallback sorting

### Output Worksheets

1. **Top 10 Sales by Geo**: Top 10 salespeople per geo across all offerings
2. **Top 10 ThinkShield by Geo**: Same structure, filtered to ThinkShield Security
3. **Top 10% All**: Percentage analysis for AP, EMEA, NA, and OTHERS groups
4. **Top 10% Security**: ThinkShield-specific percentage analysis
5. **Summary**: Overview with generation date, input file, and tab descriptions

### Error Handling

- **PopupArgumentParser** (main.py:50-53): Custom argument parser for Windows popup errors
- **show_error()** (main.py:55-68): Displays Windows MessageBox or falls back to stderr
- **show_info()** (main.py:71-84): Success notification with Windows popup or stdout
- Error scenarios: invalid file paths, missing columns, incompatible Excel format

## Input File Conventions

- **Naming pattern**: `raw_data_YYMMDD.xlsx` (e.g., `raw_data_251103.xlsx` for 2025-11-03)
- **Location**: Place in `input/` folder or repository root
- **Auto-selection**: When `--input` omitted, automatically selects latest file matching pattern
- **Flexible resolution**: Supports absolute paths, relative paths, or filename-only (searches input/ first)

## Dependencies

- **openpyxl** (≥3.1.2, <4.0.0): Excel file manipulation
- **Python 3.12+**: Type hints and modern Python features used throughout

## Important Implementation Details

- **Read-only Excel loading** (main.py:138): `load_workbook(..., read_only=True, data_only=True)`
- **Currency formatting** (main.py:31): `[$$-409]#,##0.00` number format for revenue cells
- **Case-insensitive filtering** (main.py:576): ThinkShield filter uses `.lower()` comparison
- **Quarter sorting** (main.py:220-227): Parses FY2024Q1 format; non-matching quarters get fallback ordering
- **History tracking** (main.py:612-615): Saves timestamped copy as `report_history_YYMMDD.xlsx`
- **Worksheet replacement** (main.py:352-354): Replaces existing sheets with same name instead of appending

## Existing Documentation

- **README.md**: Usage examples, input/output descriptions, error handling
- **AGENTS.md**: Development guidelines, coding style, testing approach, commit conventions
- **implementation_guide.md**: Original requirements and example output format

## Agent-Specific Notes

- Do not edit `.venv/` or Excel artifacts (`*.xlsx`) manually
- All changes should be minimal and focused
- Keep data loading/writing, transformation logic, and configuration clearly separated
- Follow existing function naming: snake_case for functions, CapWords for classes
- When adding tests, place under `tests/` directory as `test_*.py`