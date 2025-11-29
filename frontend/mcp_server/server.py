"""
Vienna Transit MCP Server - FastMCP 2.13 Compliant

This server provides MCP tools for Vienna public transport information.
It runs with stdio transport for Claude Desktop integration.

Usage:
    python -m mcp_server.server
    # Or with FastMCP CLI:
    fastmcp dev mcp_server.server:mcp
"""

import logging
import os
import sys
from pathlib import Path

from fastmcp import FastMCP

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize database BEFORE importing tools (they depend on db)
try:
    from database import db
    
    class _MCPApp:
        """Minimal app stub for db.init_app()."""
        pass
    
    # Only init if DATABASE_URL is set and db not already initialized
    if os.getenv('DATABASE_URL') and db.engine is None:
        db.init_app(_MCPApp())
except Exception as e:
    logging.getLogger("mcp_server").warning(f"Database init skipped: {e}")

# Import tools
from mcp_server.tools.departures import register_departures_tool
from mcp_server.tools.stations import register_station_search_tool
from mcp_server.tools.status import register_status_tool
from mcp_server.tools.journey import register_journey_tool

# Import prompts and resources
from mcp_server.prompts import register_prompts
from mcp_server.resources import register_resources

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_server")

# Create FastMCP server instance
mcp = FastMCP(
    name="vienna-transit",
    version="1.0.0",
)

# Note: Middleware support may vary by FastMCP version
# Middleware registration commented out until FastMCP 2.13 middleware API is confirmed
# from mcp_server.middleware.logging import register_logging_middleware
# from mcp_server.middleware.error_handler import register_error_handler_middleware
# register_error_handler_middleware(mcp)
# register_logging_middleware(mcp)

# Register prompts and resources (before tools for better discovery)
# Store references to prevent garbage collection (FastMCP 2.12+ standard)
_prompt_refs = register_prompts(mcp)
_resource_refs = register_resources(mcp)

# Register tools
register_departures_tool(mcp)
register_station_search_tool(mcp)
register_status_tool(mcp)
register_journey_tool(mcp)

logger.info("Vienna Transit MCP Server initialized with FastMCP 2.13")
logger.info("Registered prompts and resources for AI assistant guidance")

# Export for FastMCP CLI
if __name__ == "__main__":
    # Run with stdio transport (for Claude Desktop)
    mcp.run(transport="stdio")

