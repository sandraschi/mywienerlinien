"""
GTFS Service for handling GTFS data processing.
"""

import csv
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[1]

# City ids are used as directory names under cities/ — keep the alphabet tight
# so resolve_data_city can never escape into a traversal.
_CITY_ID_RE = re.compile(r"[a-z0-9][a-z0-9_-]*")


def extracted_dir() -> Path:
    """Legacy Vienna feed directory (the live reader's historic home)."""
    return _REPO_ROOT / "scripts" / "gtfs_data" / "extracted"


def data_cities_root() -> Path:
    """Root of per-city gtfs-mcp exports.

    Override via PUBLICtransport_GTFS_CITIES (deprecated alias
    MYWIENERLINIEN_GTFS_CITIES still honored).
    """
    override = os.environ.get("PUBLICtransport_GTFS_CITIES", "").strip()
    override = override or os.environ.get("MYWIENERLINIEN_GTFS_CITIES", "").strip()
    if override:
        return Path(override).expanduser()
    return _REPO_ROOT / "scripts" / "gtfs_data" / "cities"


def _read_manifest(city_dir: Path) -> dict:
    try:
        return json.loads((city_dir / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def resolve_data_city(city_id: str) -> Path | None:
    """Feed-data directory for a city id, or None when unavailable.

    ``vienna`` is the legacy ``extracted/`` checkout; every other city lives in
    ``cities/<id>/`` with a ``manifest.json`` (the gtfs-mcp export contract).
    """
    cid = (city_id or "").strip().lower()
    if not cid or _CITY_ID_RE.fullmatch(cid) is None:
        return None
    if cid == "vienna":
        cand = extracted_dir()
        if (cand / "calendar.txt").exists() or (cand / "stops.txt").exists():
            return cand
        return None
    cand = data_cities_root() / cid
    if (cand / "manifest.json").is_file():
        return cand
    return None


def list_data_cities() -> list[dict]:
    """Cities with locally available feed data (for the city switcher UI).

    Vienna first when its legacy checkout has data, then every cities/<id>/
    carrying a manifest.json, enriched with that manifest's counts/export time.
    An index.json (written by gtfs-mcp exports) is honoured when present but a
    manifest on disk is sufficient — never trust the index alone.
    """
    found: list[dict] = []
    vienna = resolve_data_city("vienna")
    if vienna is not None:
        found.append({"id": "vienna", "dir": str(vienna), "source": "extracted-legacy"})
    root = data_cities_root()
    try:
        names = sorted(p.name for p in root.iterdir() if p.is_dir())
    except OSError:
        names = []
    for name in names:
        if name == "vienna":
            continue
        city_dir = resolve_data_city(name)
        if city_dir is None:
            continue
        manifest = _read_manifest(city_dir)
        found.append(
            {
                "id": name,
                "dir": str(city_dir),
                "source": "gtfs-mcp-export",
                "exported_at": manifest.get("exported_at"),
                "counts": manifest.get("counts", {}),
            }
        )
    return found


@dataclass
class GTFSDateRange:
    """Represents a date range for GTFS calendar entries."""

    start_date: date
    end_date: date
    days: list[bool]  # [monday, tuesday, ..., sunday]
    service_id: str


@dataclass
class GTFSTrip:
    """Represents a GTFS trip."""

    trip_id: str
    route_id: str
    service_id: str
    trip_headsign: str
    direction_id: int
    block_id: str
    shape_id: str


class GTFSService:
    """Service for handling GTFS data processing."""

    def __init__(self, gtfs_dir: str):
        """Initialize with path to extracted GTFS directory."""
        self.gtfs_dir = gtfs_dir
        self.calendar_entries: dict[str, GTFSDateRange] = {}
        self.trips: list[GTFSTrip] = []
        self._loaded = False

    def load_data(self) -> None:
        """Load all GTFS data into memory."""
        if self._loaded:
            return

        logger.info("Loading GTFS data...")
        self._load_calendar()
        self._load_trips()
        self._loaded = True
        logger.info(f"GTFS data loaded: {len(self.calendar_entries)} calendar entries, {len(self.trips)} trips")

    def _load_calendar(self) -> None:
        """Load calendar.txt data."""
        calendar_path = os.path.join(self.gtfs_dir, "calendar.txt")

        try:
            with open(calendar_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        entry = GTFSDateRange(
                            service_id=row["service_id"],
                            start_date=datetime.strptime(row["start_date"], "%Y%m%d").date(),
                            end_date=datetime.strptime(row["end_date"], "%Y%m%d").date(),
                            days=[
                                row["monday"] == "1",
                                row["tuesday"] == "1",
                                row["wednesday"] == "1",
                                row["thursday"] == "1",
                                row["friday"] == "1",
                                row["saturday"] == "1",
                                row["sunday"] == "1",
                            ],
                        )
                        self.calendar_entries[entry.service_id] = entry
                    except (KeyError, ValueError) as e:
                        logger.warning(f"Invalid calendar entry: {row}. Error: {e}")
                        continue

            logger.info(f"Loaded {len(self.calendar_entries)} calendar entries")

        except FileNotFoundError:
            logger.warning(f"calendar.txt not found in {self.gtfs_dir}")
        except Exception as e:
            logger.error(f"Error loading calendar data: {e}")

    def _load_trips(self) -> None:
        """Load trips.txt data."""
        trips_path = os.path.join(self.gtfs_dir, "trips.txt")

        try:
            with open(trips_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        trip = GTFSTrip(
                            trip_id=row["trip_id"],
                            route_id=row["route_id"],
                            service_id=row["service_id"],
                            trip_headsign=row.get("trip_headsign", ""),
                            direction_id=int(row.get("direction_id", 0)),
                            block_id=row.get("block_id", ""),
                            shape_id=row.get("shape_id", ""),
                        )
                        self.trips.append(trip)
                    except (KeyError, ValueError) as e:
                        logger.warning(f"Invalid trip entry: {row}. Error: {e}")
                        continue

            logger.info(f"Loaded {len(self.trips)} trips")

        except FileNotFoundError:
            logger.warning(f"trips.txt not found in {self.gtfs_dir}")
        except Exception as e:
            logger.error(f"Error loading trips data: {e}")

    def get_active_services(self, target_date: date | None = None) -> set[str]:
        """Get set of service_ids that are active on the given date."""
        if not self._loaded:
            self.load_data()

        target = target_date or date.today()
        weekday = target.weekday()  # 0 = Monday, 6 = Sunday

        active_services = set()

        for service_id, entry in self.calendar_entries.items():
            if entry.start_date <= target <= entry.end_date and entry.days[weekday]:
                active_services.add(service_id)

        # TODO: Apply calendar_dates.txt exceptions

        return active_services

    def get_trips_for_route(self, route_id: str, date_filter: date | None = None) -> list[GTFSTrip]:
        """Get all trips for a specific route, optionally filtered by date."""
        if not self._loaded:
            self.load_data()

        if date_filter:
            active_services = self.get_active_services(date_filter)
            return [t for t in self.trips if t.route_id == route_id and t.service_id in active_services]

        return [t for t in self.trips if t.route_id == route_id]

    def get_trip_schedule(self, trip_id: str) -> list[dict]:
        """Get the schedule for a specific trip."""
        if not self._loaded:
            self.load_data()

        # TODO: Implement using stop_times.txt
        return []


# Singleton instance
gtfs_service = GTFSService(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "gtfs_data", "extracted")
)
