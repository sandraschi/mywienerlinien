"""Unit tests for Pydantic models."""

from __future__ import annotations

from mcp_server.models.departures import Departure, DepartureResponse
from mcp_server.models.journey import JourneyPlan, JourneySegment
from mcp_server.models.stations import Station, StationSearchResponse
from mcp_server.models.status import LineStatusResponse, ServiceStatus


def test_departure_model_validation():
    """Test Departure model validation."""
    departure = Departure(
        line="U1",
        destination="Leopoldau",
        departure_time="2025-01-15T14:30:00Z",
        countdown_minutes=3,
        delay_minutes=None,
        platform="1",
        vehicle_type="metro",
    )

    assert departure.line == "U1"
    assert departure.destination == "Leopoldau"
    assert departure.countdown_minutes == 3
    assert departure.delay_minutes is None


def test_departure_response_model():
    """Test DepartureResponse model."""
    response = DepartureResponse(
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

    assert response.station_name == "Stephansplatz"
    assert len(response.departures) == 1


def test_station_model():
    """Test Station model."""
    station = Station(
        name="Stephansplatz",
        rbl="1234",
        type="metro",
        zone="100",
        lat=48.2085,
        lng=16.3731,
    )

    assert station.name == "Stephansplatz"
    assert station.rbl == "1234"
    assert station.type == "metro"


def test_station_search_response_model():
    """Test StationSearchResponse model."""
    response = StationSearchResponse(
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

    assert response.query == "Stephans"
    assert response.count == 1
    assert len(response.results) == 1


def test_journey_segment_model():
    """Test JourneySegment model."""
    segment = JourneySegment(
        line="U1",
        from_station="Stephansplatz",
        to_station="Hauptbahnhof",
        departure_time="2025-01-15T14:30:00Z",
        arrival_time="2025-01-15T14:45:00Z",
        duration_minutes=15,
        vehicle_type="metro",
    )

    assert segment.line == "U1"
    assert segment.duration_minutes == 15
    assert segment.vehicle_type == "metro"


def test_journey_plan_model():
    """Test JourneyPlan model."""
    plan = JourneyPlan(
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

    assert plan.from_station == "Stephansplatz"
    assert plan.total_duration_minutes == 15
    assert plan.transfers == 0


def test_service_status_model():
    """Test ServiceStatus model."""
    status = ServiceStatus(
        line="U1",
        status="operational",
        severity="low",
        title="U1 operating normally",
        description="U1 line is operating on schedule.",
        affected_stations=[],
        start_time=None,
        end_time=None,
    )

    assert status.line == "U1"
    assert status.status == "operational"
    assert status.severity == "low"


def test_line_status_response_model():
    """Test LineStatusResponse model."""
    response = LineStatusResponse(
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

    assert response.line_filter is None
    assert len(response.statuses) == 1
