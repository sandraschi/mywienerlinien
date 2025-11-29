"""MCP tool for checking service status and disruptions."""

import logging
import sys
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

# Add frontend to path for backend imports
_project_root = Path(__file__).parent.parent.parent.parent
_frontend_path = _project_root / "frontend"
if str(_frontend_path) not in sys.path:
    sys.path.insert(0, str(_frontend_path))

from wienerlinien_mcp.models.status import ServiceStatus, LineStatusResponse
from disruption_alerts import disruption_monitor

logger = logging.getLogger(__name__)


def register_status_tool(mcp: FastMCP) -> None:
    """Register the line_status tool with the MCP server."""
    
    @mcp.tool()
    async def line_status(
        line_name: Optional[str] = None
    ) -> LineStatusResponse:
        """Check Vienna transit service status and disruptions.
        
        Args:
            line_name: Optional line name filter (e.g., "U1", "D", "13A")
                     If not provided, returns system-wide status
        
        Returns:
            List of service status entries with line, status, disruptions
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
                statuses.append(ServiceStatus(
                    line=line_name,
                    status="operational",
                    severity="low",
                    title="Service Operating Normally",
                    description="No disruptions reported",
                    affected_stations=[],
                    start_time=None,
                    end_time=None,
                ))
            
            return LineStatusResponse(
                line_filter=line_name,
                statuses=statuses,
            )
            
        except Exception as e:
            logger.error(f"Error fetching line status: {e}", exc_info=True)
            raise RuntimeError(f"Failed to fetch line status: {str(e)}") from e



