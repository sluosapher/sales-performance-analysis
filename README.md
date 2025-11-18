## Sales Performance Analysis

This tool reads raw sales data from an Excel workbook and generates geo-based “Top 10” summary reports into another workbook.

### Requirements
- Python 3.12 or later
- Dependencies from `pyproject.toml` installed (for example, with `uv sync` or `pip install -r <generated requirements>`)

### Usage
From the repository root, run:

```bash
python main.py <input.xlsx> <output.xlsx>
```

Examples:
- `python main.py raw_data_1103.xlsx report.xlsx`
- `python main.py raw_data_1104.xlsx report.xlsx`

If `<output.xlsx>` already exists, the report sheets will be replaced; otherwise a new workbook is created.

### Expected Output
The program writes several worksheets to the output workbook:
- `Top 10 Sales by Geo` (default): Top 10 salespeople per Geo (AP, BRAZIL, EMEA, LAS, MX, NA) with per-quarter revenue and totals.
- `Top 10 ThinkShield by Geo` (default): Same structure, filtered to the `ThinkShield Security` offering.
- `Top 10% All` (default): Per-geo tables showing total revenue, top 10 revenue, and the percentage represented by the top 10.
- `Top 10% Security` (default): The same percentage tables, restricted to ThinkShield revenue.

Sheet names can be customized with optional flags (see `python main.py --help`).

### Errors
If required arguments are missing or an unexpected error occurs (for example, invalid file path or incompatible Excel format), an error message is printed and, on Windows, also shown in a pop-up dialog.*** End Patchjuna ***!
