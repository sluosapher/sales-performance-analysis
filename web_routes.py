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
