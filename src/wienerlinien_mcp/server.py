"""
Vienna Transit MCP Server - FastMCP 2.13 Compliant

This server provides MCP tools for Vienna public transport information.
It runs with stdio transport for Claude Desktop integration.

Usage:
    python -m wienerlinien_mcp.server
    # Or with FastMCP CLI:
    fastmcp dev wienerlinien_mcp.server:mcp
"""

import logging
import os
import sys
from pathlib import Path

from fastmcp import FastMCP

# Add project roots to path for imports
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "frontend"))
sys.path.insert(0, str(_project_root / "src"))

# Initialize database BEFORE importing tools (they depend on db)
try:
    from database import db

    class _MCPApp:
        """Minimal app stub for db.init_app()."""

        pass

    # Only init if DATABASE_URL is set and db not already initialized
    if os.getenv("DATABASE_URL") and db.engine is None:
        db.init_app(_MCPApp())
except Exception as e:
    logging.getLogger("wienerlinien_mcp").warning(f"Database init skipped: {e}")

# Import tools
# Import prompts and resources
from wienerlinien_mcp.prompts import register_prompts
from wienerlinien_mcp.resources import register_resources
from wienerlinien_mcp.tools.alerts import register_traffic_alerts_tool
from wienerlinien_mcp.tools.cities import register_cities_tools
from wienerlinien_mcp.tools.departures import register_departures_tool
from wienerlinien_mcp.tools.help import register_help_tool
from wienerlinien_mcp.tools.journey import register_journey_tool
from wienerlinien_mcp.tools.nearby import register_nearby_stops_tool
from wienerlinien_mcp.tools.server_status import register_server_status_tool
from wienerlinien_mcp.tools.routes import register_routes_tool
from wienerlinien_mcp.tools.stations import register_station_search_tool
from wienerlinien_mcp.tools.status import register_status_tool
from wienerlinien_mcp.tools.timetable import register_stop_timetable_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("wienerlinien_mcp")

# Create FastMCP server instance
mcp = FastMCP(
    name="vienna-transit",
    version="1.0.0",
)

# Note: Middleware support may vary by FastMCP version
# Middleware registration commented out until FastMCP 2.13 middleware API is confirmed
# from wienerlinien_mcp.middleware.logging import register_logging_middleware
# from wienerlinien_mcp.middleware.error_handler import register_error_handler_middleware
# register_error_handler_middleware(mcp)
# register_logging_middleware(mcp)

# Register prompts and resources (before tools for better discovery)
# Store references to prevent garbage collection (FastMCP 2.12+ standard)
_prompt_refs = register_prompts(mcp)
_resource_refs = register_resources(mcp)

# Register tools - Essential
register_help_tool(mcp)
register_server_status_tool(mcp)

# Register tools - Multi-City Management (Phase 6)
register_cities_tools(mcp)

# Register tools - Search & Discovery
register_station_search_tool(mcp)
register_nearby_stops_tool(mcp)

# Register tools - Real-time
register_departures_tool(mcp)
register_traffic_alerts_tool(mcp)
register_status_tool(mcp)  # line_status

# Register tools - Schedule
register_stop_timetable_tool(mcp)

# Register tools - Trip Planning
register_journey_tool(mcp)

# Register tools - Route Info
register_routes_tool(mcp)

logger.info("Vienna Transit MCP Server initialized with FastMCP 2.13")
logger.info(
    f"Registered {len(mcp._tool_manager._tools)} tools, {len(mcp._resource_manager._resources)} resources, {len(mcp._prompt_manager._prompts)} prompts"
)

# Export for FastMCP CLI
if __name__ == "__main__":
    # Run with stdio transport (for Claude Desktop)
    mcp.run(transport="stdio")
