# Sales Performance Analysis MCP Server

This MCP server processes Excel sales data files and generates formatted reports.

## Server Name
`sales-performance-analysis`

## Tools

### 1. upload-input
Upload an Excel sales data file for processing.

**Parameters:**
- `file_name` (string, required): Name of file (must match `raw_data_YYMMDD.xlsx`)
- `content` (string, required): Base64-encoded Excel file content

**Example:**
```python
{
  "file_name": "raw_data_251103.xlsx",
  "content": "UEsDBBQABgAIAAAAIQCL1rvzRwEAABAE..."
}
```

**Response:**
```
File processed successfully!
Input: raw_data_251103.xlsx
Output: result_251103.xlsx
Timestamp: 251103
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
  result_251103.xlsx
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
  "file_name": "result_251103.xlsx"
}
```

**Response:**
```
================================================================================
SALES PERFORMANCE ANALYSIS REPORT
File: result_251103.xlsx
================================================================================

--------------------------------------------------------------------------------
SHEET: Top 10 Sales by Geo
--------------------------------------------------------------------------------
  Salesperson | FY2024Q1 | FY2024Q2 | FY2024Q3 | Total
  Alice Johnson | 100.00 | 150.00 | 200.00 | 450.00
  ...
```

## File Upload via MCP Resources

Upload files using the MCP resources feature:

```python
resource = {
  "uri": "sales://input/raw_data_251103.xlsx",
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

Files must match the pattern `raw_data_YYMMDD.xlsx` where:
- YY = Year (last two digits)
- MM = Month
- DD = Day

Required columns in Excel:
- Geo
- FTF_Name
- Quarter
- Revenue ($M)
- oh_l3_sub_offering

## Output

Generated Excel files are saved in the `output/` directory with names like `result_YYMMDD.xlsx`.
