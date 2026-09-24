"""Unit tests for utility functions."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from mcp_server.utils import find_station_by_name


@pytest.fixture
def mock_data_loader():
    """Local loader with real attribute values (shadows the shared Mock-based one).

    `Mock(name="...")` sets the mock's name, not a `.name` attribute, so the
    shared fixture's stations are unusable for attribute-style access here.
    """
    stations = [
        SimpleNamespace(name="Stephansplatz", rbl="1234", type="metro",
                        zone="100", lat=48.2085, lng=16.3731),
        SimpleNamespace(name="Hauptbahnhof", rbl="5678", type="metro",
                        zone="100", lat=48.1847, lng=16.3786),
        SimpleNamespace(name="Schwedenplatz", rbl="9012", type="metro",
                        zone="100", lat=48.2119, lng=16.3778),
    ]
    loader = Mock()
    loader.load_stations = Mock(return_value=stations)
    return loader


def test_find_station_by_name_exact_match(mock_data_loader):
    """Test finding station by exact name."""
    with patch("mcp_server.utils.data_loader", mock_data_loader):
        result = find_station_by_name("Stephansplatz")

    assert result is not None
    assert result["name"] == "Stephansplatz"


def test_find_station_by_name_partial_match(mock_data_loader):
    """Test finding station by partial name."""
    with patch("mcp_server.utils.data_loader", mock_data_loader):
        result = find_station_by_name("Stephans")

    assert result is not None
    assert "Stephans" in result["name"]


def test_find_station_by_name_case_insensitive(mock_data_loader):
    """Test that station search is case-insensitive."""
    with patch("mcp_server.utils.data_loader", mock_data_loader):
        result_lower = find_station_by_name("stephansplatz")
        result_upper = find_station_by_name("STEPHANSPLATZ")

    assert result_lower is not None
    assert result_upper is not None
    assert result_lower["name"] == result_upper["name"]


def test_find_station_by_name_not_found(mock_data_loader):
    """Test finding non-existent station."""
    with patch("mcp_server.utils.data_loader", mock_data_loader):
        result = find_station_by_name("NonExistentStation")

    assert result is None


def test_find_station_by_name_empty_list():
    """Test finding station in empty list."""
    empty_loader = Mock()
    empty_loader.load_stations = Mock(return_value=[])

    with patch("mcp_server.utils.data_loader", empty_loader):
        result = find_station_by_name("Stephansplatz")

    assert result is None
