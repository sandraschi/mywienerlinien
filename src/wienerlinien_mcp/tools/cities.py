"""
Multi-city management tools for Vienna Transit MCP Server.
Phase 6 Extension: Support for multiple Austrian and international cities.

Provides tools for managing city configurations, switching between cities,
and accessing city-specific transit information.
"""

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

try:
    from ..city_manager import get_city_manager
    from ..database import db
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from database import db
    from wienerlinien_mcp.city_manager import get_city_manager

logger = logging.getLogger(__name__)


class CityInfo(BaseModel):
    """Information about a transit city."""

    city_code: str = Field(..., description="Unique city identifier (lowercase)")
    city_name: str = Field(..., description="Display name of the city")
    country: str = Field(..., description="Country where the city is located")
    timezone: str = Field(..., description="Timezone for the city")
    language: str = Field(..., description="Primary language code")
    enabled: bool = Field(..., description="Whether the city is active")
    data_loaded: bool = Field(..., description="Whether GTFS data is loaded")
    map_center_lat: Optional[float] = Field(None, description="Map center latitude")
    map_center_lng: Optional[float] = Field(None, description="Map center longitude")
    map_zoom: Optional[int] = Field(None, description="Default map zoom level")


class CityStatistics(BaseModel):
    """Statistics for a city's transit system."""

    city_code: str = Field(..., description="City identifier")
    city_name: str = Field(..., description="City display name")
    total_stops: int = Field(..., description="Total number of transit stops")
    total_routes: int = Field(..., description="Total number of transit routes")
    total_trips: int = Field(..., description="Total number of scheduled trips")
    active_vehicles: int = Field(..., description="Currently active vehicles")
    last_updated: Optional[str] = Field(None, description="Last data update timestamp")


async def list_available_cities() -> list[CityInfo]:
    """
    List all available transit cities and their current status.

    Returns information about all configured cities, including their
    operational status and data loading state.

    Returns:
        List of CityInfo objects for all available cities

    Raises:
        Exception: If database query fails
    """
    try:
        city_manager = get_city_manager(db)
        cities_data = city_manager.list_cities()

        cities = []
        for city_code, config in cities_data.items():
            # Get additional info from database
            city_info = city_manager.get_city_info(city_code)
            if city_info:
                cities.append(
                    CityInfo(
                        city_code=city_code,
                        city_name=city_info.get("name", config.get("name", city_code.title())),
                        country=city_info.get("country", config.get("country", "Unknown")),
                        timezone=city_info.get("timezone", config.get("timezone", "Europe/Vienna")),
                        language=city_info.get("language", config.get("language", "de")),
                        enabled=city_info.get("enabled", True),
                        data_loaded=city_info.get("data_loaded", False),
                        map_center_lat=city_info.get("map_center_lat"),
                        map_center_lng=city_info.get("map_center_lng"),
                        map_zoom=city_info.get("map_zoom", 12),
                    )
                )

        logger.info(f"Retrieved information for {len(cities)} cities")
        return cities

    except Exception as e:
        logger.error(f"Failed to list cities: {e}", exc_info=True)
        raise Exception(f"Unable to retrieve city list: {str(e)}")


async def switch_city(city_code: str) -> dict[str, Any]:
    """
    Switch the active city for transit queries.

    Changes the current city context for all transit operations.
    This affects which city's data is used for searches, departures, and routing.

    Args:
        city_code: The city code to switch to (e.g., 'vienna', 'graz', 'linz')

    Returns:
        Dictionary with switch result and city information

    Raises:
        ValueError: If city code is invalid or city is not available
        Exception: If database operation fails
    """
    try:
        city_manager = get_city_manager(db)

        # Validate city exists and is available
        available_cities = await list_available_cities()
        city_codes = [city.city_code for city in available_cities]

        if city_code not in city_codes:
            raise ValueError(
                f"City '{city_code}' not found. Available cities: {', '.join(city_codes)}"
            )

        # Check if city data is loaded
        city_info = next((c for c in available_cities if c.city_code == city_code), None)
        if not city_info.data_loaded:
            logger.warning(
                f"City '{city_code}' data not loaded yet - limited functionality available"
            )

        # Perform the switch
        success = city_manager.switch_city(city_code)

        if not success:
            raise ValueError(f"Failed to switch to city '{city_code}'")

        # Get updated city info
        new_city_info = city_manager.get_city_info(city_code)

        result = {
            "success": True,
            "current_city": city_code,
            "city_info": new_city_info,
            "data_loaded": city_info.data_loaded if city_info else False,
            "message": f"Successfully switched to {city_code.title()}",
        }

        if not city_info.data_loaded:
            result["warning"] = (
                f"City '{city_code}' data not fully loaded. Some features may be limited."
            )

        logger.info(f"Switched to city: {city_code}")
        return result

    except ValueError as e:
        logger.warning(f"City switch validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to switch city: {e}", exc_info=True)
        raise Exception(f"Unable to switch city: {str(e)}")


