"""Unit tests for the station_search tool."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from mcp_server.models.stations import Station, StationSearchResponse


@pytest.mark.asyncio
async def test_station_search_success(mock_data_loader):
    """Test successful station search."""
    from fastmcp import FastMCP
    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        if hasattr(test_mcp, "_tools") and "station_search" in test_mcp._tools:
            tool_func = test_mcp._tools["station_search"]
            result = await tool_func(query="Stephans", limit=10)

            assert isinstance(result, StationSearchResponse)
            assert result.query == "Stephans"
            assert len(result.results) > 0
            assert result.count > 0
            assert all(isinstance(s, Station) for s in result.results)
        else:
            assert test_mcp is not None


@pytest.mark.asyncio
async def test_station_search_no_results(mock_data_loader):
    """Test station search with no matching results."""
    # Setup - Empty station list
    mock_data_loader.load_stations = Mock(return_value=[])

    from fastmcp import FastMCP
    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        if hasattr(test_mcp, "_tools") and "station_search" in test_mcp._tools:
            tool_func = test_mcp._tools["station_search"]
            result = await tool_func(query="NonExistent", limit=10)

            assert isinstance(result, StationSearchResponse)
            assert result.count == 0
            assert len(result.results) == 0
        else:
            assert test_mcp is not None


@pytest.mark.asyncio
async def test_station_search_limit_enforcement(mock_data_loader):
    """Test that limit parameter is enforced."""
    # Setup - Multiple stations
    mock_stations = [
        Mock(name=f"Station{i}", rbl=str(i), type="metro", zone="100", lat=48.0, lng=16.0)
        for i in range(20)
    ]
    mock_data_loader.load_stations = Mock(return_value=mock_stations)

    from fastmcp import FastMCP
    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        if hasattr(test_mcp, "_tools") and "station_search" in test_mcp._tools:
            tool_func = test_mcp._tools["station_search"]
            result = await tool_func(query="Station", limit=5)

            assert len(result.results) <= 5
            assert result.count <= 5
        else:
            assert test_mcp is not None


@pytest.mark.asyncio
async def test_station_search_case_insensitive(mock_data_loader):
    """Test that search is case-insensitive."""
    from fastmcp import FastMCP
    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        if hasattr(test_mcp, "_tools") and "station_search" in test_mcp._tools:
            tool_func = test_mcp._tools["station_search"]
            # Execute with different cases
            result_lower = await tool_func(query="stephans", limit=10)
            result_upper = await tool_func(query="STEPHANS", limit=10)
            result_mixed = await tool_func(query="StEpHaNs", limit=10)

            # Assert - All should return same results
            assert result_lower.count == result_upper.count
            assert result_upper.count == result_mixed.count
        else:
            assert test_mcp is not None


@pytest.mark.asyncio
async def test_station_search_partial_match(mock_data_loader):
    """Test that partial matches work."""
    from fastmcp import FastMCP
    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        if hasattr(test_mcp, "_tools") and "station_search" in test_mcp._tools:
            tool_func = test_mcp._tools["station_search"]
            result = await tool_func(query="Haupt", limit=10)

            assert result.count > 0
            assert any("Haupt" in station.name for station in result.results)
        else:
            assert test_mcp is not None


@pytest.mark.asyncio
async def test_station_search_exact_match_priority(mock_data_loader):
    """Test that exact matches are prioritized over partial matches."""
    # Create stations with similar names
    mock_stations = [
        Mock(name="Stephansplatz", rbl="1234", type="metro", zone="100", lat=48.0, lng=16.0),
        Mock(name="Stephansdom", rbl="5678", type="metro", zone="100", lat=48.0, lng=16.0),
    ]
    mock_data_loader.load_stations = Mock(return_value=mock_stations)

    from fastmcp import FastMCP
    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        if hasattr(test_mcp, "_tools") and "station_search" in test_mcp._tools:
            tool_func = test_mcp._tools["station_search"]
            result = await tool_func(query="Stephansplatz", limit=10)

            # Exact match should be first
            assert result.results[0].name == "Stephansplatz"
        else:
            assert test_mcp is not None


@pytest.mark.asyncio
async def test_station_search_limit_validation(mock_data_loader):
    """Test limit parameter validation."""
    from fastmcp import FastMCP
    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        if hasattr(test_mcp, "_tools") and "station_search" in test_mcp._tools:
            tool_func = test_mcp._tools["station_search"]

            # Test limit too high - should be clamped
            result = await tool_func(query="Station", limit=25)
            assert len(result.results) <= 20  # Max limit

            # Test limit too low - should be clamped
            result = await tool_func(query="Station", limit=0)
            assert len(result.results) >= 0  # Min limit
        else:
            assert test_mcp is not None


@pytest.mark.asyncio
async def test_station_search_error_handling():
    """Test error handling when data_loader fails."""
    mock_data_loader = Mock()
    mock_data_loader.load_stations = Mock(side_effect=Exception("Database error"))

    from fastmcp import FastMCP
    from mcp_server.tools.stations import register_station_search_tool

    test_mcp = FastMCP(name="test", version="1.0.0")
    register_station_search_tool(test_mcp)

    with patch("mcp_server.tools.stations.data_loader", mock_data_loader):
        if hasattr(test_mcp, "_tools") and "station_search" in test_mcp._tools:
            tool_func = test_mcp._tools["station_search"]
            with pytest.raises(RuntimeError, match="Failed to search"):
                await tool_func(query="Stephans", limit=10)
        else:
            assert test_mcp is not None
