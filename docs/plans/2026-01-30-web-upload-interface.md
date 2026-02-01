# Web-Based File Upload Interface Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a web-based file upload interface to sales_mcp_server.py where the `upload-input` tool returns a URL for browser-based file upload, displays results in the browser, and handles errors with retry functionality.

**Architecture:** Modify the existing FastMCP server to integrate a Flask web application. When `upload-input` is called, it returns a URL instead of accepting base64 content. The web interface provides:
- Upload page with file validation
- Processing with results display
- Error handling with retry functionality
- Integration with existing `process_input_file` and `format_result_file` functions

**Tech Stack:**
- Flask for web framework
- Jinja2 for HTML templating
- Existing FastMCP for MCP protocol
- Existing openpyxl-based processing logic

---

## Task 1: Create HTML Templates

**Files:**
- Create: `templates/upload.html`
- Create: `templates/results.html`
- Create: `templates/error.html`
- Create: `static/style.css`

**Step 1: Create upload.html template**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sales Data Upload</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <h1>Sales Performance Analysis</h1>
        <div class="upload-section">
            <h2>Upload Sales Data</h2>
            <p>Upload an Excel file with sales data (format: raw_data_YYMMDD.xlsx)</p>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <input type="file" name="file" id="file" accept=".xlsx" required>
                </div>
                <button type="submit" class="btn-primary">Upload and Process</button>
            </form>
        </div>
        <div class="info-section">
            <h3>Requirements:</h3>
            <ul>
                <li>File must be in .xlsx format</li>
                <li>Filename must match pattern: raw_data_YYMMDD.xlsx</li>
                <li>Expected columns: Geo, FTF_Name, Quarter, Revenue ($M), oh_l3_sub_offering</li>
            </ul>
        </div>
    </div>
</body>
</html>
```

**Step 2: Create results.html template**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sales Analysis Results</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <h1>Sales Performance Analysis Results</h1>
        <div class="result-info">
            <p><strong>Input File:</strong> {{ filename }}</p>
            <p><strong>Timestamp:</strong> {{ timestamp }}</p>
            <p><strong>Generated:</strong> {{ generated_date }}</p>
        </div>
        <div class="download-section">
            <a href="/download/{{ filename }}" class="btn-primary">Download Excel Report</a>
            <a href="/" class="btn-secondary">Upload Another File</a>
        </div>
        <div class="results-section">
            <h2>Report Summary</h2>
            <div class="text-results">
                <pre>{{ results_text }}</pre>
            </div>
        </div>
    </div>
</body>
</html>
```

**Step 3: Create error.html template**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - Sales Analysis</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <h1>Error Occurred</h1>
        <div class="error-message">
            <h2>{{ error_title }}</h2>
            <p>{{ error_message }}</p>
        </div>
        <div class="actions">
            <a href="/" class="btn-primary">Try Again</a>
        </div>
    </div>
</body>
</html>
```

**Step 4: Create style.css**

```css
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    background-color: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

h1 {
    color: #333;
    border-bottom: 3px solid #007bff;
    padding-bottom: 10px;
}

h2 {
    color: #555;
    margin-top: 20px;
}

.upload-section, .results-section {
    margin: 20px 0;
}

.form-group {
    margin: 20px 0;
}

input[type="file"] {
    display: block;
    margin: 10px 0;
    padding: 10px;
    border: 2px solid #ddd;
    border-radius: 4px;
    width: 100%;
    max-width: 400px;
}

.btn-primary, .btn-secondary {
    display: inline-block;
    padding: 12px 24px;
    margin: 10px 5px;
    text-decoration: none;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    border: none;
    transition: background-color 0.3s;
}

.btn-primary {
    background-color: #007bff;
    color: white;
}

.btn-primary:hover {
    background-color: #0056b3;
}

.btn-secondary {
    background-color: #6c757d;
    color: white;
}

.btn-secondary:hover {
    background-color: #545b62;
}

.error-message {
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
    padding: 20px;
    border-radius: 4px;
    margin: 20px 0;
}

.info-section {
    background-color: #e7f3ff;
    border-left: 4px solid #007bff;
    padding: 15px;
    margin: 20px 0;
}

.result-info {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 4px;
    margin: 20px 0;
}

.text-results {
    background-color: #f8f9fa;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 20px;
    overflow-x: auto;
    margin: 20px 0;
}

pre {
    font-family: 'Courier New', monospace;
    white-space: pre-wrap;
    word-wrap: break-word;
    margin: 0;
}
```

**Step 5: Commit**

```bash
git add templates/upload.html templates/results.html templates/error.html static/style.css
git commit -m "feat: add HTML templates for web interface"
```

---

## Task 2: Create Flask Web Routes Module

**Files:**
- Create: `web_routes.py`

**Step 1: Create web_routes.py with Flask application**

```python
"""Flask web routes for sales analysis upload interface."""

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_file,
    flash,
)
from pathlib import Path
import tempfile
import os
import base64
from werkzeug.utils import secure_filename
import traceback

