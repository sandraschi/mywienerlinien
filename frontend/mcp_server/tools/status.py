"""MCP tool for checking service status and disruptions."""

import logging
from typing import Optional

from fastmcp import FastMCP

try:
    from ...disruption_alerts import disruption_monitor
    from ..models.status import LineStatusResponse, ServiceStatus
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from disruption_alerts import disruption_monitor
    from mcp_server.models.status import LineStatusResponse, ServiceStatus

logger = logging.getLogger(__name__)


def register_status_tool(mcp: FastMCP) -> None:
    """Register the line_status tool with the MCP server.

    This tool provides real-time service status and disruption information
    for Vienna's public transport network. It monitors active disruptions,
    delays, and service changes across all lines or for a specific line.

    Args:
        mcp: FastMCP server instance to register the tool with
    """

    @mcp.tool()
    async def line_status(line_name: Optional[str] = None) -> LineStatusResponse:
        """Check Vienna transit service status and disruptions.

        Retrieves current service status for Vienna's public transport network.
        Can check system-wide status or filter by a specific line. Returns
        information about disruptions, delays, service changes, and affected
        stations.

        If no disruptions are active, returns an "operational" status indicating
        normal service. When disruptions exist, provides detailed information
        including severity, affected stations, and expected duration.

        Args:
            line_name (str, optional): Line name filter. If provided, returns status
                only for that line. Examples: "U1" (metro), "D" (tram), "13A" (bus),
                "N25" (night bus). If None or not provided, returns system-wide
                status for all lines.

        Returns:
            LineStatusResponse: Response containing:
                - line_filter (str, optional): The line name filter used (None if
                    system-wide)
                - statuses (List[ServiceStatus]): List of ServiceStatus objects with:
                    * line (str, optional): Line name (None for system-wide status)
                    * status (str): Current status (operational, disrupted, delayed)
                    * severity (str): Severity level (low, medium, high)
                    * title (str): Brief status title
                    * description (str): Detailed description of the status
                    * affected_stations (List[str]): List of affected station names
                    * start_time (datetime, optional): When the disruption started
                    * end_time (datetime, optional): Expected resolution time
                - timestamp (datetime): Response generation timestamp

        Raises:
            RuntimeError: If status cannot be retrieved or processed.

        Example:
            >>> # Check system-wide status
            >>> status = await line_status()
            >>> print(f"System status: {status.statuses[0].status}")

            >>> # Check specific line
            >>> u1_status = await line_status("U1")
            >>> print(f"U1 status: {u1_status.statuses[0].title}")
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
            raise RuntimeError(f"Failed to fetch line status: {str(e)}") from e
