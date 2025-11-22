"""Tests for vehicle data caching and throttling logic."""

from __future__ import annotations

import types

import pytest

from tests.utils import build_api_response, make_station_list
from frontend import vehicle_service


@pytest.fixture(autouse=True)
def reset_cache(app_module, monkeypatch):
    """Ensure each test starts with a clean cache and consistent fixtures."""

    monkeypatch.setattr(vehicle_service, 'data_loader', app_module.data_loader)
    monkeypatch.setattr(vehicle_service.data_loader, 'load_stations', lambda: make_station_list())
    monkeypatch.setattr(vehicle_service, 'db', types.SimpleNamespace(get_line_stations=lambda line: []))
    monkeypatch.setattr(vehicle_service, '_vehicle_snapshot_cache', {})
    vehicle_service.clear_vehicle_cache()
    yield
    vehicle_service.clear_vehicle_cache()


def test_collect_vehicle_data_uses_cache(app_module, monkeypatch):
    """Subsequent calls within 30 seconds reuse cached API data."""

    call_counter = {'count': 0}

    def fake_fetch(rbl: str):
        call_counter['count'] += 1
        return build_api_response(f'U1-{rbl}', 'ptSubway')

    monkeypatch.setattr(vehicle_service, 'fetch_vehicle_data', fake_fetch)

    first = vehicle_service.collect_vehicle_data()
    assert call_counter['count'] == 5
    assert first['vehicles']

    second = vehicle_service.collect_vehicle_data()
    assert call_counter['count'] == 5, "API should not be called within cache TTL"
    assert second['vehicles'] == first['vehicles']


def test_collect_vehicle_data_filters_by_type(app_module, monkeypatch):
    """Vehicle type filtering is applied after caching."""

    def fake_fetch(rbl: str):
        line_type = 'ptBus' if int(rbl) % 2 == 0 else 'ptTram'
        return build_api_response('Line', line_type)

    monkeypatch.setattr(vehicle_service, 'fetch_vehicle_data', fake_fetch)

    result = vehicle_service.collect_vehicle_data(vehicle_type='bus')
    assert result['vehicles']
    assert all(vehicle['type'] == 'bus' for vehicle in result['vehicles'])


def test_collect_vehicle_data_filters_by_lines(app_module, monkeypatch):
    """Filtering by multiple lines should include only requested lines."""

    mapping = {
        '1000': ('U1', 'ptSubway'),
        '1001': ('U2', 'ptSubway'),
        '1002': ('11A', 'ptBus'),
        '1003': ('U1', 'ptSubway'),
        '1004': ('11A', 'ptBus'),
    }

    def fake_fetch(rbl: str):
        line_name, line_type = mapping.get(rbl, ('U3', 'ptSubway'))
        return build_api_response(line_name, line_type)

    monkeypatch.setattr(vehicle_service, 'fetch_vehicle_data', fake_fetch)
    monkeypatch.setattr(
        vehicle_service,
        'db',
        types.SimpleNamespace(
            get_line_stations=lambda name: [
                {'rbl': code}
                for code, (line, _type) in mapping.items()
                if line.upper() == name.upper()
            ]
        ),
    )

    result = vehicle_service.collect_vehicle_data(lines=['u1', 'U2'])
    assert result['vehicles']
    assert {vehicle['line'] for vehicle in result['vehicles']} == {'U1', 'U2'}


def test_collect_vehicle_data_refreshes_after_ttl(app_module, monkeypatch):
    """Cache entries older than the TTL trigger new API calls."""

    call_counter = {'count': 0}

    def fake_fetch(rbl: str):
        call_counter['count'] += 1
        return build_api_response('U2', 'ptSubway')

    monkeypatch.setattr(vehicle_service, 'fetch_vehicle_data', fake_fetch)

    # First call populates cache.
    vehicle_service.collect_vehicle_data()
    assert call_counter['count'] == 5

    cache_key = vehicle_service.vehicle_cache_key(None, None)
    cached_entry = vehicle_service._vehicle_snapshot_cache[cache_key]
    cached_entry['fetched_at'] -= vehicle_service.VEHICLE_CACHE_TTL + 1

    vehicle_service.collect_vehicle_data()
    assert call_counter['count'] == 10, "Expired cache should trigger new API calls"