# Import from sales_mcp_server
from sales_mcp_server import (
    process_input_file,
    format_result_file,
    extract_timestamp_from_stem,
)

ALLOWED_EXTENSIONS = {"xlsx"}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

# Create Flask app instance
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    """Check if file has allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    """Render the upload page."""
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload and processing."""
    if "file" not in request.files:
        return render_template(
            "error.html",
            error_title="No File Selected",
            error_message="Please select a file to upload.",
        )

    file = request.files["file"]
    if file.filename == "":
        return render_template(
            "error.html",
            error_title="No File Selected",
            error_message="Please select a file to upload.",
        )

    if file and allowed_file(file.filename):
        # Validate filename pattern
        if not extract_timestamp_from_stem(file.filename.replace(".xlsx", "")):
            return render_template(
                "error.html",
                error_title="Invalid Filename",
                error_message=f"Filename must match pattern: raw_data_YYMMDD.xlsx. Got: {file.filename}",
            )

        try:
            # Save uploaded file to temporary location
            temp_dir = Path(tempfile.mkdtemp())
            input_path = temp_dir / secure_filename(file.filename)
            file.save(str(input_path))

            # Process the file
            output_dir = Path("output")
            output_dir.mkdir(parents=True, exist_ok=True)

            output_path, timestamp = process_input_file(input_path, output_dir)

            # Format results
            results_text = format_result_file(output_path)

            # Get metadata for display
            from datetime import datetime
            generation_date = datetime.now().strftime("%Y-%m-%d")

            return render_template(
                "results.html",
                filename=file.filename,
                timestamp=timestamp,
                generated_date=generation_date,
                results_text=results_text,
                result_filename=output_path.name,
            )

        except ValueError as e:
            error_msg = str(e)
            return render_template(
                "error.html",
                error_title="Processing Error",
                error_message=f"Failed to process file: {error_msg}",
            )

        except Exception as e:
            print(f"Unexpected error: {traceback.format_exc()}")
            return render_template(
                "error.html",
                error_title="Unexpected Error",
                error_message=f"An unexpected error occurred: {str(e)}",
            )

        finally:
            # Cleanup temp directory
            if "temp_dir" in locals():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)

    else:
        return render_template(
            "error.html",
            error_title="Invalid File Type",
            error_message="Please upload an Excel file (.xlsx).",
        )

@app.route("/download/<path:filename>")
def download_file(filename):
    """Download the generated Excel report."""
    output_path = Path("output") / filename
    if output_path.exists():
        return send_file(str(output_path), as_attachment=True)
    else:
        return render_template(
            "error.html",
            error_title="File Not Found",
            error_message="The requested file could not be found.",
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8004, debug=True)
```

**Step 2: Commit**

```bash
git add web_routes.py
git commit -m "feat: add Flask web routes module"
```

---

## Task 3: Update upload-input Tool to Return URL

**Files:**
- Modify: `sales_mcp_server.py:497-531`

**Step 1: Replace upload-input tool implementation**

Replace the existing `upload-input` tool function:

```python
@app.tool(name="upload-input")
async def upload_input(file_name: str, content: str) -> str:
    """Upload an Excel sales data file for processing."""
    # Return URL instead of processing base64 content
    return (
        f"File upload requested for: {file_name}\n"
        f"Please visit: http://localhost:8004/upload\n"
        f"Use the web interface to upload your file and view results."
    )
```

**Step 2: Remove base64 processing code**

The tool no longer needs to process base64 content, so remove lines 500-531.

**Step 3: Commit**

```bash
git add sales_mcp_server.py
git commit -m "feat: update upload-input tool to return URL instead of processing content"
```

---

## Task 4: Integrate Flask with FastMCP Server

**Files:**
- Modify: `sales_mcp_server.py:580-582`

**Step 1: Update sales_mcp_server.py to integrate Flask routes**

Replace the existing main block at the end of sales_mcp_server.py:

```python
if __name__ == "__main__":
    # Start both MCP server and web interface
    import threading

    # Start Flask web server in a separate thread
    def run_web_server():
        import web_routes
        web_routes.app.run(host="0.0.0.0", port=8004, debug=False, use_reloader=False)

    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # Start MCP server
    print("Starting MCP server on port 8003...")
    print("Starting web interface on port 8004...")
    app.run(transport="http", host="0.0.0.0", port=8003)
