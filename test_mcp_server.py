"""Basic tests for MCP server functions."""

from sales_mcp_server import (
    SalesRow, TARGET_GEOS, REQUIRED_COLUMNS,
    to_str,
    to_float,
    summarize_sales,
    extract_timestamp_from_stem,
    load_sales_data,
    iter_rows_values, build_header_index, quarter_sort_key
)

from pathlib import Path
from openpyxl import Workbook

def test_sales_row():
    row = SalesRow("NA", "Alice", "FY2024Q1", "Product A", 100.0)
    assert row.geo == "NA"
    assert row.salesperson == "Alice"

def test_to_str():
    assert to_str("  hello  ") == "hello"
    assert to_str(None) == ""

def test_to_float():
    assert to_float("100.5") == 100.5
    assert to_float(None) == 0.0

def test_extract_timestamp():
    assert extract_timestamp_from_stem("raw_data_251103") == "251103"
    assert extract_timestamp_from_stem("invalid") is None

def test_summarize_sales():
    rows = [
        SalesRow("NA", "Alice", "FY2024Q1", "Product A", 100.0),
        SalesRow("NA", "Bob", "FY2024Q1", "Product A", 50.0),
    ]
    summary = summarize_sales(rows)
    assert summary["NA"]["Alice"]["FY2024Q1"] == 100.0
    assert summary["NA"]["Bob"]["FY2024Q1"] == 50.0

def test_load_sales_data_creates_structure():
    # This test currently requires a real Excel file, so it's a placeholder.
    # We'll create a mock Excel file for proper testing later if needed.
    pass

if __name__ == "__main__":
    test_sales_row()
    test_to_str()
    test_to_float()
    test_extract_timestamp()
    test_summarize_sales()
    test_load_sales_data_creates_structure()
    test_upload_input_tool_exists()
    test_format_result_file_structure()
    print("All tests passed!")

def test_format_result_file_structure():
    # Test will be written when we have an actual result file
    pass


def test_upload_input_tool_exists():
    # This test will require MCP server to be running and callable
    # For now, it's a placeholder to indicate the tool's presence.
    pass
