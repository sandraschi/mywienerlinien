"""Server status tool for Vienna Transit MCP."""

import os
import time
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from fastmcp import FastMCP

# Track server start time
_server_start_time = time.time()


class CacheStats(BaseModel):
    """Cache performance statistics."""

    stations_cached: bool = Field(..., description="Stations data cached")
    lines_cached: bool = Field(..., description="Lines data cached")
    routes_cached: bool = Field(..., description="Routes data cached")


class ServerStatus(BaseModel):
    """Server health and status information."""

    status: str = Field(..., description="Overall status: healthy, degraded, unhealthy")
    api_status: str = Field(..., description="Wiener Linien API: connected, timeout, unavailable")
    database_status: str = Field(..., description="PostgreSQL: connected, disconnected")
    gtfs_data_age: Optional[str] = Field(None, description="Age of GTFS data")
    cache_stats: CacheStats = Field(..., description="Cache performance")
    version: str = Field(..., description="MCP server version")
    uptime_seconds: int = Field(..., description="Seconds since server start")
    uptime_human: str = Field(..., description="Human-readable uptime")
    timestamp: datetime = Field(..., description="Status check timestamp")
    tools_available: int = Field(..., description="Number of registered tools")
    resources_available: int = Field(..., description="Number of registered resources")


def register_server_status_tool(mcp: FastMCP) -> None:
    """Register the server_status tool with the MCP server."""

    @mcp.tool()
    async def server_status() -> ServerStatus:
        """Check Vienna Transit MCP server health and status.

        Returns comprehensive information about server health, API connectivity,
        database status, data freshness, and performance metrics. Use this to
        diagnose issues or verify the server is working correctly.

        Returns:
            ServerStatus: Detailed health information including:
                - status: Overall health (healthy, degraded, unhealthy)
                - api_status: Wiener Linien API connectivity
                - database_status: PostgreSQL connection status
                - gtfs_data_age: When GTFS data was last updated
                - cache_stats: What data is currently cached
                - version: Server version number
                - uptime_seconds: Time since server started
                - uptime_human: Human-readable uptime
                - tools_available: Number of registered tools
                - resources_available: Number of registered resources

        Example:
            >>> status = await server_status()
            >>> print(f"Server is {status.status}")
            Server is healthy
        """
        issues = []

        # Check database status
        db_status = "disconnected"
        try:
            from database import db

            if db.engine is not None:
                # Try a simple query
                with db.get_session() as session:
                    session.execute("SELECT 1")
                db_status = "connected"
        except Exception as e:
            issues.append(f"Database: {e}")

        # Check API status
        api_status = "unavailable"
        try:
            import requests

            resp = requests.get(
                "https://www.wienerlinien.at/ogd_realtime/monitor?rbl=252",
                timeout=5,
            )
            if resp.status_code == 200:
                api_status = "connected"
            else:
                api_status = "error"
                issues.append(f"API returned {resp.status_code}")
        except requests.Timeout:
            api_status = "timeout"
            issues.append("API timeout")
        except Exception as e:
            issues.append(f"API: {e}")

        # Check data freshness
        gtfs_age = None
        try:
            from data_loader import data_loader

            cache_status = data_loader.get_cache_status()
            if cache_status.get("stations_loaded"):
                last_loaded = cache_status.get("last_loaded", {}).get("stations")
                if last_loaded:
                    if isinstance(last_loaded, str):
                        last_loaded = datetime.fromisoformat(last_loaded)
                    age = datetime.now() - last_loaded
                    gtfs_age = f"{age.seconds // 3600}h {(age.seconds % 3600) // 60}m ago"
        except Exception:
            pass

        # Check cache status
        cache_stats = CacheStats(
            stations_cached=False,
            lines_cached=False,
            routes_cached=False,
        )
        try:
            from data_loader import data_loader

            status = data_loader.get_cache_status()
            cache_stats = CacheStats(
                stations_cached=status.get("stations_loaded", False),
                lines_cached=status.get("lines_loaded", False),
                routes_cached=status.get("routes_loaded", False),
            )
        except Exception:
            pass

        # Calculate uptime
        uptime_secs = int(time.time() - _server_start_time)
        hours, remainder = divmod(uptime_secs, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_human = f"{hours}h {minutes}m {seconds}s"

        # Count tools and resources
        tools_count = len(mcp._tool_manager._tools) if hasattr(mcp, "_tool_manager") else 0
        resources_count = (
            len(mcp._resource_manager._resources) if hasattr(mcp, "_resource_manager") else 0
        )

        # Determine overall status
        if db_status == "connected" and api_status == "connected":
            overall_status = "healthy"
        elif api_status == "connected":
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        return ServerStatus(
            status=overall_status,
            api_status=api_status,
            database_status=db_status,
            gtfs_data_age=gtfs_age,
            cache_stats=cache_stats,
            version="1.0.0",
            uptime_seconds=uptime_secs,
            uptime_human=uptime_human,
            timestamp=datetime.now(timezone.utc),
            tools_available=tools_count,
            resources_available=resources_count,
        )

