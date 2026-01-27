"""MCP Server for Sales Performance Analysis."""

import asyncio
from mcp.server.fastmcp.server import FastMCP as Server
from mcp.server.stdio import stdio_server
import anyio
from mcp.server.models import InitializationOptions
from mcp.types import Tool
from collections import defaultdict
from typing import Callable, Dict, Iterable, List, NamedTuple, Optional, Tuple
from datetime import date # for quarter_sort_key
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet
import re # for QUARTER_PATTERN
from pathlib import Path # Added missing import

TARGET_GEOS = ["AP", "BRAZIL", "EMEA", "LAS", "MX", "NA"]
REQUIRED_COLUMNS = {
    "Geo", "FTF_Name", "Quarter", "Revenue ($M)", "oh_l3_sub_offering"
}
DEFAULT_ALL_SHEET_NAME = "Top 10 Sales by Geo"
DEFAULT_THINKSHIELD_SHEET_NAME = "Top 10 ThinkShield by Geo"
DEFAULT_TOP_PERCENT_SHEET_NAME = "Top 10% All"
DEFAULT_TOP_PERCENT_SECURITY_SHEET_NAME = "Top 10% Security"
SUMMARY_SHEET_NAME = "Summary"
NUMBER_FORMAT = '[$$-409]#,##0.00'
THINKSHIELD_VALUE = "ThinkShield Security"
THINKSHIELD_VALUE_LOWER = THINKSHIELD_VALUE.lower()
QUARTER_PATTERN = re.compile(r"^FY(?P<year>\d{4})Q(?P<quarter>\d)$")
RAW_DATA_STEM_PATTERN = re.compile(r"^raw_data_(\d{6})$", re.IGNORECASE)

class SalesRow(NamedTuple):
    geo: str
    salesperson: str
    quarter: str
    offering: str
    revenue: float

def to_str(value: object) -> str:
    return str(value).strip() if value is not None else ""

def to_float(value: object) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Unable to convert {value!r} to float.") from exc

def iter_rows_values(ws: Worksheet, min_row: int = 1, max_rows: int | None = None) -> Iterable[List[object]]:
    """Yield worksheet rows as plain value lists."""
    count = 0
    for row in ws.iter_rows(min_row=min_row, values_only=True):
        yield list(row)
        count += 1
        if max_rows is not None and count >= max_rows:
            break

def build_header_index(header_row: Iterable[object]) -> Dict[str, int]:
    index: Dict[str, int] = {}
    for col_idx, raw_value in enumerate(header_row):
        header = to_str(raw_value)
        if header:
            index[header.strip()] = col_idx
    return index

def quarter_sort_key(value: str, fallback_index: int) -> Tuple[int, int, int]:
    """Return a sort key that orders fiscal quarters chronologically."""
    match = QUARTER_PATTERN.match(value)
    if match:
        year = int(match.group("year"))
        quarter = int(match.group("quarter"))
        return (0, year, quarter)
    return (1, fallback_index, 0)

def load_sales_data(path: Path) -> Tuple[List[str], List[SalesRow]]:
    """Load sales rows from the worksheet that contains the required columns."""
    workbook = load_workbook(filename=path, data_only=True, read_only=True)
    try:
        worksheet: Worksheet | None = None
        header_index: Dict[str, int] | None = None

        for candidate in workbook.worksheets:
            header_row = next(iter_rows_values(candidate, max_rows=1), None)
            if not header_row:
                continue
            candidate_index = build_header_index(header_row)
            if REQUIRED_COLUMNS.issubset(candidate_index):
                worksheet = candidate
                header_index = candidate_index
                break

        if worksheet is None or header_index is None:
            raise ValueError(
                f"No worksheet in {path} contains columns: {', '.join(sorted(REQUIRED_COLUMNS))}"
            )

        quarter_order: Dict[str, int] = {}
        next_order = 0

        rows: List[SalesRow] = []
        for row in iter_rows_values(worksheet, min_row=2):
            geo = to_str(row[header_index["Geo"]])
            if geo not in TARGET_GEOS:
                continue

            sales_person = to_str(row[header_index["FTF_Name"]]) or "blank"
            quarter = to_str(row[header_index["Quarter"]]) or "Unknown"
            revenue = to_float(row[header_index["Revenue ($M)"]])
            offering = to_str(row[header_index["oh_l3_sub_offering"]])

            if quarter not in quarter_order:
                quarter_order[quarter] = next_order
                next_order += 1

            rows.append(SalesRow(geo, sales_person, quarter, offering, revenue))

        quarters = sorted(
            quarter_order.keys(),
            key=lambda value: quarter_sort_key(value, quarter_order[value]),
        )

        return quarters, rows
    finally:
        workbook.close()

def summarize_sales(
    rows: Iterable[SalesRow],
    offering_filter: Callable[[SalesRow], bool] | None = None,
) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Return nested geo -> salesperson -> quarter -> revenue mapping."""
    summary: Dict[str, Dict[str, Dict[str, float]]] = {
        geo: defaultdict(lambda: defaultdict(float)) for geo in TARGET_GEOS
    }
    for entry in rows:
        if offering_filter and not offering_filter(entry):
            continue
        summary[entry.geo][entry.salesperson][entry.quarter] += entry.revenue
    return summary

def sort_salespeople(data: Dict[str, Dict[str, Dict[str, float]]], quarters: List[str]) -> Dict[str, List[Tuple[str, List[float], float]]]:
    """Prepare the top 10 rows per geo with per-quarter totals."""
    result: Dict[str, List[Tuple[str, List[float], float]]] = {}
    for geo in TARGET_GEOS:
        geo_entries = []
        for salesperson, quarter_map in data.get(geo, {}).items():
            quarter_values = [quarter_map.get(q, 0.0) for q in quarters]
            total = sum(quarter_values)
            geo_entries.append((salesperson, quarter_values, total))
        geo_entries.sort(key=lambda item: item[2], reverse=True)
        result[geo] = geo_entries[:10]
    return result

app = Server("sales-performance-analysis")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, InitializationOptions())

if __name__ == "__main__":
    anyio.run(main)