async def get_city_statistics(city_code: Optional[str] = None) -> CityStatistics:
    """
    Get comprehensive statistics for a city's transit system.

    Provides detailed metrics about stops, routes, trips, and real-time data
    for the specified city (or current city if none specified).

    Args:
        city_code: City code to get statistics for (defaults to current city)

    Returns:
        CityStatistics object with detailed transit system metrics

    Raises:
        ValueError: If city is not found or invalid
        Exception: If database queries fail
    """
    try:
        city_manager = get_city_manager(db)

        if city_code is None:
            city_code = city_manager.current_city

        # Validate city exists
        available_cities = await list_available_cities()
        city_info = next((c for c in available_cities if c.city_code == city_code), None)

        if not city_info:
            city_codes = [c.city_code for c in available_cities]
            raise ValueError(f"City '{city_code}' not found. Available: {', '.join(city_codes)}")

        # Query database for statistics
        # Note: In Phase 6, these will be filtered by city_code
        # For now, returns Vienna statistics since that's the only loaded city

        try:
            stops_count = db.execute_query("SELECT COUNT(*) as count FROM stops", fetch_one=True)
            routes_count = db.execute_query("SELECT COUNT(*) as count FROM routes", fetch_one=True)
            trips_count = db.execute_query("SELECT COUNT(*) as count FROM trips", fetch_one=True)

            # Get active vehicles count (rough estimate from recent snapshots)
            vehicles_query = """
            SELECT COUNT(DISTINCT vehicle_id) as count
            FROM vehicle_snapshots
            WHERE timestamp > NOW() - INTERVAL '1 hour'
            """
            vehicles_count = db.execute_query(vehicles_query, fetch_one=True)

            # Get last update timestamp
            last_update = db.execute_query(
                "SELECT MAX(timestamp) as last_update FROM vehicle_snapshots", fetch_one=True
            )

        except Exception as db_error:
            logger.warning(f"Database query failed, using fallback values: {db_error}")
            # Fallback values if database issues
            stops_count = {"count": 0}
            routes_count = {"count": 0}
            trips_count = {"count": 0}
            vehicles_count = {"count": 0}
            last_update = {"last_update": None}

        stats = CityStatistics(
            city_code=city_code,
            city_name=city_info.city_name,
            total_stops=stops_count.get("count", 0),
            total_routes=routes_count.get("count", 0),
            total_trips=trips_count.get("count", 0),
            active_vehicles=vehicles_count.get("count", 0),
            last_updated=last_update.get("last_update").isoformat()
            if last_update.get("last_update")
            else None,
        )

        logger.info(f"Retrieved statistics for city: {city_code}")
        return stats

    except ValueError as e:
        logger.warning(f"City statistics validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to get city statistics: {e}", exc_info=True)
        raise Exception(f"Unable to retrieve city statistics: {str(e)}")


async def get_city_info(city_code: str) -> CityInfo:
    """
    Get detailed information about a specific city.

    Returns comprehensive information about a city's configuration,
    capabilities, and current operational status.

    Args:
        city_code: The city code to get information for

    Returns:
        CityInfo object with detailed city configuration

    Raises:
        ValueError: If city is not found
        Exception: If data retrieval fails
    """
    try:
        available_cities = await list_available_cities()
        city_info = next((c for c in available_cities if c.city_code == city_code), None)

        if not city_info:
            city_codes = [c.city_code for c in available_cities]
            raise ValueError(f"City '{city_code}' not found. Available: {', '.join(city_codes)}")

        logger.info(f"Retrieved info for city: {city_code}")
        return city_info

    except ValueError as e:
        logger.warning(f"City info request failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to get city info: {e}", exc_info=True)
        raise Exception(f"Unable to retrieve city information: {str(e)}")


