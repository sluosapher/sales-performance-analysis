# Sales Performance Analysis MCP Server

This MCP server processes Excel sales data files and generates formatted reports.

## Server Name
`sales-performance-analysis`

## Tools

### 1. upload-data
Open a native file selection dialog and upload the selected Excel sales data file to the server.

**Parameters:** None

**Example:**
```python
{}
```

**Response:**
```
File uploaded successfully!
Input: raw_data_20260131.xlsx
Timestamp: 20260131
View input: http://localhost:8004/view-input/raw_data_20260131.xlsx
```

### 2. analyze_input_data
Analyze an uploaded server-side input file and generate a report.

**Parameters:**
- `file_name` (string, required): Server-side input filename (must match `raw_data_YYYYMMDD.xlsx`)

**Example:**
```python
{
  "file_name": "raw_data_20260131.xlsx"
}
```

**Response:**
```
Input file analyzed successfully!
Input: raw_data_20260131.xlsx
Output: report_20260131.xlsx
Timestamp: 20260131
View report: http://localhost:8004/view-result/report_20260131.xlsx
```

### 3. list-results
List all available result files.

**Parameters:** None

**Example:**
```python
{}
```

**Response:**
```
Available Result Files:
============================================================
  report_20251103.xlsx
    Modified: 2026-01-27 15:30:00
    Size: 45.2 KB
```

### 4. get-result
Get formatted results from a specific result file.

**Parameters:**
- `file_name` (string, required): Name of result file

**Example:**
```python
{
  "file_name": "report_20251103.xlsx"
}
```

**Response:**
```
================================================================================
SALES PERFORMANCE ANALYSIS REPORT
File: report_20251103.xlsx
================================================================================

--------------------------------------------------------------------------------
SHEET: Top 10 Sales by Geo
--------------------------------------------------------------------------------
  Salesperson | FY2024Q1 | FY2024Q2 | FY2024Q3 | Total
  Alice Johnson | 100.00 | 150.00 | 200.00 | 450.00
  ...
```

### 5. get_top_sales
Get top-N salespeople for a region and report date, returned as a markdown table.

**Parameters:**
- `top_n` (integer, required): Number of top salespeople to return
- `region_name` (string, required): One of `AP`, `BRAZIL`, `EMEA`, `LAS`, `MX`, `NA`
- `report_date` (string, required): Date in `YYYYMMDD` format

**Example:**
```python
{
  "top_n": 5,
  "region_name": "NA",
  "report_date": "20260131"
}
```

**Response:**
```markdown
### Top Sales for NA (20260131)

| Rank | Salesperson | FY2025Q1 | FY2025Q2 | Total Revenue ($M) |
| --- | --- | --- | --- | --- |
| 1 | Alice Johnson | 120.50 | 145.00 | 265.50 |
| 2 | Bob Lee | 100.00 | 120.00 | 220.00 |
```

## File Upload via MCP Tool

Use `upload-data` and select a local file in the OS file picker dialog. Then call `analyze_input_data` with the uploaded filename.

## Future Compatibility

The `get-result` tool returns structured data for future UI rendering:

```python
{
  "text": "Human-readable formatted output",
  "structured": {
    "sheets": [...],
    "metadata": {...}
  },
  "ui_resources": [...]  # Future: charts, graphs, etc.
}
```

## Input Format

Files must match the pattern `raw_data_YYYYMMDD.xlsx` where:
- YYYY = Year (four digits)
- MM = Month
- DD = Day

Required columns in Excel:
- Geo
- FTF_Name
- Quarter
- Revenue ($M)
- oh_l3_sub_offering

## Output

Generated Excel files are saved in the `output/` directory with names like `report_YYYYMMDD.xlsx`.
