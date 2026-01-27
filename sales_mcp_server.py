"""MCP Server for Sales Performance Analysis."""

import asyncio
from mcp.server.fastmcp.server import FastMCP as Server
from mcp.server.stdio import stdio_server
import anyio
from mcp.server.models import InitializationOptions
from mcp.types import Tool
from collections import defaultdict
from typing import Callable, Dict, Iterable, List, NamedTuple, Optional, Tuple

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

app = Server("sales-performance-analysis")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, InitializationOptions())

if __name__ == "__main__":
    anyio.run(main)
