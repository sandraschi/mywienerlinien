"""MCP tool for journey planning."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

# Add frontend to path for backend imports
_project_root = Path(__file__).parent.parent.parent.parent
_frontend_path = _project_root / "frontend"
if str(_frontend_path) not in sys.path:
    sys.path.insert(0, str(_frontend_path))

from wienerlinien_mcp.models.journey import JourneyPlan, JourneySegment
from wienerlinien_mcp.utils import find_station_by_name

logger = logging.getLogger(__name__)


def register_journey_tool(mcp: FastMCP) -> None:
    """Register the journey_planner tool with the MCP server."""
    
    @mcp.tool()
    async def journey_planner(
        from_station: str,
        to_station: str,
        departure_time: Optional[str] = None
    ) -> JourneyPlan:
        """Plan optimal journey between Vienna stations.
        
        Args:
            from_station: Origin station name
            to_station: Destination station name
            departure_time: Optional departure time (ISO format, e.g., "2025-01-15T14:30:00Z")
                         If not provided, uses current time
        
        Returns:
            Journey plan with routes, transfers, duration, cost
        """
        try:
            # Parse departure time
            if departure_time:
                try:
                    dep_time = datetime.fromisoformat(departure_time.replace("Z", "+00:00"))
                except:
                    dep_time = datetime.utcnow()
            else:
                dep_time = datetime.utcnow()
            
            # Find stations
            from_info = find_station_by_name(from_station)
            if not from_info:
                raise ValueError(f"Origin station '{from_station}' not found")
            
            to_info = find_station_by_name(to_station)
            if not to_info:
                raise ValueError(f"Destination station '{to_station}' not found")
            
            # TODO: Implement actual journey planning algorithm
            # For now, return a placeholder response
            # This would integrate with GTFS routing or Wiener Linien journey planner API
            
            # Placeholder: Simple direct route estimate
            # In production, this would use GTFS routing or API
            segments = []
            total_duration = 15  # Placeholder
            
            journey = JourneyPlan(
                from_station=from_info["name"],
                to_station=to_info["name"],
                departure_time=dep_time,
                total_duration_minutes=total_duration,
                segments=segments,
                transfers=0,
                estimated_cost="€2.40",  # Standard Vienna fare
            )
            
            return journey
            
        except ValueError as e:
            logger.warning(f"Journey planning error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error planning journey: {e}", exc_info=True)
            raise RuntimeError(f"Failed to plan journey: {str(e)}") from e

