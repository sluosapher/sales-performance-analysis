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
