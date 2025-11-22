"""
Wiener Linien MCP Server - FastMCP 2.13 Compliant

This server provides MCP tools for Vienna public transport information.
It runs with stdio transport for Claude Desktop integration.

Usage:
    python -m wienerlinien_mcp.server
    # Or with FastMCP CLI:
    fastmcp dev wienerlinien_mcp.server:mcp
"""

import logging
import sys
from pathlib import Path

from fastmcp import FastMCP

# Add frontend directory to path for backend imports
_project_root = Path(__file__).parent.parent.parent
_frontend_path = _project_root / "frontend"
if str(_frontend_path) not in sys.path:
    sys.path.insert(0, str(_frontend_path))

# Import tools
from wienerlinien_mcp.tools.departures import register_departures_tool
from wienerlinien_mcp.tools.stations import register_station_search_tool
from wienerlinien_mcp.tools.status import register_status_tool
from wienerlinien_mcp.tools.journey import register_journey_tool

# Import middleware
from wienerlinien_mcp.middleware.logging import register_logging_middleware
from wienerlinien_mcp.middleware.error_handler import register_error_handler_middleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("wienerlinien_mcp")

# Create FastMCP server instance
mcp = FastMCP(
    name="wienerlinien-transit",
    version="1.0.0",
)

# Register middleware (order matters - first registered runs first)
register_error_handler_middleware(mcp)
register_logging_middleware(mcp)

# Register tools
register_departures_tool(mcp)
register_station_search_tool(mcp)
register_status_tool(mcp)
register_journey_tool(mcp)

logger.info("Wiener Linien MCP Server initialized with FastMCP 2.13")

# Export for FastMCP CLI
if __name__ == "__main__":
    # Run with stdio transport (for Claude Desktop)
    mcp.run(transport="stdio")

