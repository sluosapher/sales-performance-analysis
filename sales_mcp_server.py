"""MCP Server for Sales Performance Analysis."""

import asyncio
from mcp.server.fastmcp.server import FastMCP as Server
from mcp.server.stdio import stdio_server
import anyio
from mcp.server.models import InitializationOptions
from mcp.types import Tool

app = Server("sales-performance-analysis")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, InitializationOptions())

if __name__ == "__main__":
    anyio.run(main)
