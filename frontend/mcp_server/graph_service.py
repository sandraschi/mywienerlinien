"""
Graph-based routing service for Vienna public transport.
Phase 3B Enhancement: A* pathfinding with real-time delay integration.

This module builds a graph representation of the Vienna transit network
and implements A* pathfinding for optimal multi-transfer routing.
"""

import heapq
import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class TransitNode:
    """A node in the transit graph (station)."""

    stop_id: str
    stop_name: str
    lat: float
    lon: float
    zone_id: Optional[str] = None
    wheelchair_accessible: bool = False


@dataclass
class TransitEdge:
    """An edge in the transit graph (connection between stations)."""

    from_stop_id: str
    to_stop_id: str
    line: str
    route_type: int
    duration_minutes: float
    distance_meters: float
    vehicle_type: str
    direction_id: int = 0
    is_walking: bool = False


@dataclass
class SearchNode:
    """A* search node with priority queue support."""

    stop_id: str
    g_cost: float  # Actual cost from start
    h_cost: float  # Heuristic cost to goal
    f_cost: float = field(init=False)  # Total cost (g + h)
    parent: Optional["SearchNode"] = None
    edge_used: Optional[TransitEdge] = None
    arrival_time: Optional[datetime] = None

    def __post_init__(self):
        self.f_cost = self.g_cost + self.h_cost

    def __lt__(self, other):
        return self.f_cost < other.f_cost


