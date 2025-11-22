"""
City configuration for GTFS data loading.

This module provides city-specific configurations for loading GTFS data
from different transit agencies around the world.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
from pathlib import Path


@dataclass
class CityConfig:
    """Configuration for a specific city's GTFS feed."""
    name: str
    gtfs_url: str
    timezone: str
    language: str = "en"
    enable_rbl_mapping: bool = False  # Vienna-specific RBL/DIVA mapping
    metadata_sources: Optional[Dict[str, str]] = None  # City-specific metadata URLs
    description: str = ""
    map_center: Optional[Tuple[float, float]] = None  # (lat, lng) for map initialization
    map_zoom: int = 13  # Default zoom level


# Pre-configured cities
CITIES: Dict[str, CityConfig] = {
    "vienna": CityConfig(
        name="Vienna",
        gtfs_url="https://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/gtfs.zip",
        timezone="Europe/Vienna",
        language="de",
        enable_rbl_mapping=True,
        description="Vienna public transport (Wiener Linien) - U-Bahn, trams, buses",
        map_center=(48.2082, 16.3738),
        map_zoom=13
    ),
    "munich": CityConfig(
        name="Munich",
        gtfs_url="https://gtfs.de/en/feeds/de_full/",  # Note: May need specific Munich feed
        timezone="Europe/Berlin",
        language="de",
        enable_rbl_mapping=False,
        description="Munich public transport (MVV) - S-Bahn, U-Bahn, trams, buses"
    ),
    "london": CityConfig(
        name="London",
        gtfs_url="https://storage.googleapis.com/stadtnavi-data/gtfs/gtfs-london.zip",  # Example - verify actual URL
        timezone="Europe/London",
        language="en",
        enable_rbl_mapping=False,
        description="London public transport (TfL) - Tube, buses, trams, DLR"
    ),
    "tokyo": CityConfig(
        name="Tokyo",
        gtfs_url="https://challenge2025.odpt.org/en/opendata.html",  # Note: May need API key/registration
        timezone="Asia/Tokyo",
        language="ja",
        enable_rbl_mapping=False,
        description="Tokyo public transport - JR, Metro, private railways"
    ),
    "berlin": CityConfig(
        name="Berlin",
        gtfs_url="https://gtfs.de/en/feeds/de_full/",  # Note: May need specific Berlin feed
        timezone="Europe/Berlin",
        language="de",
        enable_rbl_mapping=False,
        description="Berlin public transport (BVG) - U-Bahn, S-Bahn, trams, buses"
    ),
    "paris": CityConfig(
        name="Paris",
        gtfs_url="https://data.iledefrance.fr/api/explore/v2.1/catalog/datasets/offre-horaires-tc-gtfs-idfm/exports/gtfs",  # Example - verify actual URL
        timezone="Europe/Paris",
        language="fr",
        enable_rbl_mapping=False,
        description="Paris public transport (RATP/IDFM) - Metro, RER, buses, trams"
    ),
    "newyork": CityConfig(
        name="New York",
        gtfs_url="https://www.nyc.gov/assets/mta/downloads/gtfs/google_transit.zip",
        timezone="America/New_York",
        language="en",
        enable_rbl_mapping=False,
        description="New York public transport (MTA) - Subway, buses",
        map_center=(40.7128, -74.0060),
        map_zoom=13
    ),
    "oebb": CityConfig(
        name="ÖBB (Austria)",
        gtfs_url="https://data.oebb.at/de/datensaetze~soll-fahrplan-gtfs~/download",  # Note: May need to verify exact download URL
        timezone="Europe/Vienna",
        language="de",
        enable_rbl_mapping=False,
        description="Austrian Federal Railways (ÖBB) - National and regional train services covering all of Austria, including Vienna and Lower Austria",
        map_center=(48.2082, 16.3738),  # Centered on Vienna (central Austria)
        map_zoom=10  # Wider zoom to show regional coverage
    ),
}


def get_city_config(city_name: str) -> Optional[CityConfig]:
    """Get configuration for a city by name (case-insensitive)."""
    city_lower = city_name.lower().strip()
    return CITIES.get(city_lower)


def list_cities() -> Dict[str, CityConfig]:
    """List all available city configurations."""
    return CITIES.copy()


def create_custom_config(
    name: str,
    gtfs_url: str,
    timezone: str,
    language: str = "en",
    enable_rbl_mapping: bool = False,
    description: str = "",
    map_center: Optional[Tuple[float, float]] = None,
    map_zoom: int = 13
) -> CityConfig:
    """Create a custom city configuration."""
    return CityConfig(
        name=name,
        gtfs_url=gtfs_url,
        timezone=timezone,
        language=language,
        enable_rbl_mapping=enable_rbl_mapping,
        description=description,
        map_center=map_center,
        map_zoom=map_zoom
    )


def get_gtfs_filename(city_name: str) -> str:
    """Generate a standardized GTFS filename for a city."""
    city_safe = city_name.lower().replace(" ", "-").replace("_", "-")
    return f"{city_safe}-gtfs.zip"

