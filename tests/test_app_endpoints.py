"""High-level endpoint behaviour tests for the FastAPI application."""

from __future__ import annotations

import types
from datetime import datetime

from frontend.data_loader import Line


def test_get_vehicles_endpoint_uses_cache(app_module, app_client, monkeypatch):
    """Repeated calls should reuse cached data rather than hitting the API."""

    calls = []

    def fake_collect(**kwargs):
        calls.append(kwargs)
        return {
            "vehicles": [{"id": "vehicle-1"}, {"id": "vehicle-2"}],
            "successful_requests": 2,
            "failed_requests": 0,
        }

    monkeypatch.setattr(app_module, "collect_vehicle_data", fake_collect)

    first_response = app_client.get("/api/vehicles")
    first_payload = first_response.json()

    assert first_response.status_code == 200
    assert first_payload["successful_requests"] == 2
    assert first_payload["failed_requests"] == 0
    assert first_payload["vehicles"]

    second_response = app_client.get("/api/vehicles")
    second_payload = second_response.json()

    assert second_response.status_code == 200
    assert len(calls) == 2
    assert second_payload["vehicles"] == first_payload["vehicles"]


def test_get_vehicles_handles_empty_results(app_module, app_client, monkeypatch):
    """Endpoint should gracefully handle empty or failed API responses."""

    monkeypatch.setattr(
        app_module,
        "collect_vehicle_data",
        lambda **kwargs: {"vehicles": [], "successful_requests": 0, "failed_requests": 1},
    )

    response = app_client.get("/api/vehicles")
    payload = response.json()

    assert response.status_code == 200
    assert payload["successful_requests"] == 0
    assert payload["failed_requests"] == 1


def test_get_vehicles_supports_multi_line_filter(app_module, app_client, monkeypatch):
    calls: list[dict] = []

    def fake_collect(**kwargs):
        calls.append(kwargs)
        return {"vehicles": [], "successful_requests": 0, "failed_requests": 0}

    monkeypatch.setattr(app_module, "collect_vehicle_data", fake_collect)

    response_multi = app_client.get("/api/vehicles?lines=U1,U2&lines=11A")
    assert response_multi.status_code == 200
    assert calls[-1]["lines"] == ["11A", "U1", "U2"]

    response_single = app_client.get("/api/vehicles?line=U4")
    assert response_single.status_code == 200
    assert calls[-1]["lines"] == ["U4"]


def test_get_lines_prefers_gtfs_catalog(app_module, app_client, monkeypatch):
    catalog = [
        {
            "name": "U1",
            "type": "Metro",
            "type_code": 1,
            "color": "#FF0000",
            "description": "Sample",
            "agency": "Wiener Linien",
            "trip_count": 10,
            "stop_count": 20,
        }
    ]

    monkeypatch.setattr(app_module.data_loader, "get_gtfs_line_catalog", lambda: catalog)

    response = app_client.get("/api/lines")
    assert response.status_code == 200
    assert response.json()["lines"] == catalog


def test_get_lines_falls_back_to_markdown(app_module, app_client, monkeypatch):
    monkeypatch.setattr(app_module.data_loader, "get_gtfs_line_catalog", lambda: [])
    monkeypatch.setattr(
        app_module.data_loader,
        "load_lines",
        lambda force_reload=False: [
            Line(
                name="U1",
                type="Metro",
                color="#FF0000",
                length="19 km",
                stations=20,
                description="Fallback line",
                frequency="5 min",
                operating_hours="04:30-00:30",
            )
        ],
    )

    response = app_client.get("/api/lines")
    payload = response.json()["lines"]

    assert response.status_code == 200
    assert payload[0]["name"] == "U1"
    assert payload[0]["description"] == "Fallback line"