class TransitGraph:
    """Graph representation of Vienna public transport network."""

    # Maximum walking distance in meters
    MAX_WALKING_DISTANCE = 500
    # Walking speed in m/s (average 5 km/h)
    WALKING_SPEED_MPS = 1.4
    # Transfer penalty in minutes
    TRANSFER_PENALTY = 5
    # Route type preferences (lower is better)
    ROUTE_TYPE_PREFERENCE = {
        1: 1.0,  # Metro (best)
        0: 1.1,  # Tram
        3: 1.2,  # Bus
        800: 1.2,  # Bus alternative code
        2: 1.0,  # Rail
        7: 1.3,  # Funicular
    }

    def __init__(self, db_manager):
        """Initialize transit graph with database connection."""
        self.db = db_manager
        self.nodes: dict[str, TransitNode] = {}
        self.edges: dict[str, list[TransitEdge]] = defaultdict(list)
        self.built = False

    def build_graph(self, include_walking: bool = True):
        """Build the transit graph from GTFS data.

        Args:
            include_walking: Whether to include walking connections
        """
        logger.info("Building transit graph from GTFS data...")

        # Load all stops as nodes
        self._load_nodes()

        # Load all connections as edges
        self._load_edges()

        # Add walking connections between nearby stops
        if include_walking:
            self._add_walking_connections()

        self.built = True
        logger.info(
            f"Graph built: {len(self.nodes)} nodes, {sum(len(e) for e in self.edges.values())} edges"
        )

    def _load_nodes(self):
        """Load all stops as graph nodes."""
        query = """
        SELECT
            stop_id,
            stop_name,
            stop_lat,
            stop_lon,
            zone_id,
            CASE WHEN wheelchair_boarding = 1 THEN true ELSE false END as wheelchair_accessible
        FROM stops
        WHERE location_type = 1 OR parent_station IS NULL OR parent_station = ''
        """

        try:
            results = self.db.execute_query(query)
            for row in results:
                node = TransitNode(
                    stop_id=row["stop_id"],
                    stop_name=row["stop_name"],
                    lat=float(row["stop_lat"]),
                    lon=float(row["stop_lon"]),
                    zone_id=row.get("zone_id"),
                    wheelchair_accessible=row.get("wheelchair_accessible", False),
                )
                self.nodes[node.stop_id] = node

            logger.info(f"Loaded {len(self.nodes)} nodes")
        except Exception as e:
            logger.error(f"Error loading nodes: {e}", exc_info=True)

    def _load_edges(self):
        """Load all transit connections as graph edges."""
        query = """
        SELECT DISTINCT
            st1.stop_id as from_stop_id,
            st2.stop_id as to_stop_id,
            r.route_short_name as line,
            r.route_type,
            t.direction_id,
            s1.stop_lat as from_lat,
            s1.stop_lon as from_lon,
            s2.stop_lat as to_lat,
            s2.stop_lon as to_lon
        FROM stop_times st1
        JOIN stop_times st2 ON st1.trip_id = st2.trip_id
        JOIN trips t ON st1.trip_id = t.trip_id
        JOIN routes r ON t.route_id = r.route_id
        JOIN stops s1 ON st1.stop_id = s1.stop_id
        JOIN stops s2 ON st2.stop_id = s2.stop_id
        WHERE st2.stop_sequence = st1.stop_sequence + 1
        """

        # Route type to vehicle type mapping
        route_type_map = {0: "tram", 1: "metro", 2: "rail", 3: "bus", 7: "funicular", 800: "bus"}

        # Vehicle type speeds (m/s)
        speeds = {
            "metro": 9.7,  # 35 km/h
            "tram": 5.6,  # 20 km/h
            "bus": 5.0,  # 18 km/h
            "rail": 11.1,  # 40 km/h
            "funicular": 3.0,
        }

        try:
            results = self.db.execute_query(query)
            for row in results:
                # Calculate distance
                distance = self._haversine(
                    row["from_lat"], row["from_lon"], row["to_lat"], row["to_lon"]
                )

                # Calculate duration based on vehicle type
                vehicle_type = route_type_map.get(row["route_type"], "bus")
                speed_mps = speeds.get(vehicle_type, 5.0)
                duration_minutes = max(1.0, (distance / speed_mps) / 60)

                edge = TransitEdge(
                    from_stop_id=row["from_stop_id"],
                    to_stop_id=row["to_stop_id"],
                    line=row["line"],
                    route_type=row["route_type"],
                    duration_minutes=duration_minutes,
                    distance_meters=distance,
                    vehicle_type=vehicle_type,
                    direction_id=row["direction_id"],
                    is_walking=False,
                )

                self.edges[edge.from_stop_id].append(edge)

            logger.info(f"Loaded {sum(len(e) for e in self.edges.values())} edges")
        except Exception as e:
            logger.error(f"Error loading edges: {e}", exc_info=True)

    def _add_walking_connections(self):
        """Add walking connections between nearby stops."""
        logger.info("Adding walking connections...")

        walking_count = 0
        node_list = list(self.nodes.values())

        for i, node1 in enumerate(node_list):
            for node2 in node_list[i + 1 :]:
                distance = self._haversine(node1.lat, node1.lon, node2.lat, node2.lon)

                if distance <= self.MAX_WALKING_DISTANCE:
                    # Calculate walking time
                    duration_minutes = (distance / self.WALKING_SPEED_MPS) / 60

                    # Add bidirectional walking edges
                    edge1 = TransitEdge(
                        from_stop_id=node1.stop_id,
                        to_stop_id=node2.stop_id,
                        line="WALK",
                        route_type=-1,
                        duration_minutes=duration_minutes,
                        distance_meters=distance,
                        vehicle_type="walk",
                        is_walking=True,
                    )
                    edge2 = TransitEdge(
                        from_stop_id=node2.stop_id,
                        to_stop_id=node1.stop_id,
                        line="WALK",
                        route_type=-1,
                        duration_minutes=duration_minutes,
                        distance_meters=distance,
                        vehicle_type="walk",
                        is_walking=True,
                    )

                    self.edges[node1.stop_id].append(edge1)
                    self.edges[node2.stop_id].append(edge2)
                    walking_count += 2

        logger.info(f"Added {walking_count} walking connections")

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate haversine distance between two points."""
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

    def get_neighbors(self, stop_id: str) -> list[TransitEdge]:
        """Get all outgoing edges from a stop."""
        return self.edges.get(stop_id, [])

    def get_node(self, stop_id: str) -> Optional[TransitNode]:
        """Get node information for a stop."""
        return self.nodes.get(stop_id)

    def heuristic(self, from_stop_id: str, to_stop_id: str) -> float:
        """Calculate heuristic cost (estimated time) between stops.

        Uses straight-line distance and metro speed as optimistic estimate.

        Args:
            from_stop_id: Origin stop ID
            to_stop_id: Destination stop ID

        Returns:
            Estimated time in minutes
        """
        from_node = self.nodes.get(from_stop_id)
        to_node = self.nodes.get(to_stop_id)

        if not from_node or not to_node:
            return 0.0

        # Straight-line distance
        distance = self._haversine(from_node.lat, from_node.lon, to_node.lat, to_node.lon)

        # Estimate time using metro speed (optimistic)
        metro_speed_mps = 9.7  # 35 km/h
        estimated_minutes = (distance / metro_speed_mps) / 60

        return estimated_minutes


class AStarRouter:
    """A* pathfinding router for transit network."""

    def __init__(self, graph: TransitGraph):
        """Initialize router with transit graph."""
        self.graph = graph

    def find_path(
        self,
        from_stop_id: str,
        to_stop_id: str,
        max_transfers: int = 3,
        departure_time: Optional[datetime] = None,
    ) -> Optional[list[TransitEdge]]:
        """Find optimal path using A* algorithm.

        Args:
            from_stop_id: Origin stop ID
            to_stop_id: Destination stop ID
            max_transfers: Maximum number of transfers allowed
            departure_time: Desired departure time

        Returns:
            List of transit edges forming the path, or None if no path found
        """
        if not self.graph.built:
            logger.error("Graph not built yet")
            return None

        if departure_time is None:
            departure_time = datetime.now()

        # Check if both nodes exist
        if from_stop_id not in self.graph.nodes or to_stop_id not in self.graph.nodes:
            logger.warning(f"Start or end node not in graph: {from_stop_id}, {to_stop_id}")
            return None

        # Initialize A* data structures
        open_set = []
        closed_set: set[str] = set()

        # Start node
        start_node = SearchNode(
            stop_id=from_stop_id,
            g_cost=0.0,
            h_cost=self.graph.heuristic(from_stop_id, to_stop_id),
            arrival_time=departure_time,
        )

        heapq.heappush(open_set, start_node)
        best_nodes: dict[str, SearchNode] = {from_stop_id: start_node}

        while open_set:
            current = heapq.heappop(open_set)

            # Goal reached
            if current.stop_id == to_stop_id:
                return self._reconstruct_path(current)

            # Already processed
            if current.stop_id in closed_set:
                continue

            closed_set.add(current.stop_id)

            # Count transfers in current path
            transfers = self._count_transfers(current)
            if transfers > max_transfers:
                continue

            # Explore neighbors
            for edge in self.graph.get_neighbors(current.stop_id):
                neighbor_id = edge.to_stop_id

                # Skip if already processed
                if neighbor_id in closed_set:
                    continue

                # Calculate costs
                new_g_cost = current.g_cost + edge.duration_minutes

                # Add transfer penalty if switching lines
                if current.edge_used and not edge.is_walking:
                    if current.edge_used.line != edge.line and not current.edge_used.is_walking:
                        new_g_cost += self.graph.TRANSFER_PENALTY

                # Apply route type preference
                route_pref = self.graph.ROUTE_TYPE_PREFERENCE.get(edge.route_type, 1.2)
                new_g_cost *= route_pref

                # Check if this is a better path
                if neighbor_id not in best_nodes or new_g_cost < best_nodes[neighbor_id].g_cost:
                    h_cost = self.graph.heuristic(neighbor_id, to_stop_id)

                    neighbor_time = current.arrival_time + timedelta(minutes=edge.duration_minutes)
                    if current.edge_used and current.edge_used.line != edge.line:
                        neighbor_time += timedelta(minutes=self.graph.TRANSFER_PENALTY)

                    neighbor_node = SearchNode(
                        stop_id=neighbor_id,
                        g_cost=new_g_cost,
                        h_cost=h_cost,
                        parent=current,
                        edge_used=edge,
                        arrival_time=neighbor_time,
                    )

                    best_nodes[neighbor_id] = neighbor_node
                    heapq.heappush(open_set, neighbor_node)

        logger.warning(f"No path found from {from_stop_id} to {to_stop_id}")
        return None

    def _count_transfers(self, node: SearchNode) -> int:
        """Count number of transfers in path to this node."""
        transfers = 0
        current = node
        prev_line = None

        while current.parent:
            if current.edge_used and not current.edge_used.is_walking:
                if prev_line and prev_line != current.edge_used.line:
                    transfers += 1
                prev_line = current.edge_used.line
            current = current.parent

        return transfers

    def _reconstruct_path(self, goal_node: SearchNode) -> list[TransitEdge]:
        """Reconstruct path from goal node to start."""
        path = []
        current = goal_node

        while current.parent:
            if current.edge_used:
                path.append(current.edge_used)
            current = current.parent

        path.reverse()
        return path

    def find_multiple_routes(
        self,
        from_stop_id: str,
        to_stop_id: str,
        num_routes: int = 3,
        max_transfers: int = 3,
        departure_time: Optional[datetime] = None,
    ) -> list[list[TransitEdge]]:
        """Find multiple alternative routes between stops.

        Args:
            from_stop_id: Origin stop ID
            to_stop_id: Destination stop ID
            num_routes: Number of alternative routes to find
            max_transfers: Maximum transfers per route
            departure_time: Departure time

        Returns:
            List of paths, each path is a list of edges
        """
        routes = []
        blocked_edges: set[tuple[str, str, str]] = set()

        for attempt in range(num_routes):
            # Find path avoiding blocked edges
            path = self._find_path_with_blocked_edges(
                from_stop_id, to_stop_id, blocked_edges, max_transfers, departure_time
            )

            if not path:
                break

            routes.append(path)

            # Block the main line used in this path
            main_line = self._get_main_line(path)
            if main_line:
                for edge in path:
                    if edge.line == main_line:
                        blocked_edges.add((edge.from_stop_id, edge.to_stop_id, edge.line))

        return routes

    def _find_path_with_blocked_edges(
        self,
        from_stop_id: str,
        to_stop_id: str,
        blocked_edges: set[tuple[str, str, str]],
        max_transfers: int,
        departure_time: Optional[datetime],
    ) -> Optional[list[TransitEdge]]:
        """Find path while avoiding blocked edges."""
        # Similar to find_path but skip blocked edges
        if departure_time is None:
            departure_time = datetime.now()

        open_set = []
        closed_set: set[str] = set()

        start_node = SearchNode(
            stop_id=from_stop_id,
            g_cost=0.0,
            h_cost=self.graph.heuristic(from_stop_id, to_stop_id),
            arrival_time=departure_time,
        )

        heapq.heappush(open_set, start_node)
        best_nodes: dict[str, SearchNode] = {from_stop_id: start_node}

        while open_set:
            current = heapq.heappop(open_set)

            if current.stop_id == to_stop_id:
                return self._reconstruct_path(current)

            if current.stop_id in closed_set:
                continue

            closed_set.add(current.stop_id)

            transfers = self._count_transfers(current)
            if transfers > max_transfers:
                continue

            for edge in self.graph.get_neighbors(current.stop_id):
                # Skip blocked edges
                if (edge.from_stop_id, edge.to_stop_id, edge.line) in blocked_edges:
                    continue

                neighbor_id = edge.to_stop_id

                if neighbor_id in closed_set:
                    continue

                new_g_cost = current.g_cost + edge.duration_minutes

                if current.edge_used and not edge.is_walking:
                    if current.edge_used.line != edge.line and not current.edge_used.is_walking:
                        new_g_cost += self.graph.TRANSFER_PENALTY

                route_pref = self.graph.ROUTE_TYPE_PREFERENCE.get(edge.route_type, 1.2)
                new_g_cost *= route_pref

                if neighbor_id not in best_nodes or new_g_cost < best_nodes[neighbor_id].g_cost:
                    h_cost = self.graph.heuristic(neighbor_id, to_stop_id)

                    neighbor_time = current.arrival_time + timedelta(minutes=edge.duration_minutes)
                    if current.edge_used and current.edge_used.line != edge.line:
                        neighbor_time += timedelta(minutes=self.graph.TRANSFER_PENALTY)

                    neighbor_node = SearchNode(
                        stop_id=neighbor_id,
                        g_cost=new_g_cost,
                        h_cost=h_cost,
                        parent=current,
                        edge_used=edge,
                        arrival_time=neighbor_time,
                    )

                    best_nodes[neighbor_id] = neighbor_node
                    heapq.heappush(open_set, neighbor_node)

        return None

    def _get_main_line(self, path: list[TransitEdge]) -> str | None:
        """Get the main transit line used in path (not walking)."""
        for edge in path:
            if not edge.is_walking:
                return edge.line
        return None
