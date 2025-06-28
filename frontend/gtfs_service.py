"""
GTFS Service for handling GTFS data processing.
"""
import os
import csv
from datetime import datetime, date
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class GTFSDateRange:
    """Represents a date range for GTFS calendar entries."""
    start_date: date
    end_date: date
    days: List[bool]  # [monday, tuesday, ..., sunday]
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
        self.calendar_entries: Dict[str, GTFSDateRange] = {}
        self.trips: List[GTFSTrip] = []
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
        calendar_path = os.path.join(self.gtfs_dir, 'calendar.txt')
        
        try:
            with open(calendar_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        entry = GTFSDateRange(
                            service_id=row['service_id'],
                            start_date=datetime.strptime(row['start_date'], '%Y%m%d').date(),
                            end_date=datetime.strptime(row['end_date'], '%Y%m%d').date(),
                            days=[
                                row['monday'] == '1',
                                row['tuesday'] == '1',
                                row['wednesday'] == '1',
                                row['thursday'] == '1',
                                row['friday'] == '1',
                                row['saturday'] == '1',
                                row['sunday'] == '1',
                            ]
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
        trips_path = os.path.join(self.gtfs_dir, 'trips.txt')
        
        try:
            with open(trips_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        trip = GTFSTrip(
                            trip_id=row['trip_id'],
                            route_id=row['route_id'],
                            service_id=row['service_id'],
                            trip_headsign=row.get('trip_headsign', ''),
                            direction_id=int(row.get('direction_id', 0)),
                            block_id=row.get('block_id', ''),
                            shape_id=row.get('shape_id', '')
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
    
    def get_active_services(self, target_date: Optional[date] = None) -> Set[str]:
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
    
    def get_trips_for_route(self, route_id: str, date_filter: Optional[date] = None) -> List[GTFSTrip]:
        """Get all trips for a specific route, optionally filtered by date."""
        if not self._loaded:
            self.load_data()
            
        if date_filter:
            active_services = self.get_active_services(date_filter)
            return [t for t in self.trips 
                   if t.route_id == route_id and t.service_id in active_services]
        
        return [t for t in self.trips if t.route_id == route_id]
    
    def get_trip_schedule(self, trip_id: str) -> List[Dict]:
        """Get the schedule for a specific trip."""
        if not self._loaded:
            self.load_data()
            
        # TODO: Implement using stop_times.txt
        return []

# Singleton instance
gtfs_service = GTFSService(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'gtfs_data', 'extracted')
)
