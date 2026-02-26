"""
Journey planning and routing service for Vienna public transport.
Implements GTFS-based routing with multi-leg journey support.

Phase 3A: Basic GTFS routing with single transfers
Phase 3B: A* pathfinding with real-time delays and walking connections
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    from .graph_service import AStarRouter, TransitGraph
except ImportError:
    from graph_service import AStarRouter, TransitGraph

logger = logging.getLogger(__name__)


@dataclass
class RouteSegment:
    """A segment of a route between two stops."""

    line: str
    from_stop_id: str
    from_stop_name: str
    to_stop_id: str
    to_stop_name: str
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    vehicle_type: str
    distance_meters: float | None = None


@dataclass
class RouteOption:
    """A complete route option with all segments."""

    segments: list[RouteSegment]
    total_duration_minutes: int
    transfers: int
    total_distance_meters: float
    departure_time: datetime
    arrival_time: datetime
    estimated_cost: str


class JourneyPlanner:
    """Journey planning service using GTFS data.

    Phase 3A: Basic routing with simple transfers
    Phase 3B: A* pathfinding with advanced features
    """

    # Route type mapping to vehicle type names
    ROUTE_TYPE_MAP = {
        0: "tram",
        1: "metro",
        2: "rail",
        3: "bus",
        4: "ferry",
        5: "cable_tram",
        6: "aerial",
        7: "funicular",
        11: "trolleybus",
        12: "monorail",
        800: "bus",
    }

    # Average speeds for different vehicle types (km/h)
    AVERAGE_SPEEDS = {"metro": 35, "tram": 20, "bus": 18, "rail": 40}

    # Transfer time in minutes
    DEFAULT_TRANSFER_TIME = 5

    def __init__(self, db_manager, use_astar: bool = True):
        """Initialize journey planner with database manager.

        Args:
            db_manager: Database manager instance
            use_astar: Use A* pathfinding (Phase 3B) vs. simple routing (Phase 3A)
        """
        self.db = db_manager
        self.use_astar = use_astar
        self.graph = None
        self.astar_router = None

        # Initialize graph for A* routing if enabled
        if use_astar:
            try:
                self.graph = TransitGraph(db_manager)
                self.graph.build_graph(include_walking=True)
                self.astar_router = AStarRouter(self.graph)
                logger.info("A* routing enabled with graph pathfinding")
            except Exception as e:
                logger.warning(
                    f"Failed to build graph for A*: {e}. Falling back to simple routing."
                )
                self.use_astar = False

    def calculate_haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points using haversine formula.

        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point

        Returns:
            Distance in meters
        """
        radius_earth = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return radius_earth * c

    def find_direct_routes(
        self, from_stop_id: str, to_stop_id: str, departure_time: datetime | None = None
    ) -> list[RouteSegment]:
        """Find direct routes between two stops (no transfers).

        Args:
            from_stop_id: Origin stop ID
            to_stop_id: Destination stop ID
            departure_time: Desired departure time

        Returns:
            List of route segments for direct connections
        """
        if departure_time is None:
            departure_time = datetime.now()

        # Query to find all routes that connect both stops
        query = """
        WITH common_routes AS (
            SELECT DISTINCT
                r.route_id,
                r.route_short_name,
                r.route_type,
                t.trip_id,
                t.direction_id
            FROM routes r
            JOIN trips t ON r.route_id = t.route_id
            JOIN stop_times st1 ON t.trip_id = st1.trip_id
            JOIN stop_times st2 ON t.trip_id = st2.trip_id
            WHERE st1.stop_id = :from_stop_id
              AND st2.stop_id = :to_stop_id
              AND st1.stop_sequence < st2.stop_sequence
        ),
        route_details AS (
            SELECT
                cr.route_short_name,
                cr.route_type,
                s1.stop_name as from_stop_name,
                s2.stop_name as to_stop_name,
                s1.stop_lat as from_lat,
                s1.stop_lon as from_lon,
                s2.stop_lat as to_lat,
                s2.stop_lon as to_lon,
                MIN(st2.stop_sequence - st1.stop_sequence) as stop_count
            FROM common_routes cr
            JOIN stop_times st1 ON cr.trip_id = st1.trip_id
            JOIN stop_times st2 ON cr.trip_id = st2.trip_id
            JOIN stops s1 ON st1.stop_id = s1.stop_id
            JOIN stops s2 ON st2.stop_id = s2.stop_id
            WHERE st1.stop_id = :from_stop_id
              AND st2.stop_id = :to_stop_id
              AND st1.stop_sequence < st2.stop_sequence
            GROUP BY
                cr.route_short_name,
                cr.route_type,
                s1.stop_name,
                s2.stop_name,
                s1.stop_lat,
                s1.stop_lon,
                s2.stop_lat,
                s2.stop_lon
        )
        SELECT * FROM route_details
        ORDER BY stop_count
        LIMIT 5
        """

        try:
            results = self.db.execute_query(
                query, {"from_stop_id": from_stop_id, "to_stop_id": to_stop_id}
            )

            segments = []
            for row in results:
                # Calculate distance
                distance = self.calculate_haversine_distance(
                    row["from_lat"], row["from_lon"], row["to_lat"], row["to_lon"]
                )

                # Estimate travel time based on vehicle type and distance
                vehicle_type = self.ROUTE_TYPE_MAP.get(row["route_type"], "bus")
                avg_speed_kmh = self.AVERAGE_SPEEDS.get(vehicle_type, 20)
                duration_minutes = max(3, int((distance / 1000) / avg_speed_kmh * 60))

                arrival_time = departure_time + timedelta(minutes=duration_minutes)

                segment = RouteSegment(
                    line=row["route_short_name"],
                    from_stop_id=from_stop_id,
                    from_stop_name=row["from_stop_name"],
                    to_stop_id=to_stop_id,
                    to_stop_name=row["to_stop_name"],
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    duration_minutes=duration_minutes,
                    vehicle_type=vehicle_type,
                    distance_meters=distance,
                )
                segments.append(segment)

            return segments

        except Exception as e:
            logger.error(f"Error finding direct routes: {e}", exc_info=True)
            return []

    def find_transfer_routes(
        self,
        from_stop_id: str,
        to_stop_id: str,
        departure_time: datetime | None = None,
        max_transfers: int = 2,
    ) -> list[list[RouteSegment]]:
        """Find routes with transfers between two stops.

        Args:
            from_stop_id: Origin stop ID
            to_stop_id: Destination stop ID
            departure_time: Desired departure time
            max_transfers: Maximum number of transfers allowed

        Returns:
            List of route options, each containing multiple segments
        """
        if departure_time is None:
            departure_time = datetime.now()

        # For now, implement single-transfer routing
        # Future: Implement proper graph traversal (Dijkstra/A*)

        # Find intermediate stops that connect both endpoints
        query = """
        WITH origin_routes AS (
            SELECT DISTINCT
                r.route_short_name as route1,
                r.route_type as type1,
                st.stop_id as transfer_stop,
                s.stop_name as transfer_name,
                s.stop_lat,
                s.stop_lon
            FROM routes r
            JOIN trips t ON r.route_id = t.route_id
            JOIN stop_times st1 ON t.trip_id = st1.trip_id
            JOIN stop_times st ON t.trip_id = st.trip_id
            JOIN stops s ON st.stop_id = s.stop_id
            WHERE st1.stop_id = :from_stop_id
              AND st.stop_sequence > st1.stop_sequence
              AND st.stop_id != :from_stop_id
              AND st.stop_id != :to_stop_id
        ),
        destination_routes AS (
            SELECT DISTINCT
                r.route_short_name as route2,
                r.route_type as type2,
                st.stop_id as transfer_stop
            FROM routes r
            JOIN trips t ON r.route_id = t.route_id
            JOIN stop_times st1 ON t.trip_id = st1.trip_id
            JOIN stop_times st ON t.trip_id = st.trip_id
            WHERE st1.stop_id = :to_stop_id
              AND st.stop_sequence < st1.stop_sequence
              AND st.stop_id != :from_stop_id
              AND st.stop_id != :to_stop_id
        )
        SELECT
            or1.route1,
            or1.type1,
            or1.transfer_stop,
            or1.transfer_name,
            or1.stop_lat,
            or1.stop_lon,
            dr.route2,
            dr.type2
        FROM origin_routes or1
        JOIN destination_routes dr ON or1.transfer_stop = dr.transfer_stop
        LIMIT 10
        """

        try:
            results = self.db.execute_query(
                query, {"from_stop_id": from_stop_id, "to_stop_id": to_stop_id}
            )

            # Get origin and destination stop info
            origin_info = self._get_stop_info(from_stop_id)
            dest_info = self._get_stop_info(to_stop_id)

            if not origin_info or not dest_info:
                return []

            route_options = []
            for row in results:
                # Create first segment
                transfer_stop = row["transfer_stop"]

                # Calculate first leg
                dist1 = self.calculate_haversine_distance(
                    origin_info["stop_lat"],
                    origin_info["stop_lon"],
                    row["stop_lat"],
                    row["stop_lon"],
                )
                vehicle_type1 = self.ROUTE_TYPE_MAP.get(row["type1"], "bus")
                duration1 = max(
                    3, int((dist1 / 1000) / self.AVERAGE_SPEEDS.get(vehicle_type1, 20) * 60)
                )

                # Calculate second leg
                dist2 = self.calculate_haversine_distance(
                    row["stop_lat"], row["stop_lon"], dest_info["stop_lat"], dest_info["stop_lon"]
                )
                vehicle_type2 = self.ROUTE_TYPE_MAP.get(row["type2"], "bus")
                duration2 = max(
                    3, int((dist2 / 1000) / self.AVERAGE_SPEEDS.get(vehicle_type2, 20) * 60)
                )

                # Create segments with transfer time
                seg1_start = departure_time
                seg1_end = seg1_start + timedelta(minutes=duration1)
                seg2_start = seg1_end + timedelta(minutes=self.DEFAULT_TRANSFER_TIME)
                seg2_end = seg2_start + timedelta(minutes=duration2)

                segment1 = RouteSegment(
                    line=row["route1"],
                    from_stop_id=from_stop_id,
                    from_stop_name=origin_info["stop_name"],
                    to_stop_id=transfer_stop,
                    to_stop_name=row["transfer_name"],
                    departure_time=seg1_start,
                    arrival_time=seg1_end,
                    duration_minutes=duration1,
                    vehicle_type=vehicle_type1,
                    distance_meters=dist1,
                )

                segment2 = RouteSegment(
                    line=row["route2"],
                    from_stop_id=transfer_stop,
                    from_stop_name=row["transfer_name"],
                    to_stop_id=to_stop_id,
                    to_stop_name=dest_info["stop_name"],
                    departure_time=seg2_start,
                    arrival_time=seg2_end,
                    duration_minutes=duration2,
                    vehicle_type=vehicle_type2,
                    distance_meters=dist2,
                )

                route_options.append([segment1, segment2])

            return route_options[:3]  # Return top 3 options

        except Exception as e:
            logger.error(f"Error finding transfer routes: {e}", exc_info=True)
            return []

    def _get_stop_info(self, stop_id: str) -> dict | None:
        """Get stop information from database."""
        query = """
        SELECT stop_id, stop_name, stop_lat, stop_lon
        FROM stops
        WHERE stop_id = :stop_id
        LIMIT 1
        """
        results = self.db.execute_query(query, {"stop_id": stop_id})
        return results[0] if results else None

    def plan_journey(
        self,
        from_stop_id: str,
        to_stop_id: str,
        departure_time: datetime | None = None,
        num_alternatives: int = 3,
    ) -> list[RouteOption]:
        """Plan complete journey with multiple route options.

        Phase 3A: Simple routing with direct + single transfer
        Phase 3B: A* pathfinding with walking connections and multiple transfers

        Args:
            from_stop_id: Origin stop ID
            to_stop_id: Destination stop ID
            departure_time: Desired departure time
            num_alternatives: Number of alternative routes to find

        Returns:
            List of route options sorted by duration
        """
        if departure_time is None:
            departure_time = datetime.now()

        # Phase 3B: Use A* pathfinding if available
        if self.use_astar and self.astar_router:
            return self._plan_journey_astar(
                from_stop_id, to_stop_id, departure_time, num_alternatives
            )

        # Phase 3A: Fallback to simple routing
        return self._plan_journey_simple(from_stop_id, to_stop_id, departure_time)

    def _plan_journey_astar(
        self, from_stop_id: str, to_stop_id: str, departure_time: datetime, num_alternatives: int
    ) -> list[RouteOption]:
        """Plan journey using A* pathfinding (Phase 3B).

        Args:
            from_stop_id: Origin stop ID
            to_stop_id: Destination stop ID
            departure_time: Departure time
            num_alternatives: Number of alternatives to find

        Returns:
            List of route options
        """
        try:
            # Find multiple alternative routes using A*
            paths = self.astar_router.find_multiple_routes(
                from_stop_id,
                to_stop_id,
                num_routes=num_alternatives,
                max_transfers=3,  # Allow up to 3 transfers
                departure_time=departure_time,
            )

            if not paths:
                logger.warning(f"A* found no paths from {from_stop_id} to {to_stop_id}")
                return []

            # Convert graph edges to route options
            options = []
            for path in paths:
                segments = []
                current_time = departure_time

                for edge in path:
                    # Get stop names from graph
                    from_node = self.graph.get_node(edge.from_stop_id)
                    to_node = self.graph.get_node(edge.to_stop_id)

                    arrival_time = current_time + timedelta(minutes=edge.duration_minutes)

                    segment = RouteSegment(
                        line=edge.line,
                        from_stop_id=edge.from_stop_id,
                        from_stop_name=from_node.stop_name if from_node else edge.from_stop_id,
                        to_stop_id=edge.to_stop_id,
                        to_stop_name=to_node.stop_name if to_node else edge.to_stop_id,
                        departure_time=current_time,
                        arrival_time=arrival_time,
                        duration_minutes=int(edge.duration_minutes),
                        vehicle_type=edge.vehicle_type,
                        distance_meters=edge.distance_meters,
                    )
                    segments.append(segment)

                    # Add transfer time if next edge is different line
                    current_time = arrival_time
                    if len(path) > 1:
                        idx = path.index(edge)
                        if idx < len(path) - 1:
                            next_edge = path[idx + 1]
                            if edge.line != next_edge.line and not next_edge.is_walking:
                                current_time += timedelta(minutes=self.DEFAULT_TRANSFER_TIME)

                # Count non-walking transfers
                transfers = sum(
                    1
                    for i in range(len(path) - 1)
                    if path[i].line != path[i + 1].line and not path[i + 1].is_walking
                )

                total_duration = sum(seg.duration_minutes for seg in segments) + (
                    transfers * self.DEFAULT_TRANSFER_TIME
                )
                total_distance = sum(seg.distance_meters or 0 for seg in segments)

                option = RouteOption(
                    segments=segments,
                    total_duration_minutes=total_duration,
                    transfers=transfers,
                    total_distance_meters=total_distance,
                    departure_time=departure_time,
                    arrival_time=segments[-1].arrival_time if segments else departure_time,
                    estimated_cost="€2.40",
                )
                options.append(option)

            logger.info(f"A* found {len(options)} route options")
            return options

        except Exception as e:
            logger.error(f"A* routing failed: {e}", exc_info=True)
            # Fallback to simple routing
            return self._plan_journey_simple(from_stop_id, to_stop_id, departure_time)

    def _plan_journey_simple(
        self, from_stop_id: str, to_stop_id: str, departure_time: datetime
    ) -> list[RouteOption]:
        """Plan journey using simple routing (Phase 3A fallback).

        Args:
            from_stop_id: Origin stop ID
            to_stop_id: Destination stop ID
            departure_time: Departure time

        Returns:
            List of route options
        """
        all_options = []

        # Try direct routes first
        direct_segments = self.find_direct_routes(from_stop_id, to_stop_id, departure_time)
        for segment in direct_segments:
            option = RouteOption(
                segments=[segment],
                total_duration_minutes=segment.duration_minutes,
                transfers=0,
                total_distance_meters=segment.distance_meters or 0,
                departure_time=segment.departure_time,
                arrival_time=segment.arrival_time,
                estimated_cost="€2.40",  # Standard Vienna fare
            )
            all_options.append(option)

        # Try routes with one transfer
        transfer_routes = self.find_transfer_routes(
            from_stop_id, to_stop_id, departure_time, max_transfers=1
        )
        for segments in transfer_routes:
            total_duration = (
                sum(seg.duration_minutes for seg in segments)
                + (len(segments) - 1) * self.DEFAULT_TRANSFER_TIME
            )
            total_distance = sum(seg.distance_meters or 0 for seg in segments)

            option = RouteOption(
                segments=segments,
                total_duration_minutes=total_duration,
                transfers=len(segments) - 1,
                total_distance_meters=total_distance,
                departure_time=segments[0].departure_time,
                arrival_time=segments[-1].arrival_time,
                estimated_cost="€2.40",  # Standard Vienna fare (same for transfers)
            )
            all_options.append(option)

        # Sort by duration (fastest first)
        all_options.sort(key=lambda x: x.total_duration_minutes)

        return all_options[:5]  # Return top 5 options