```

**Step 2: Commit**

```bash
git add sales_mcp_server.py
git commit -m "feat: integrate Flask web interface with FastMCP server"
```

---

## Task 5: Create Configuration and Documentation

**Files:**
- Create: `web_interface.md`
- Modify: `requirements.txt`

**Step 1: Update requirements.txt to include Flask**

```txt
fastmcp>=0.1.0
openpyxl>=3.1.2,<4.0.0
flask>=3.0.0
```

**Step 2: Create web_interface.md documentation**

```markdown
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
```

**Step 3: Commit**

```bash
git add requirements.txt web_interface.md
git commit -m "docs: add web interface documentation and Flask dependency"
```

---

## Task 6: Create Test for Web Interface

**Files:**
- Create: `tests/test_web_interface.py`

**Step 1: Create test file with basic functionality tests**

```python
"""Tests for web interface functionality."""

import pytest
import tempfile
from pathlib import Path
from werkzeug.test import Client
from werkzeug.wrappers import Response
from web_routes import app

@pytest.fixture
def client():
    """Create test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_upload_page_loads(client):
    """Test that upload page loads successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Sales Performance Analysis" in response.data

def test_upload_page_has_file_input(client):
    """Test that upload page has file input field."""
    response = client.get("/")
    assert b'type="file"' in response.data
    assert b'name="file"' in response.data

def test_upload_no_file(client):
    """Test upload without selecting a file."""
    response = client.post("/upload", data={})
    assert response.status_code == 200
    assert b"No File Selected" in response.data

def test_upload_invalid_filename(client):
    """Test upload with invalid filename pattern."""
    # Create a temporary file with invalid name
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        temp_path = Path(f.name)
        # Don't actually write Excel content, just test validation

    try:
        with open(temp_path, "wb") as f:
            f.write(b"fake")

        with open(temp_path, "rb") as f:
            response = client.post(
                "/upload",
                data={"file": (f, "invalid_name.xlsx")},
                content_type="multipart/form-data",
            )

        assert response.status_code == 200
        assert b"Invalid Filename" in response.data
        assert b"raw_data_YYMMDD.xlsx" in response.data
    finally:
        temp_path.unlink()

def test_download_nonexistent_file(client):
    """Test downloading a file that doesn't exist."""
    response = client.get("/download/nonexistent.xlsx")
    assert response.status_code == 200
    assert b"File Not Found" in response.data
```

**Step 2: Run tests to verify they work**

```bash
cd /workspace/sales-performance-analysis
uv run pytest tests/test_web_interface.py -v
```

Expected: Tests should run (some may fail due to missing implementation, but structure should be correct)

**Step 3: Commit**

```bash
git add tests/test_web_interface.py
git commit -m "test: add web interface tests"
```

---

## Task 7: Test Integration

**Files:**
- Test: `sales_mcp_server.py`

**Step 1: Install Flask dependency**

```bash
cd /workspace/sales-performance-analysis
uv add flask
```

**Step 2: Start the server**

```bash
cd /workspace/sales-performance-analysis
python sales_mcp_server.py
```

Expected output:
```
Starting MCP server on port 8003...
Starting web interface on port 8004...
```

**Step 3: Test web interface access**

In a separate terminal:
```bash
curl http://localhost:8004/
```

Expected: HTML page with upload form

**Step 4: Test MCP server still works**

```bash
curl http://localhost:8003/
```

Expected: MCP server response

**Step 5: Commit**

```bash
git add requirements.txt
git commit -m "feat: add Flask dependency to project"
```

---

## Summary

**Files Modified:**
- `sales_mcp_server.py` - Updated upload-input tool to return URL instead of processing content; Integrated Flask routes with FastMCP server
- `requirements.txt` - Added Flask dependency

**Files Created:**
- `web_routes.py` - Flask application with upload, processing, and download routes
- `templates/upload.html` - File upload page
- `templates/results.html` - Results display page
- `templates/error.html` - Error handling page
- `static/style.css` - Styling for web interface
- `web_interface.md` - Documentation
- `tests/test_web_interface.py` - Tests for web interface

**Key Features Implemented:**
1. ✅ `upload-input` tool returns URL for browser-based upload
2. ✅ Web-based file upload interface on port 8004
3. ✅ File validation (extension and filename pattern)
4. ✅ Integration with existing `process_input_file` function
5. ✅ Results display with formatted text and download link
6. ✅ Error handling with user-friendly messages and retry option
7. ✅ Automatic cleanup of temporary files
8. ✅ Seamless flow from MCP tool to web interface

**Architecture:**
- `upload-input` tool returns URL instead of processing base64 content
- Flask runs in a daemon thread alongside FastMCP on port 8004
- Uses Jinja2 templates for HTML rendering
- Maintains existing processing logic in sales_mcp_server
- Both servers start automatically when script runs

---

## Plan Complete

The plan has been saved to `docs/plans/2026-01-30-web-upload-interface.md`.

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach would you prefer?
