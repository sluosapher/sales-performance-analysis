"""Tests for timestamp parsing and normalization used in MCP output naming."""

from sales_mcp_server import extract_timestamp_from_stem, normalize_report_date


def test_extract_timestamp_accepts_yyyymmdd() -> None:
    assert extract_timestamp_from_stem("raw_data_20260131") == "20260131"


def test_extract_timestamp_converts_legacy_yymmdd() -> None:
    assert extract_timestamp_from_stem("raw_data_260131") == "20260131"


def test_normalize_report_date_keeps_yyyymmdd() -> None:
    assert normalize_report_date("20260131") == "20260131"
