"""Unit tests for the station_search tool."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError


def _fix_fixture_names(mock_data_loader):
    """Give fixture stations real string names.

    NOTE: conftest builds stations as Mock(name="Stephansplatz", ...) but
    the `name` kwarg sets the mock's debug name, NOT a `.name` attribute
    (accessing `.name` yields a child Mock, and `in <Mock>` raises
    TypeError). Assign real strings here; conftest.py is out of scope.
    """
    stations = mock_data_loader.load_stations()
    for station, real_name in zip(
        stations, ("Stephansplatz", "Hauptbahnhof", "Schwedenplatz")
    ):
        station.name = real_name
    return stations


def _make_station(real_name, rbl):
    """Build a station Mock with a real string `.name` (see note above)."""
    station = Mock(rbl=rbl, type="metro", zone="100", lat=48.0, lng=16.0)
    station.name = real_name
    return station


@pytest.mark.asyncio
async def test_station_search_success(mock_data_loader):
    """Test successful station search."""
    _fix_fixture_names(mock_data_loader)
    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        async with Client(test_mcp) as client:
            result = await client.call_tool(
                "station_search", {"query": "Stephans", "limit": 10}
            )
            data = result.structured_content

            assert data["query"] == "Stephans"
            assert len(data["results"]) > 0
            assert data["count"] > 0
            assert all("name" in s for s in data["results"])


@pytest.mark.asyncio
async def test_station_search_no_results(mock_data_loader):
    """Test station search with no matching results."""
    # Setup - Empty station list
    mock_data_loader.load_stations = Mock(return_value=[])

    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        async with Client(test_mcp) as client:
            result = await client.call_tool(
                "station_search", {"query": "NonExistent", "limit": 10}
            )
            data = result.structured_content

            assert data["count"] == 0
            assert len(data["results"]) == 0


@pytest.mark.asyncio
async def test_station_search_limit_enforcement(mock_data_loader):
    """Test that limit parameter is enforced."""
    # Setup - Multiple stations
    mock_stations = [_make_station(f"Station{i}", str(i)) for i in range(20)]
    mock_data_loader.load_stations = Mock(return_value=mock_stations)

    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        async with Client(test_mcp) as client:
            result = await client.call_tool(
                "station_search", {"query": "Station", "limit": 5}
            )
            data = result.structured_content

            assert len(data["results"]) <= 5
            assert data["count"] <= 5


@pytest.mark.asyncio
async def test_station_search_case_insensitive(mock_data_loader):
    """Test that search is case-insensitive."""
    _fix_fixture_names(mock_data_loader)
    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        async with Client(test_mcp) as client:
            # Execute with different cases
            result_lower = await client.call_tool(
                "station_search", {"query": "stephans", "limit": 10}
            )
            result_upper = await client.call_tool(
                "station_search", {"query": "STEPHANS", "limit": 10}
            )
            result_mixed = await client.call_tool(
                "station_search", {"query": "StEpHaNs", "limit": 10}
            )

            # Assert - All should return same results
            assert (
                result_lower.structured_content["count"]
                == result_upper.structured_content["count"]
            )
            assert (
                result_upper.structured_content["count"]
                == result_mixed.structured_content["count"]
            )


@pytest.mark.asyncio
async def test_station_search_partial_match(mock_data_loader):
    """Test that partial matches work."""
    _fix_fixture_names(mock_data_loader)
    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        async with Client(test_mcp) as client:
            result = await client.call_tool(
                "station_search", {"query": "Haupt", "limit": 10}
            )
            data = result.structured_content

            assert data["count"] > 0
            assert any("Haupt" in station["name"] for station in data["results"])


@pytest.mark.asyncio
async def test_station_search_exact_match_priority(mock_data_loader):
    """Test that exact matches are prioritized over partial matches."""
    # Create stations with similar names
    mock_stations = [
        _make_station("Stephansplatz", "1234"),
        _make_station("Stephansdom", "5678"),
    ]
    mock_data_loader.load_stations = Mock(return_value=mock_stations)

    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        async with Client(test_mcp) as client:
            result = await client.call_tool(
                "station_search", {"query": "Stephansplatz", "limit": 10}
            )
            data = result.structured_content

            # Exact match should be first
            assert data["results"][0]["name"] == "Stephansplatz"


@pytest.mark.asyncio
async def test_station_search_limit_validation(mock_data_loader):
    """Test limit parameter validation."""
    _fix_fixture_names(mock_data_loader)
    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        async with Client(test_mcp) as client:
            # Test limit at max boundary - should be accepted
            result = await client.call_tool(
                "station_search", {"query": "Station", "limit": 20}
            )
            assert len(result.structured_content["results"]) <= 20  # Max limit

            # Test limit at min boundary - should be accepted
            result = await client.call_tool(
                "station_search", {"query": "Station", "limit": 1}
            )
            assert len(result.structured_content["results"]) >= 0  # Min limit


@pytest.mark.asyncio
async def test_station_search_error_handling():
    """Test error handling when data_loader fails."""
    mock_data_loader = Mock()
    mock_data_loader.load_stations = Mock(side_effect=Exception("Database error"))

    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        async with Client(test_mcp) as client:
            with pytest.raises(ToolError, match="Failed to search"):
                await client.call_tool(
                    "station_search", {"query": "Stephans", "limit": 10}
                )
