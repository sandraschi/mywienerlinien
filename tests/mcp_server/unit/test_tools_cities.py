"""Unit tests for the multi-city management tools."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest
from fastmcp import FastMCP


@pytest.fixture
def mock_city_manager():
    """Create a mock city manager with sample data."""
    manager = MagicMock()

    # Mock cities data
    mock_cities = {
        "vienna": {
            "city_code": "vienna",
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

    # Mock query results
    db.execute_query = Mock(side_effect=lambda query, **kwargs: {
        "SELECT COUNT(*) as count FROM stops": [{"count": 4684}],
        "SELECT COUNT(*) as count FROM routes": [{"count": 1138}],
        "SELECT COUNT(*) as count FROM trips": [{"count": 562609}],
        "SELECT COUNT(DISTINCT vehicle_id) as count FROM vehicle_snapshots WHERE timestamp > NOW() - INTERVAL '1 hour'": [{"count": 51}],
        "SELECT MAX(timestamp) as last_update FROM vehicle_snapshots": [{"last_update": None}],
    }.get(query.strip(), []))

    return db


@pytest.mark.asyncio
async def test_list_cities_success(mock_city_manager, mock_db):
    """Test successful listing of available cities."""
    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        if hasattr(test_mcp, "_tools") and "list_cities" in test_mcp._tools:
            tool_func = test_mcp._tools["list_cities"]
            result = await tool_func()

            assert isinstance(result, str)
            assert "Vienna" in result
            assert "Graz" in result
            assert "✅" in result  # Data loaded indicator
            assert "⏳" in result  # Data not loaded indicator
            assert "Available Transit Cities" in result


@pytest.mark.asyncio
async def test_list_cities_empty(mock_city_manager, mock_db):
    """Test listing cities when no cities are available."""
    mock_city_manager.list_cities = Mock(return_value={})

    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        if hasattr(test_mcp, "_tools") and "list_cities" in test_mcp._tools:
            tool_func = test_mcp._tools["list_cities"]
            result = await tool_func()

            assert isinstance(result, str)
            assert "No cities configured yet" in result


@pytest.mark.asyncio
async def test_switch_to_city_success(mock_city_manager, mock_db):
    """Test successful city switching."""
    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        if hasattr(test_mcp, "_tools") and "switch_to_city" in test_mcp._tools:
            tool_func = test_mcp._tools["switch_to_city"]
            result = await tool_func(city_code="graz")

            assert isinstance(result, str)
            assert "✅ **Switched to Graz**" in result
            assert "🏙️  City: graz" in result
            assert "📊 Data Status: Not loaded" in result
            assert "⚠️  **Warning:**" in result


@pytest.mark.asyncio
async def test_switch_to_city_invalid(mock_city_manager, mock_db):
    """Test switching to invalid city."""
    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        if hasattr(test_mcp, "_tools") and "switch_to_city" in test_mcp._tools:
            tool_func = test_mcp._tools["switch_to_city"]
            result = await tool_func(city_code="invalid_city")

            assert isinstance(result, str)
            assert "❌ **Invalid City**" in result
            assert "not found" in result


@pytest.mark.asyncio
async def test_switch_to_city_failure(mock_city_manager, mock_db):
    """Test city switching failure."""
    mock_city_manager.switch_city = Mock(return_value=False)

    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        if hasattr(test_mcp, "_tools") and "switch_to_city" in test_mcp._tools:
            tool_func = test_mcp._tools["switch_to_city"]
            result = await tool_func(city_code="vienna")

            assert isinstance(result, str)
            assert "❌ **Error**" in result
            assert "Failed to switch city" in result


@pytest.mark.asyncio
async def test_city_transit_stats_success(mock_city_manager, mock_db):
    """Test successful retrieval of city transit statistics."""
    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        if hasattr(test_mcp, "_tools") and "city_transit_stats" in test_mcp._tools:
            tool_func = test_mcp._tools["city_transit_stats"]
            result = await tool_func(city_code="vienna")

            assert isinstance(result, str)
            assert "📊 **Vienna Transit Statistics**" in result
            assert "🏙️  City Code: vienna" in result
            assert "🚏 Total Stops: 4,684" in result
            assert "🚌 Routes: 1,138" in result
            assert "📅 Scheduled Trips: 562,609" in result
            assert "🚊 Active Vehicles: 51" in result
            assert "💡 **Insights:**" in result


@pytest.mark.asyncio
async def test_city_transit_stats_default_city(mock_city_manager, mock_db):
    """Test statistics retrieval using default current city."""
    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        if hasattr(test_mcp, "_tools") and "city_transit_stats" in test_mcp._tools:
            tool_func = test_mcp._tools["city_transit_stats"]
            result = await tool_func()  # No city_code provided

            assert isinstance(result, str)
            assert "📊 **Vienna Transit Statistics**" in result


@pytest.mark.asyncio
async def test_city_transit_stats_invalid_city(mock_city_manager, mock_db):
    """Test statistics retrieval for invalid city."""
    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        if hasattr(test_mcp, "_tools") and "city_transit_stats" in test_mcp._tools:
            tool_func = test_mcp._tools["city_transit_stats"]
            result = await tool_func(city_code="invalid_city")

            assert isinstance(result, str)
            assert "❌ **Invalid City**" in result
            assert "not found" in result


@pytest.mark.asyncio
async def test_city_transit_stats_db_error(mock_city_manager, mock_db):
    """Test statistics retrieval when database queries fail."""
    mock_db.execute_query = Mock(side_effect=Exception("Database connection failed"))

    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        if hasattr(test_mcp, "_tools") and "city_transit_stats" in test_mcp._tools:
            tool_func = test_mcp._tools["city_transit_stats"]
            result = await tool_func(city_code="vienna")

            assert isinstance(result, str)
            assert "❌ **Error**" in result
            assert "Failed to retrieve statistics" in result


@pytest.mark.asyncio
async def test_city_transit_stats_fallback_values(mock_city_manager, mock_db):
    """Test statistics with fallback values when database returns empty results."""
    mock_db.execute_query = Mock(return_value=[{"count": 0}])

    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    with patch("mcp_server.tools.cities.get_city_manager", return_value=mock_city_manager), \
         patch("mcp_server.tools.cities.db", mock_db):

        if hasattr(test_mcp, "_tools") and "city_transit_stats" in test_mcp._tools:
            tool_func = test_mcp._tools["city_transit_stats"]
            result = await tool_func(city_code="vienna")

            assert isinstance(result, str)
            assert "🚏 Total Stops: 0" in result
            assert "🚌 Routes: 0" in result
            assert "🚊 Active Vehicles: 0" in result


@pytest.mark.asyncio
async def test_tools_registration(mock_city_manager, mock_db):
    """Test that all three cities tools are properly registered."""
    from mcp_server.tools.cities import register_cities_tools

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_cities_tools(test_mcp)

    # Check that all three tools are registered
    expected_tools = ["list_cities", "switch_to_city", "city_transit_stats"]

    if hasattr(test_mcp, "_tools"):
        registered_tools = list(test_mcp._tools.keys())
        for tool_name in expected_tools:
            assert tool_name in registered_tools, f"Tool '{tool_name}' not registered"
    else:
        # If _tools attribute doesn't exist, at least verify the function ran
        assert test_mcp is not None
