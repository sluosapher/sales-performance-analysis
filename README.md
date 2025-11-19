## Sales Performance Analysis

This tool reads raw sales data from an Excel workbook and generates geo-based “Top 10” summary reports into another workbook.

### Requirements
- Python 3.12 or later
- Dependencies from `pyproject.toml` installed (for example, with `uv sync` or `pip install -r <generated requirements>`)

### Usage
From the repository root, run:

```bash
python main.py --output <output.xlsx> [--input <input.xlsx>]
```

Examples:
- `python main.py --input raw_data_1103.xlsx --output report.xlsx`
- `python main.py --input raw_data_1104.xlsx --output report.xlsx`
- `python main.py --output output\report.xlsx`  (auto-selects latest `raw_data_YYMMDD.xlsx` from the `input` folder)

If `<output.xlsx>` already exists, the report sheets will be replaced; otherwise a new workbook is created.

### Prepare input data
- Place your raw Excel workbooks in the `input` folder at the project root (created automatically by `install.ps1`, or you can create it yourself).
- Name input files using the pattern `raw_data_YYMMDD.xlsx` (for example, `raw_data_251103.xlsx` for 2025‑11‑03); this timestamp is used to pick the latest file and to name history reports.
- When you omit `--input`, the tool automatically selects the latest `raw_data_YYMMDD.xlsx` from the `input` folder.
- When you provide `--input` with just a filename (for example, `--input raw_data_251103.xlsx`), the program first looks in `input\` and then in the current directory; you can also pass an absolute or relative path if you store the file elsewhere.

### Expected Output
The program writes several worksheets to the output workbook:
- `Top 10 Sales by Geo` (default): Top 10 salespeople per Geo (AP, BRAZIL, EMEA, LAS, MX, NA) with per-quarter revenue and totals.
- `Top 10 ThinkShield by Geo` (default): Same structure, filtered to the `ThinkShield Security` offering.
- `Top 10% All` (default): Per-geo tables showing total revenue, top 10 revenue, and the percentage represented by the top 10.
- `Top 10% Security` (default): The same percentage tables, restricted to ThinkShield revenue.

Sheet names can be customized with optional flags (see `python main.py --help`).

### Errors
If required arguments are missing or an unexpected error occurs (for example, invalid file path or incompatible Excel format), an error message is printed and, on Windows, also shown in a pop-up dialog.*** End Patchjuna ***!
