"""Tests for vehicle snapshot caching and filtering logic.

Covers the schedule-interpolated snapshot architecture in
``frontend.vehicle_service``: per-key snapshots, TTL refresh, and
post-snapshot type/line filtering. The schedule DB layer is stubbed via
``_schedule_pseudo_vehicles`` so no database is required.
"""

from __future__ import annotations

import pytest

from frontend import vehicle_service


@pytest.fixture(autouse=True)
def reset_cache():
    """Ensure each test starts with a clean snapshot cache."""
    vehicle_service.clear_vehicle_cache()
    yield
    vehicle_service.clear_vehicle_cache()


def _canned(line: str = "U1", vtype: str = "metro") -> list[dict]:
    return [
        {
            "line": line,
            "type": vtype,
            "next_station": "Stephansplatz",
            "countdown": 3,
            "timestamp": "2025-01-15T14:30:00Z",
        }
    ]


def _patch_schedule(monkeypatch, fake):
    monkeypatch.setattr(vehicle_service, "_schedule_pseudo_vehicles", fake)


def test_collect_vehicle_data_uses_cache(monkeypatch):
    """Subsequent calls within the TTL reuse the cached snapshot."""
    calls = {"count": 0}

    def fake_schedule(line_name: str):
        calls["count"] += 1
        return _canned()

    _patch_schedule(monkeypatch, fake_schedule)

    expected_calls = len(vehicle_service.DEFAULT_PSEUDO_LINES)
    first = vehicle_service.collect_vehicle_data()
    assert calls["count"] == expected_calls
    assert first["vehicles"]

    second = vehicle_service.collect_vehicle_data()
    assert calls["count"] == expected_calls, "snapshot should be reused within TTL"
    assert second["vehicles"] == first["vehicles"]


def test_collect_vehicle_data_filters_by_type(monkeypatch):
    """Vehicle type filtering is applied after the snapshot."""
    def fake_schedule(line_name: str):
        idx = vehicle_service.DEFAULT_PSEUDO_LINES.index(line_name)
        vtype = "bus" if idx % 2 == 0 else "tram"
        return _canned(vtype=vtype)

    _patch_schedule(monkeypatch, fake_schedule)

    result = vehicle_service.collect_vehicle_data(vehicle_type="bus")
    assert result["vehicles"]
    assert all(vehicle["type"] == "bus" for vehicle in result["vehicles"])


def test_collect_vehicle_data_filters_by_lines(monkeypatch):
    """Filtering by multiple lines includes only requested lines."""
    def fake_schedule(line_name: str):
        return _canned(line=line_name.upper())

    _patch_schedule(monkeypatch, fake_schedule)

    wanted = [vehicle_service.DEFAULT_PSEUDO_LINES[0].upper(),
              vehicle_service.DEFAULT_PSEUDO_LINES[1].upper()]
    result = vehicle_service.collect_vehicle_data(lines=wanted)
    assert result["vehicles"]
    assert {vehicle["line"] for vehicle in result["vehicles"]} == set(wanted)


def test_collect_vehicle_data_refreshes_after_ttl(monkeypatch):
    """Snapshots older than the TTL trigger a new schedule pass."""
    calls = {"count": 0}

    def fake_schedule(line_name: str):
        calls["count"] += 1
        return _canned()

    _patch_schedule(monkeypatch, fake_schedule)

    expected_calls = len(vehicle_service.DEFAULT_PSEUDO_LINES)
    vehicle_service.collect_vehicle_data()
    assert calls["count"] == expected_calls

    cache_key = vehicle_service.vehicle_cache_key(None, None)
    cached_entry = vehicle_service._vehicle_snapshot_cache[cache_key]
    cached_entry["fetched_at"] -= vehicle_service.VEHICLE_CACHE_TTL + 1

    vehicle_service.collect_vehicle_data()
    assert calls["count"] == 2 * expected_calls, "expired snapshot must refresh"
