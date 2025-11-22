"""Shared test utilities for Wiener Linien project tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class DummyStation:
    """Minimal station representation providing only the attributes tests need."""

    rbl: str


def make_station_list(count: int = 5, base: int = 1000) -> List[DummyStation]:
    """Create a list of dummy stations with four-digit RBL codes."""

    return [DummyStation(f"{base + index}") for index in range(count)]


def build_api_response(
    line_name: str,
    line_type: str,
    *,
    countdown: int = 3,
    latitude: float = 48.2082,
    longitude: float = 16.3738,
) -> dict:
    """Construct a minimal Wiener Linien API response for a single monitor."""

    return {
        'data': {
            'monitors': [
                {
                    'lines': [
                        {
                            'name': line_name,
                            'type': line_type,
                            'departures': {
                                'departure': [
                                    {
                                        'vehicle': {
                                            'towards': 'Central Station',
                                            'platform': '1',
                                            'barrierFree': True,
                                        },
                                        'departureTime': {
                                            'timePlanned': '2024-01-01T00:00:00Z',
                                            'timeReal': '2024-01-01T00:01:00Z',
                                            'countdown': countdown,
                                        },
                                    }
                                ]
                            },
                        }
                    ],
                    'locationStop': {
                        'geometry': {'coordinates': [longitude, latitude]},
                        'properties': {'title': 'Sample Station'},
                    },
                }
            ]
        }
    }

