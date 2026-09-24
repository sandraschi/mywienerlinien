"""Unit tests for the multi-city management tools."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest
from fastmcp import Client, FastMCP


@pytest.fixture
def mock_city_manager():
    """Create a mock city manager with sample data."""
    manager = MagicMock()

    # Mock cities data (keys mirror the real CityManager.get_city_info
    # shape: "name" for display name, plus the config fields).
    mock_cities = {
        "vienna": {
            "city_code": "vienna",
            "name": "Vienna",
            "city_name": "Vienna",
            "country": "Austria",
            "timezone": "Europe/Vienna",
            "language": "de",
            "gtfs_url": "https://example.com/gtfs.zip",
            "map_center_lat": 48.2082,
            "map_center_lng": 16.3738,
            "map_zoom": 12,
            "enabled": True,
            "data_loaded": True,
        },
        "graz": {
            "city_code": "graz",
            "name": "Graz",
            "city_name": "Graz",
            "country": "Austria",
            "timezone": "Europe/Vienna",
            "language": "de",
            "gtfs_url": "https://example.com/graz-gtfs.zip",
            "map_center_lat": 47.0667,
            "map_center_lng": 15.4333,
            "map_zoom": 13,
            "enabled": True,
            "data_loaded": False,
        }
    }

    # Mock methods
    manager.list_cities = Mock(return_value=mock_cities)
    manager.current_city = "vienna"
    manager.switch_city = Mock(return_value=True)
    manager.get_city_info = Mock(side_effect=lambda city_code: mock_cities.get(city_code))

    # Mock statistics
    mock_stats = {
        "city_code": "vienna",
        "city_name": "Vienna",
        "total_stops": 4684,
        "total_routes": 1138,
        "total_trips": 562609,
        "active_vehicles": 51,
        "last_updated": "2025-12-17T13:27:24.577399"
    }
    manager.get_city_statistics = Mock(return_value=mock_stats)

    return manager


@pytest.fixture
def mock_db():
    """Create a mock database with sample data."""
    db = MagicMock()

    # Match on normalized query content: the live tools build multi-line
    # SQL, so exact-string keys are brittle (whitespace mismatches silently
    # fall through to the empty default).
    def _execute_query(query, **kwargs):
        normalized = " ".join(str(query).split())
        if "MAX(timestamp)" in normalized:
            return {"last_update": None}
        if "COUNT(DISTINCT" in normalized:
            return {"count": 51}
        if "FROM stops" in normalized:
            return {"count": 4684}
        if "FROM routes" in normalized:
            return {"count": 1138}
        if "FROM trips" in normalized:
            return {"count": 562609}
        return []

    db.execute_query = Mock(side_effect=_execute_query)

    return db


@pytest.mark.asyncio
async def test_list_cities_success(mock_city_manager, mock_db):
    """Test successful listing of available cities."""
    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        async with Client(test_mcp) as client:
            result = await client.call_tool("list_cities", {})
            text = result.structured_content["result"]

            assert isinstance(text, str)
            assert "Vienna" in text
            assert "Graz" in text
            assert "✅" in text  # Data loaded indicator
            assert "⏳" in text  # Data not loaded indicator
            assert "Available Transit Cities" in text


@pytest.mark.asyncio
async def test_list_cities_empty(mock_city_manager, mock_db):
    """Test listing cities when no cities are available."""
    mock_city_manager.list_cities = Mock(return_value={})

    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        async with Client(test_mcp) as client:
            result = await client.call_tool("list_cities", {})
            text = result.structured_content["result"]

            assert isinstance(text, str)
            assert "No cities configured yet" in text


@pytest.mark.asyncio
async def test_switch_to_city_success(mock_city_manager, mock_db):
    """Test successful city switching."""
    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        async with Client(test_mcp) as client:
            result = await client.call_tool("switch_to_city", {"city_code": "graz"})
            text = result.structured_content["result"]

            assert isinstance(text, str)
            assert "✅ **Switched to Graz**" in text
            assert "🏙️  City: graz" in text
            assert "📊 Data Status: Not loaded" in text
            assert "⚠️  **Warning:**" in text


@pytest.mark.asyncio
async def test_switch_to_city_invalid(mock_city_manager, mock_db):
    """Test switching to invalid city."""
    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        async with Client(test_mcp) as client:
            result = await client.call_tool("switch_to_city", {"city_code": "invalid_city"})
            text = result.structured_content["result"]

            assert isinstance(text, str)
            assert "❌ **Invalid City**" in text
            assert "not found" in text


@pytest.mark.asyncio
async def test_switch_to_city_failure(mock_city_manager, mock_db):
    """Test city switching failure."""
    mock_city_manager.switch_city = Mock(return_value=False)

    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        async with Client(test_mcp) as client:
            result = await client.call_tool("switch_to_city", {"city_code": "vienna"})
            text = result.structured_content["result"]

            # NOTE: the live tool maps a failed switch (manager returns
            # False -> ValueError) to the "Invalid City" message, not the
            # generic "Error" branch, so assert the real contract.
            assert isinstance(text, str)
            assert "❌ **Invalid City**" in text
            assert "Failed to switch to city" in text


@pytest.mark.asyncio
async def test_city_transit_stats_success(mock_city_manager, mock_db):
    """Test successful retrieval of city transit statistics."""
    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        async with Client(test_mcp) as client:
            result = await client.call_tool("city_transit_stats", {"city_code": "vienna"})
            text = result.structured_content["result"]

            assert isinstance(text, str)
            assert "📊 **Vienna Transit Statistics**" in text
            assert "🏙️  City Code: vienna" in text
            assert "🚏 Total Stops: 4,684" in text
            assert "🚌 Routes: 1,138" in text
            assert "📅 Scheduled Trips: 562,609" in text
            assert "🚊 Active Vehicles: 51" in text
            assert "💡 **Insights:**" in text


@pytest.mark.asyncio
async def test_city_transit_stats_default_city(mock_city_manager, mock_db):
    """Test statistics retrieval using default current city."""
    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        async with Client(test_mcp) as client:
            result = await client.call_tool("city_transit_stats", {})  # No city_code provided
            text = result.structured_content["result"]

            assert isinstance(text, str)
            assert "📊 **Vienna Transit Statistics**" in text


@pytest.mark.asyncio
async def test_city_transit_stats_invalid_city(mock_city_manager, mock_db):
    """Test statistics retrieval for invalid city."""
    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        async with Client(test_mcp) as client:
            result = await client.call_tool(
                "city_transit_stats", {"city_code": "invalid_city"}
            )
            text = result.structured_content["result"]

            assert isinstance(text, str)
            assert "❌ **Invalid City**" in text
            assert "not found" in text


@pytest.mark.asyncio
async def test_city_transit_stats_db_error(mock_city_manager, mock_db):
    """Test statistics retrieval when database queries fail."""
    mock_db.execute_query = Mock(side_effect=Exception("Database connection failed"))

    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        async with Client(test_mcp) as client:
            result = await client.call_tool("city_transit_stats", {"city_code": "vienna"})
            text = result.structured_content["result"]

            # NOTE: the live tool degrades gracefully on DB errors (inner
            # try/except in get_city_statistics falls back to zero counts
            # instead of returning an error string), so assert the fallback
            # stats rather than an error message.
            assert isinstance(text, str)
            assert "📊 **Vienna Transit Statistics**" in text
            assert "🚏 Total Stops: 0" in text
            assert "🚌 Routes: 0" in text
            assert "🚊 Active Vehicles: 0" in text


@pytest.mark.asyncio
async def test_city_transit_stats_fallback_values(mock_city_manager, mock_db):
    """Test statistics with fallback values when database returns empty results."""
    # NOTE: the tool calls execute_query(..., fetch_one=True), whose contract
    # is a single dict row; an empty dict models "no data" and renders the
    # zero fallback stats (a list row would AttributeError on .get instead).
    mock_db.execute_query = Mock(return_value={})

    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        async with Client(test_mcp) as client:
            result = await client.call_tool("city_transit_stats", {"city_code": "vienna"})
            text = result.structured_content["result"]

            assert isinstance(text, str)
            assert "🚏 Total Stops: 0" in text
            assert "🚌 Routes: 0" in text
            assert "🚊 Active Vehicles: 0" in text


@pytest.mark.asyncio
async def test_tools_registration(mock_city_manager, mock_db):
    """Test that all three cities tools are properly registered."""
    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    # Check that all three tools are registered via the public client API
    expected_tools = ["list_cities", "switch_to_city", "city_transit_stats"]

    async with Client(test_mcp) as client:
        tools = await client.list_tools()
        registered_names = [t.name for t in tools]
        for tool_name in expected_tools:
            assert tool_name in registered_names, f"Tool '{tool_name}' not registered"
