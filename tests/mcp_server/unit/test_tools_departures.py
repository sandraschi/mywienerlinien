"""Unit tests for the next_departures tool."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError


def _fix_fixture_names(mock_data_loader):
    """Give fixture stations real string names.

    NOTE: conftest builds stations as Mock(name="Stephansplatz", ...) but
    the `name` kwarg sets the mock's debug name, NOT a `.name` attribute
    (accessing `.name` yields a child Mock). The live tool needs real
    strings, so assign them here (fixture is function-scoped; safe to
    mutate). conftest.py itself is out of scope for this task.
    """
    stations = mock_data_loader.load_stations()
    for station, real_name in zip(
        stations, ("Stephansplatz", "Hauptbahnhof", "Schwedenplatz")
    ):
        station.name = real_name
    return stations


@pytest.mark.asyncio
async def test_next_departures_success(mock_data_loader):
    """Test successful departure retrieval."""
    # Setup mock station
    _fix_fixture_names(mock_data_loader)
    mock_station = mock_data_loader.load_stations()[0]
    mock_station_dict = {
        "name": mock_station.name,
        "rbl": mock_station.rbl,
        "type": mock_station.type,
    }

    # Setup mock vehicle data
    now = datetime.utcnow()
    future_time = now + timedelta(minutes=5)
    mock_vehicles = [
        {
            "line": "U1",
            "next_station": "Leopoldau",
            "timestamp": future_time.isoformat() + "Z",
            "delay": None,
            "platform": "1",
            "type": "metro",
        },
        {
            "line": "U3",
            "next_station": "Ottakring",
            "timestamp": (now + timedelta(minutes=8)).isoformat() + "Z",
            "delay": 2,
            "platform": "2",
            "type": "metro",
        },
    ]

    with patch("mcp_server.tools.departures.data_loader", mock_data_loader):
        with patch(
            "mcp_server.tools.departures.find_station_by_name", return_value=mock_station_dict
        ):
            with patch(
                "mcp_server.tools.departures.collect_vehicle_data",
                return_value={"vehicles": mock_vehicles},
            ):
                # Import and register tool
                from mcp_server.tools.departures import register_departures_tool

                test_mcp = FastMCP(name="test", version="1.0.0")
                register_departures_tool(test_mcp)

                async with Client(test_mcp) as client:
                    result = await client.call_tool(
                        "next_departures", {"station": "Stephansplatz", "max_results": 5}
                    )
                    data = result.structured_content

                    # Assertions
                    assert data["station_name"] == mock_station.name
                    assert data["station_rbl"] == mock_station.rbl
                    assert len(data["departures"]) == 2
                    assert data["departures"][0]["line"] == "U1"
                    assert data["departures"][0]["destination"] == "Leopoldau"
                    assert data["departures"][0]["countdown_minutes"] >= 0
                    assert data["departures"][0]["delay_minutes"] is None
                    assert data["departures"][1]["delay_minutes"] == 2


@pytest.mark.asyncio
async def test_next_departures_station_not_found(mock_data_loader):
    """Test departure retrieval with non-existent station."""
    _fix_fixture_names(mock_data_loader)
    with patch("mcp_server.tools.departures.data_loader", mock_data_loader):
        with patch("mcp_server.tools.departures.find_station_by_name", return_value=None):
            from mcp_server.tools.departures import register_departures_tool

            test_mcp = FastMCP(name="test", version="1.0.0")
            register_departures_tool(test_mcp)

            async with Client(test_mcp) as client:
                with pytest.raises(ToolError, match="not found"):
                    await client.call_tool(
                        "next_departures", {"station": "NonExistentStation", "max_results": 5}
                    )


@pytest.mark.asyncio
async def test_next_departures_max_results_validation(mock_data_loader):
    """Test max_results parameter validation."""
    mock_station_dict = {
        "name": "Stephansplatz",
        "rbl": "1234",
        "type": "metro",
    }

    with patch("mcp_server.tools.departures.data_loader", mock_data_loader):
        with patch(
            "mcp_server.tools.departures.find_station_by_name", return_value=mock_station_dict
        ):
            with patch(
                "mcp_server.tools.departures.collect_vehicle_data",
                return_value={"vehicles": []},
            ):
                from mcp_server.tools.departures import register_departures_tool

                test_mcp = FastMCP(name="test", version="1.0.0")
                register_departures_tool(test_mcp)

                async with Client(test_mcp) as client:
                    # Test that max_results is clamped to valid range
                    # The tool should accept any value and clamp it internally
                    result = await client.call_tool(
                        "next_departures", {"station": "Stephansplatz", "max_results": 10}
                    )
                    assert isinstance(result.structured_content, dict)

                    result = await client.call_tool(
                        "next_departures", {"station": "Stephansplatz", "max_results": 1}
                    )
                    assert isinstance(result.structured_content, dict)


@pytest.mark.asyncio
async def test_next_departures_api_error_handling(mock_data_loader):
    """Test handling of API errors."""
    mock_station_dict = {
        "name": "Stephansplatz",
        "rbl": "1234",
        "type": "metro",
    }

    with patch("mcp_server.tools.departures.data_loader", mock_data_loader):
        with patch(
            "mcp_server.tools.departures.find_station_by_name", return_value=mock_station_dict
        ):
            with patch(
                "mcp_server.tools.departures.collect_vehicle_data",
                side_effect=Exception("API Error"),
            ):
                from mcp_server.tools.departures import register_departures_tool

                test_mcp = FastMCP(name="test", version="1.0.0")
                register_departures_tool(test_mcp)

                async with Client(test_mcp) as client:
                    with pytest.raises(ToolError, match="Failed to fetch"):
                        await client.call_tool(
                            "next_departures", {"station": "Stephansplatz", "max_results": 5}
                        )


@pytest.mark.asyncio
async def test_next_departures_partial_station_name(mock_data_loader):
    """Test departure retrieval with partial station name."""
    _fix_fixture_names(mock_data_loader)
    mock_station = mock_data_loader.load_stations()[0]
    mock_station_dict = {
        "name": mock_station.name,
        "rbl": mock_station.rbl,
        "type": mock_station.type,
    }

    with patch("mcp_server.tools.departures.data_loader", mock_data_loader):
        with patch(
            "mcp_server.tools.departures.find_station_by_name", return_value=mock_station_dict
        ):
            with patch(
                "mcp_server.tools.departures.collect_vehicle_data",
                return_value={"vehicles": []},
            ):
                from mcp_server.tools.departures import register_departures_tool

                test_mcp = FastMCP(name="test", version="1.0.0")
                register_departures_tool(test_mcp)

                async with Client(test_mcp) as client:
                    # Test with partial name
                    result = await client.call_tool(
                        "next_departures", {"station": "Stephans", "max_results": 5}
                    )
                    assert result.structured_content["station_name"] == mock_station.name


@pytest.mark.asyncio
async def test_next_departures_empty_response(mock_data_loader):
    """Test handling of empty API response."""
    mock_station_dict = {
        "name": "Stephansplatz",
        "rbl": "1234",
        "type": "metro",
    }

    with patch("mcp_server.tools.departures.data_loader", mock_data_loader):
        with patch(
            "mcp_server.tools.departures.find_station_by_name", return_value=mock_station_dict
        ):
            with patch(
                "mcp_server.tools.departures.collect_vehicle_data", return_value={"vehicles": []}
            ):
                from mcp_server.tools.departures import register_departures_tool

                test_mcp = FastMCP(name="test", version="1.0.0")
                register_departures_tool(test_mcp)

                async with Client(test_mcp) as client:
                    result = await client.call_tool(
                        "next_departures", {"station": "Stephansplatz", "max_results": 5}
                    )
                    data = result.structured_content

                    assert data["station_name"] == "Stephansplatz"
                    assert len(data["departures"]) == 0


@pytest.mark.asyncio
async def test_next_departures_max_results_limit(mock_data_loader):
    """Test that max_results limits the number of departures returned."""
    mock_station_dict = {
        "name": "Stephansplatz",
        "rbl": "1234",
        "type": "metro",
    }

    # Create many vehicles
    now = datetime.utcnow()
    mock_vehicles = [
        {
            "line": f"U{i % 5 + 1}",
            "next_station": f"Station{i}",
            "timestamp": (now + timedelta(minutes=i + 1)).isoformat() + "Z",
            "delay": None,
            "type": "metro",
        }
        for i in range(15)
    ]

    with patch("mcp_server.tools.departures.data_loader", mock_data_loader):
        with patch(
            "mcp_server.tools.departures.find_station_by_name", return_value=mock_station_dict
        ):
            with patch(
                "mcp_server.tools.departures.collect_vehicle_data",
                return_value={"vehicles": mock_vehicles},
            ):
                from mcp_server.tools.departures import register_departures_tool

                test_mcp = FastMCP(name="test", version="1.0.0")
                register_departures_tool(test_mcp)

                async with Client(test_mcp) as client:
                    result = await client.call_tool(
                        "next_departures", {"station": "Stephansplatz", "max_results": 5}
                    )

                    assert len(result.structured_content["departures"]) == 5


@pytest.mark.asyncio
async def test_next_departures_countdown_calculation(mock_data_loader):
    """Test countdown calculation from timestamps."""
    mock_station_dict = {
        "name": "Stephansplatz",
        "rbl": "1234",
        "type": "metro",
    }

    now = datetime.utcnow()
    future_time = now + timedelta(minutes=7, seconds=30)

    mock_vehicles = [
        {
            "line": "U1",
            "next_station": "Leopoldau",
            "timestamp": future_time.isoformat() + "Z",
            "delay": None,
            "type": "metro",
        }
    ]

    with patch("mcp_server.tools.departures.data_loader", mock_data_loader):
        with patch(
            "mcp_server.tools.departures.find_station_by_name", return_value=mock_station_dict
        ):
            with patch(
                "mcp_server.tools.departures.collect_vehicle_data",
                return_value={"vehicles": mock_vehicles},
            ):
                from mcp_server.tools.departures import register_departures_tool

                test_mcp = FastMCP(name="test", version="1.0.0")
                register_departures_tool(test_mcp)

                async with Client(test_mcp) as client:
                    result = await client.call_tool(
                        "next_departures", {"station": "Stephansplatz", "max_results": 5}
                    )
                    data = result.structured_content

                    assert len(data["departures"]) == 1
                    # Countdown should be approximately 7-8 minutes
                    assert 6 <= data["departures"][0]["countdown_minutes"] <= 8
