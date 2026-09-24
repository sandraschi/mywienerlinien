"""MCP tool for checking service status and disruptions."""

import logging
from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

try:
    from disruption_alerts import disruption_monitor

    from ..models.status import LineStatusResponse, ServiceStatus
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from disruption_alerts import disruption_monitor

    from wienerlinien_mcp.models.status import LineStatusResponse, ServiceStatus

logger = logging.getLogger(__name__)


def register_status_tool(mcp: FastMCP) -> None:
    """Register the line_status tool with the MCP server.

    This tool provides real-time service status and disruption information
    for Vienna's public transport network. It monitors active disruptions,
    delays, and service changes across all lines or for a specific line.

    Args:
        mcp: FastMCP server instance to register the tool with
    """

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True))
    async def line_status(
        line_name: Annotated[
            str | None, Field(description="Line filter (e.g. U1, D, 13A, N25). Omit for system-wide status.")
        ] = None,
    ) -> LineStatusResponse:
        """Check Vienna transit service status and disruptions.

        Retrieves current service status for Vienna's public transport network.
        Can check system-wide status or filter by a specific line. Returns
        information about disruptions, delays, service changes, and affected
        stations. With no active disruptions, returns an operational status.

        ## Return Format
        {"line_filter": str | None, "statuses": [{"line": str | None, "status": "operational|disrupted|delayed", "severity": "low|medium|high", "title": str, "description": str, "affected_stations": list[str], "start_time": datetime | None, "end_time": datetime | None}], "timestamp": datetime}

        ## Examples
        line_status()
        line_status(line_name="U1")
        line_status(line_name="D")
        """
        try:
            # Get disruptions from monitor
            if line_name:
                disruptions = disruption_monitor.get_disruptions_by_line(line_name.strip())
            else:
                disruptions = disruption_monitor.get_active_disruptions()

            # Convert to ServiceStatus models
            statuses = []
            for disruption in disruptions:
                status = ServiceStatus(
                    line=disruption.line,
                    status=disruption.status.value,
                    severity=disruption.severity.value,
                    title=disruption.title,
                    description=disruption.description,
                    affected_stations=disruption.affected_stations or [],
                    start_time=disruption.start_time,
                    end_time=disruption.end_time,
                )
                statuses.append(status)

            # If no disruptions, return operational status
            if not statuses:
                statuses.append(
                    ServiceStatus(
                        line=line_name,
                        status="operational",
                        severity="low",
                        title="Service Operating Normally",
                        description="No disruptions reported",
                        affected_stations=[],
                        start_time=None,
                        end_time=None,
                    )
                )

            return LineStatusResponse(
                line_filter=line_name,
                statuses=statuses,
            )

        except Exception as e:
            logger.error(f"Error fetching line status: {e}", exc_info=True)
            raise RuntimeError(f"Failed to fetch line status: {e!s}") from e

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True))
    async def get_disruptions(
        line: Annotated[str | None, Field(description="Line filter (e.g. U4). Omit for all lines.")] = None,
        station: Annotated[
            str | None, Field(description="Station filter (e.g. Karlsplatz). Omit for all stations.")
        ] = None,
        severity: Annotated[
            str | None, Field(description="Severity filter: low, medium, high, critical. Omit for all severities.")
        ] = None,
        max_results: Annotated[int, Field(description="Maximum disruptions to return.", ge=1, le=50)] = 10,
    ) -> LineStatusResponse:
        """Get current service disruptions with advanced filtering.

        Filters active disruptions by line, station, and severity, capped
        at max_results. Line filter takes precedence over station filter;
        with neither, returns system-wide disruptions.

        ## Return Format
        {"line_filter": str, "statuses": [{"line": str | None, "status": str, "severity": "low|medium|high|critical", "title": str, "description": str, "affected_stations": list[str], "start_time": datetime | None, "end_time": datetime | None}], "timestamp": datetime}

        ## Examples
        get_disruptions()
        get_disruptions(line="U4")
        get_disruptions(severity="high", max_results=5)
        """
        try:
            # Get disruptions from monitor
            if line:
                disruptions = disruption_monitor.get_disruptions_by_line(line.strip())
            elif station:
                disruptions = disruption_monitor.get_disruptions_by_station(station.strip())
            else:
                disruptions = disruption_monitor.get_active_disruptions()

            # Filter by severity if requested
            if severity:
                disruptions = [d for d in disruptions if d.severity.value == severity.lower()]

            # Convert to ServiceStatus models
            statuses = []
            for disruption in disruptions[:max_results]:
                status = ServiceStatus(
                    line=disruption.line,
                    status=disruption.status.value,
                    severity=disruption.severity.value,
                    title=disruption.title,
                    description=disruption.description,
                    affected_stations=disruption.affected_stations or [],
                    start_time=disruption.start_time,
                    end_time=disruption.end_time,
                )
                statuses.append(status)

            return LineStatusResponse(
                line_filter=line or station or "system",
                statuses=statuses,
            )
        except Exception as e:
            logger.error(f"Error in get_disruptions: {e}", exc_info=True)
            raise RuntimeError(f"Failed to fetch disruptions: {e!s}") from e

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True))
    async def get_service_status() -> LineStatusResponse:
        """Get system-wide service status summary.

        Returns an overview of current service status across the entire
        network by delegating to line_status with no filter.

        ## Return Format
        {"line_filter": str | None, "statuses": [{"line": str | None, "status": "operational|disrupted|delayed", "severity": "low|medium|high", "title": str, "description": str, "affected_stations": list[str], "start_time": datetime | None, "end_time": datetime | None}], "timestamp": datetime}

        ## Examples
        get_service_status()
        """
        return await line_status()