def test_system_status_endpoint_returns_expected_fields(app_module, app_client, monkeypatch):
    """Verify the /api/status endpoint returns structured status data."""

    class DummyManager:
        def get_connected_clients_count(self) -> int:
            return 3

        def get_vehicle_count(self) -> int:
            return 7

        def get_vehicle_total_count(self) -> int:
            return 9

        def get_filters_summary(self) -> dict:
            return {"clients": 1, "line_filters": 1, "type_filters": 0}

    manager = DummyManager()
    monkeypatch.setattr(app_module, "get_websocket_manager", lambda: manager)

    monitor = types.SimpleNamespace(
        get_active_disruptions=lambda: ["disruption"],
        last_check=datetime(2024, 1, 1, 12, 0, 0),
        get_disruption_summary=lambda: {"active": 1},
    )
    monkeypatch.setattr(app_module, "disruption_monitor", monitor)

    cache_status = {"routes_loaded": True}
    monkeypatch.setattr(app_module.data_loader, "get_cache_status", lambda: cache_status)

    response = app_client.get("/api/status")
    payload = response.json()

    assert response.status_code == 200
    assert payload["websocket_clients"] == 3
    assert payload["vehicle_count"] == 7
    assert payload["active_disruptions"] == 1
    assert payload["data_cache_status"] == cache_status
    assert "timestamp" in payload


def test_get_line_overview_endpoint(app_module, app_client, monkeypatch):
    monkeypatch.setattr(
        app_module.data_loader,
        "get_line_by_name",
        lambda name: Line(
            name=name.upper(),
            type="Metro",
            color="#FF0000",
            length="19 km",
            stations=20,
            description="Test line",
            frequency="5 min",
            operating_hours="04:30-00:30",
        ),
    )

    monkeypatch.setattr(
        app_module.db,
        "get_line_overview",
        lambda name: {
            "route_id": "100",
            "line": name.upper(),
            "name": "Sample Route",
            "route_type": 1,
            "route_type_name": "Metro",
            "color": "#FF0000",
            "text_color": "#FFFFFF",
            "trip_count": 10,
            "stop_count": 25,
            "variants": [],
        },
    )

    response = app_client.get("/api/lines/u1")
    payload = response.json()

    assert response.status_code == 200
    assert payload["line"]["name"] == "U1"
    assert payload["overview"]["route_id"] == "100"


def test_get_line_route_endpoint(app_module, app_client, monkeypatch):
    monkeypatch.setattr(
        app_module.data_loader,
        "get_gtfs_route",
        lambda name: {
            "line": name.upper(),
            "type": "Metro",
            "type_code": 1,
            "type_name": "Metro",
            "color": "#FF0000",
            "text_color": "#FFFFFF",
            "segments": [
                {
                    "route_id": "100",
                    "shape_id": "shape-1",
                    "direction_id": 0,
                    "coordinates": [[48.2, 16.3], [48.21, 16.31]],
                }
            ],
            "stops": [
                {
                    "id": "stop-1",
                    "name": "Station A",
                    "rbl": "1000",
                    "lat": 48.2,
                    "lng": 16.3,
                    "sequence": 1,
                },
            ],
            "overview": None,
        },
    )

    response = app_client.get("/api/lines/U1/route")
    payload = response.json()

    assert response.status_code == 200
    assert payload["route"]["line"] == "U1"
    assert payload["route"]["segments"]
    assert payload["route"]["stops"]


def test_get_line_route_endpoint_returns_404_when_missing(app_module, app_client, monkeypatch):
    monkeypatch.setattr(app_module.data_loader, "get_gtfs_route", lambda name: None)

    response = app_client.get("/api/lines/U99/route")
    assert response.status_code == 404


def test_get_line_stations_endpoint(app_module, app_client, monkeypatch):
    stations = [
        {
            "id": "stop-1",
            "name": "Station A",
            "rbl": "1000",
            "lat": 48.2,
            "lng": 16.3,
            "sequence": 1,
        },
        {
            "id": "stop-2",
            "name": "Station B",
            "rbl": "1001",
            "lat": 48.21,
            "lng": 16.31,
            "sequence": 2,
        },
    ]
    monkeypatch.setattr(app_module.data_loader, "get_gtfs_line_stations", lambda name: stations)

    response = app_client.get("/api/lines/U1/stations")
    payload = response.json()

    assert response.status_code == 200
    assert payload["line"] == "U1"
    assert payload["stations"] == stations
