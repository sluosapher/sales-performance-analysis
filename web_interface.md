# Web Interface for Sales Performance Analysis

The sales MCP server now includes a web-based interface for interactive file uploads and results viewing.

## Accessing the Web Interface

When the server starts, it runs on two ports:
- **MCP Server**: http://localhost:8003 (for programmatic access)
- **Web Interface**: http://localhost:8004 (for browser-based upload)

## Using the upload-input Tool

### Step 1: Call upload-input Tool
When you call the `upload-input` tool, it returns a URL:
```
File upload requested for: raw_data_1103.xlsx
Please visit: http://localhost:8004/upload
Use the web interface to upload your file and view results.
```

### Step 2: Upload File
- Click the URL or navigate to http://localhost:8004/upload
- Click "Choose File" and select an Excel file
- Ensure filename matches pattern: `raw_data_YYMMDD.xlsx`
- Click "Upload and Process"

### Step 3: View Results
- After successful processing, results display automatically
- View formatted report summary
- Download the Excel report file
- Upload another file if needed

### Step 4: Handle Errors
- If processing fails, an error page displays
- Error messages explain what went wrong
- Click "Try Again" to return to upload page

## Expected File Format

The uploaded Excel file must contain:
- **Columns**: Geo, FTF_Name, Quarter, Revenue ($M), oh_l3_sub_offering
- **Filename pattern**: raw_data_YYMMDD.xlsx (e.g., raw_data_251103.xlsx)
- **Format**: .xlsx (Excel workbook)

## Generated Output

The system generates an Excel workbook with multiple sheets:
1. **Summary**: Overview with metadata
2. **Top 10 Sales by Geo**: Top performers across all offerings
3. **Top 10 ThinkShield by Geo**: ThinkShield-specific top performers
4. **Top 10% All**: Revenue share analysis
5. **Top 10% Security**: ThinkShield revenue share analysis

## Technical Details

The web interface is built with:
- **Flask**: Web framework
- **Jinja2**: Template engine
- **Custom CSS**: Styling

The MCP server remains fully functional for programmatic access via tools like `upload-input`, `list-results`, and `get-result`.

## Starting the Server

```bash
# From the sales-performance-analysis directory
python sales_mcp_server.py
```

The server will:
1. Start the MCP server on port 8003
2. Start the web interface on port 8004
3. Display both URLs in the console
