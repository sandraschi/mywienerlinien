"""MCP tool implementations.

Tools are registered via decorators in their respective modules.
Import the registration functions to register tools with the MCP server.
"""

from .cities import register_cities_tools
from .departures import register_departures_tool
from .journey import register_journey_tool
from .stations import register_station_search_tool
from .status import register_status_tool

__all__ = [
    "register_cities_tools",
    "register_departures_tool",
    "register_station_search_tool",
    "register_status_tool",
    "register_journey_tool",
]