# Tool registration function
def register_cities_tools(wienerlinien_mcp):
    """Register multi-city management tools with the MCP server."""

    @wienerlinien_mcp.tool()
    async def list_cities() -> str:
        """
        List all available transit cities and their status.

        Shows all configured cities with their operational status,
        data loading state, and basic configuration information.

        Returns:
            Formatted string listing all available cities with details
        """
        try:
            cities = await list_available_cities()

            if not cities:
                return "No cities configured yet. Vienna should be available by default."

            result = "Available Transit Cities:\n\n"
            for city in cities:
                status_icon = "✅" if city.data_loaded else "⏳"
                enabled_icon = "🟢" if city.enabled else "🔴"

                result += f"{status_icon} **{city.city_name}** ({city.city_code})\n"
                result += f"   {enabled_icon} Status: {'Enabled' if city.enabled else 'Disabled'}\n"
                result += f"   📍 Location: {city.country}\n"
                result += f"   🕐 Timezone: {city.timezone}\n"
                result += f"   📊 Data: {'Loaded' if city.data_loaded else 'Not loaded'}\n"

                if city.map_center_lat and city.map_center_lng:
                    result += f"   🗺️  Map: {city.map_center_lat:.4f}, {city.map_center_lng:.4f} (zoom: {city.map_zoom})\n"

                result += "\n"

            result += "💡 Use 'switch_city' to change active city for transit queries."
            return result

        except Exception as e:
            logger.error(f"List cities tool failed: {e}")
            return f"Error retrieving city list: {str(e)}"

    @wienerlinien_mcp.tool()
    async def switch_to_city(city_code: str) -> str:
        """
        Switch the active city for all transit operations.

        Changes which city's transit system is used for departures, routing,
        and other transit queries. The city must be available and preferably
        have its data loaded.

        Args:
            city_code: City code to switch to (e.g., 'vienna', 'graz')

        Returns:
            Confirmation message with city switch details
        """
        try:
            result = await switch_city(city_code)

            response = f"✅ **Switched to {result['city_info']['name']}**\n\n"
            response += f"🏙️  City: {result['current_city']}\n"
            response += f"📊 Data Status: {'Loaded' if result['data_loaded'] else 'Not loaded'}\n"
            response += f"🌍 Country: {result['city_info'].get('country', 'Unknown')}\n"
            response += f"🕐 Timezone: {result['city_info'].get('timezone', 'Europe/Vienna')}\n"

            if result.get("warning"):
                response += f"\n⚠️  **Warning:** {result['warning']}\n"

            response += "\nAll transit queries now use this city's data."
            return response

        except ValueError as e:
            return f"❌ **Invalid City**: {str(e)}\n\nUse 'list_cities' to see available options."
        except Exception as e:
            logger.error(f"Switch city tool failed: {e}")
            return f"❌ **Error**: Failed to switch city: {str(e)}"

    @wienerlinien_mcp.tool()
    async def city_transit_stats(city_code: Optional[str] = None) -> str:
        """
        Get comprehensive statistics for a city's transit system.

        Shows detailed metrics including number of stops, routes, trips,
        and currently active vehicles.

        Args:
            city_code: City to get statistics for (defaults to current city)

        Returns:
            Formatted statistics report for the city
        """
        try:
            stats = await get_city_statistics(city_code)

            result = f"📊 **{stats.city_name} Transit Statistics**\n\n"
            result += f"🏙️  City Code: {stats.city_code}\n"
            result += f"🚏 Total Stops: {stats.total_stops:,}\n"
            result += f"🚌 Routes: {stats.total_routes:,}\n"
            result += f"📅 Scheduled Trips: {stats.total_trips:,}\n"
            result += f"🚊 Active Vehicles: {stats.active_vehicles:,}\n"

            if stats.last_updated:
                result += f"🕐 Last Updated: {stats.last_updated}\n"
            else:
                result += "🕐 Last Updated: Unknown\n"

            # Add some insights
            if stats.total_stops > 0:
                avg_trips_per_stop = stats.total_trips / stats.total_stops
                result += "\n💡 **Insights:**\n"
                result += f"   • Average {avg_trips_per_stop:.1f} trips per stop\n"

                if stats.active_vehicles > 0:
                    coverage_ratio = (stats.active_vehicles / stats.total_stops) * 100
                    result += f"   • {coverage_ratio:.1f}% of stops have active vehicles\n"

            return result

        except ValueError as e:
            return f"❌ **Invalid City**: {str(e)}\n\nUse 'list_cities' to see available options."
        except Exception as e:
            logger.error(f"City stats tool failed: {e}")
            return f"❌ **Error**: Failed to retrieve statistics: {str(e)}"

    logger.info("Multi-city management tools registered")
    return [list_cities, switch_to_city, city_transit_stats]
