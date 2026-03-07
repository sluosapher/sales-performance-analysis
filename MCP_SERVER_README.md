# Sales Performance Analysis MCP Server

This MCP server processes Excel sales data files and generates formatted reports.

## Server Name
`sales-performance-analysis`

## Tools

### 1. upload-input
Upload an Excel sales data file for processing.

**Parameters:**
- `file_name` (string, required): Name of file (must match `raw_data_YYYYMMDD.xlsx`)
- `content` (string, required): Base64-encoded Excel file content

**Example:**
```python
{
  "file_name": "raw_data_20251103.xlsx",
  "content": "UEsDBBQABgAIAAAAIQCL1rvzRwEAABAE..."
}
```

**Response:**
```
File processed successfully!
Input: raw_data_20251103.xlsx
Output: result_20251103.xlsx
Timestamp: 20251103
```

### 2. list-results
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
  result_20251103.xlsx
    Modified: 2026-01-27 15:30:00
    Size: 45.2 KB
```

### 3. get-result
Get formatted results from a specific result file.

**Parameters:**
- `file_name` (string, required): Name of result file

**Example:**
```python
{
  "file_name": "result_20251103.xlsx"
}
```

**Response:**
```
================================================================================
SALES PERFORMANCE ANALYSIS REPORT
File: result_20251103.xlsx
================================================================================

--------------------------------------------------------------------------------
SHEET: Top 10 Sales by Geo
--------------------------------------------------------------------------------
  Salesperson | FY2024Q1 | FY2024Q2 | FY2024Q3 | Total
  Alice Johnson | 100.00 | 150.00 | 200.00 | 450.00
  ...
```

### 4. get_top_sales
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

## File Upload via MCP Resources

Upload files using the MCP resources feature:

```python
resource = {
  "uri": "sales://input/raw_data_20251103.xlsx",
  "name": "Raw Sales Data",
  "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}
```

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

Generated Excel files are saved in the `output/` directory with names like `result_YYYYMMDD.xlsx`.
