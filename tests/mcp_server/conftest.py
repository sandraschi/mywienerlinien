"""Pytest configuration and shared fixtures for MCP server tests."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastmcp import FastMCP

# Add frontend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "frontend"))

from mcp_server.models.departures import Departure, DepartureResponse
from mcp_server.models.journey import JourneyPlan, JourneySegment
from mcp_server.models.stations import Station, StationSearchResponse
from mcp_server.models.status import LineStatusResponse, ServiceStatus


@pytest.fixture
def mock_mcp_server() -> FastMCP:
    """Create a mock FastMCP server instance for testing."""
    return FastMCP(name="test-vienna-transit", version="1.0.0")


@pytest.fixture
def mock_data_loader():
    """Create a mock data loader with sample data."""
    loader = MagicMock()

    # Mock stations
    mock_stations = [
        Mock(name="Stephansplatz", rbl="1234", type="metro", zone="100", lat=48.2085, lng=16.3731),
        Mock(name="Hauptbahnhof", rbl="5678", type="metro", zone="100", lat=48.1847, lng=16.3786),
        Mock(name="Schwedenplatz", rbl="9012", type="metro", zone="100", lat=48.2119, lng=16.3778),
    ]
    loader.load_stations = Mock(return_value=mock_stations)

    # Mock find_station_by_name
    def find_station(name: str):
        for station in mock_stations:
            if name.lower() in station.name.lower():
                return station
        return None

    loader.find_station_by_name = Mock(side_effect=find_station)

    return loader


@pytest.fixture
def mock_vehicle_service():
    """Create a mock vehicle service."""
    service = MagicMock()

    # Mock collect_vehicle_data
    async def mock_collect(*args, **kwargs):
        return {
            "vehicles": [
                {
                    "line": "U1",
                    "destination": "Leopoldau",
                    "departure_time": "2025-01-15T14:30:00Z",
                    "countdown_minutes": 3,
                    "delay_minutes": None,
                    "platform": "1",
                    "vehicle_type": "metro",
                }
            ],
            "successful_requests": 1,
            "failed_requests": 0,
        }

    service.collect_vehicle_data = AsyncMock(side_effect=mock_collect)
    return service


@pytest.fixture
def mock_wiener_linien_api():
    """Create a mock Wiener Linien API response."""

    def create_monitor_response(rbl: str = "1234"):
        return {
            "data": {
                "monitors": [
                    {
                        "locationStop": {
                            "properties": {
                                "name": "Stephansplatz",
                                "title": "Stephansplatz",
                                "municipality": "Wien",
                                "coordinates": {"lat": 48.2085, "lon": 16.3731},
                            }
                        },
                        "lines": [
                            {
                                "name": "U1",
                                "towards": "Leopoldau",
                                "direction": "H",
                                "platform": "1",
                                "departures": {
                                    "departure": [
                                        {
                                            "departureId": 12345,
                                            "departureTime": {
                                                "timePlanned": "2025-01-15T14:30:00.000+0100",
                                                "timeReal": "2025-01-15T14:30:00.000+0100",
                                                "countdown": 3,
                                            },
                                            "vehicle": {
                                                "name": "U1",
                                                "towards": "Leopoldau",
                                                "type": "ptMetro",
                                                "latitude": 48.2085,
                                                "longitude": 16.3731,
                                            },
                                        }
                                    ]
                                },
                            }
                        ],
                    }
                ]
            },
            "message": {
                "value": "OK",
                "messageCode": 1,
                "serverTime": "2025-01-15T14:27:00.000+0100",
            },
        }

    return create_monitor_response


@pytest.fixture
def sample_departure_response() -> DepartureResponse:
    """Create a sample departure response for testing."""
    return DepartureResponse(
        station_name="Stephansplatz",
        station_rbl="1234",
        departures=[
            Departure(
                line="U1",
                destination="Leopoldau",
                departure_time="2025-01-15T14:30:00Z",
                countdown_minutes=3,
                delay_minutes=None,
                platform="1",
                vehicle_type="metro",
            )
        ],
        timestamp="2025-01-15T14:27:00Z",
    )


@pytest.fixture
def sample_station_search_response() -> StationSearchResponse:
    """Create a sample station search response for testing."""
    return StationSearchResponse(
        query="Stephans",
        results=[
            Station(
                name="Stephansplatz",
                rbl="1234",
                type="metro",
                zone="100",
                lat=48.2085,
                lng=16.3731,
            )
        ],
        count=1,
    )


@pytest.fixture
def sample_journey_plan() -> JourneyPlan:
    """Create a sample journey plan for testing."""
    return JourneyPlan(
        from_station="Stephansplatz",
        to_station="Hauptbahnhof",
        departure_time="2025-01-15T14:30:00Z",
        total_duration_minutes=15,
        segments=[
            JourneySegment(
                line="U1",
                from_station="Stephansplatz",
                to_station="Hauptbahnhof",
                departure_time="2025-01-15T14:30:00Z",
                arrival_time="2025-01-15T14:45:00Z",
                duration_minutes=15,
                vehicle_type="metro",
            )
        ],
        transfers=0,
        estimated_cost="€2.40",
    )


@pytest.fixture
def sample_line_status_response() -> LineStatusResponse:
    """Create a sample line status response for testing."""
    return LineStatusResponse(
        line_filter=None,
        statuses=[
            ServiceStatus(
                line=None,
                status="operational",
                severity="low",
                title="All lines operational",
                description="All Vienna transit lines are operating normally.",
                affected_stations=[],
                start_time=None,
                end_time=None,
            )
        ],
        timestamp="2025-01-15T14:27:00Z",
    )


@pytest.fixture
def mock_requests_get():
    """Mock requests.get for API calls."""
    with patch("requests.get") as mock_get:
        yield mock_get


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks before each test."""
    yield
    # Cleanup if needed
