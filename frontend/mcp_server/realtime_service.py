"""
Real-time delay integration service for Vienna public transport.
Phase 3B Enhancement: Integrates live vehicle data into routing decisions.

This module fetches real-time vehicle positions and delays from the Wiener
Linien API and adjusts route calculations accordingly.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class LineDelay:
    """Delay information for a transit line."""

    line: str
    average_delay_minutes: float
    max_delay_minutes: float
    affected_stops: list[str]
    severity: str  # "minor", "moderate", "severe"
    last_updated: datetime


@dataclass
class RealTimeUpdate:
    """Real-time update for routing adjustments."""

    line_delays: dict[str, LineDelay]
    disrupted_lines: list[str]
    timestamp: datetime


class RealTimeDelayService:
    """Service for fetching and processing real-time delay data."""

    # Delay thresholds
    MINOR_DELAY = 3  # 0-3 minutes
    MODERATE_DELAY = 7  # 3-7 minutes
    SEVERE_DELAY = 15  # 7+ minutes

    # Cache TTL in seconds
    CACHE_TTL = 60  # 1 minute

    def __init__(self, vehicle_service_module=None):
        """Initialize real-time service.

        Args:
            vehicle_service_module: Module containing collect_vehicle_data function
        """
        self.vehicle_service = vehicle_service_module
        self._cache: Optional[RealTimeUpdate] = None
        self._cache_time: Optional[datetime] = None

    def get_realtime_updates(self, use_cache: bool = True) -> Optional[RealTimeUpdate]:
        """Get real-time delay updates for all lines.

        Args:
            use_cache: Whether to use cached data if available

        Returns:
            RealTimeUpdate object with current delay information
        """
        # Check cache
        if use_cache and self._cache and self._cache_time:
            age_seconds = (datetime.now() - self._cache_time).total_seconds()
            if age_seconds < self.CACHE_TTL:
                logger.debug(f"Using cached real-time data (age: {age_seconds:.1f}s)")
                return self._cache

        # Fetch fresh data
        try:
            updates = self._fetch_updates()
            self._cache = updates
            self._cache_time = datetime.now()
            return updates
        except Exception as e:
            logger.error(f"Error fetching real-time updates: {e}", exc_info=True)
            return self._cache  # Return stale cache if fetch fails

    def _fetch_updates(self) -> RealTimeUpdate:
        """Fetch real-time updates from vehicle service."""
        if not self.vehicle_service:
            logger.warning("Vehicle service not available, returning empty updates")
            return RealTimeUpdate(line_delays={}, disrupted_lines=[], timestamp=datetime.now())

        try:
            # Collect vehicle data for all lines
            vehicle_data = self.vehicle_service.collect_vehicle_data(
                vehicle_type="all", lines=None, station=None
            )

            vehicles = vehicle_data.get("vehicles", [])

            # Group vehicles by line
            line_groups: dict[str, list[dict]] = {}
            for vehicle in vehicles:
                line = vehicle.get("line")
                if line:
                    if line not in line_groups:
                        line_groups[line] = []
                    line_groups[line].append(vehicle)

            # Calculate delays per line
            line_delays = {}
            disrupted_lines = []

            for line, vehicles_on_line in line_groups.items():
                delays = []
                affected_stops = set()

                for vehicle in vehicles_on_line:
                    delay = vehicle.get("delay_minutes", 0)
                    if delay:
                        delays.append(delay)
                        stop = vehicle.get("station")
                        if stop:
                            affected_stops.add(stop)

                if delays:
                    avg_delay = sum(delays) / len(delays)
                    max_delay = max(delays)

                    # Determine severity
                    if max_delay >= self.SEVERE_DELAY:
                        severity = "severe"
                        disrupted_lines.append(line)
                    elif max_delay >= self.MODERATE_DELAY:
                        severity = "moderate"
                    else:
                        severity = "minor"

                    line_delays[line] = LineDelay(
                        line=line,
                        average_delay_minutes=avg_delay,
                        max_delay_minutes=max_delay,
                        affected_stops=list(affected_stops),
                        severity=severity,
                        last_updated=datetime.now(),
                    )

            return RealTimeUpdate(
                line_delays=line_delays, disrupted_lines=disrupted_lines, timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error processing vehicle data for delays: {e}", exc_info=True)
            return RealTimeUpdate(line_delays={}, disrupted_lines=[], timestamp=datetime.now())

    def adjust_route_for_delays(
        self, route_option: "RouteOption", realtime_updates: Optional[RealTimeUpdate] = None
    ) -> "RouteOption":
        """Adjust route timing based on real-time delays.

        Args:
            route_option: Original route option
            realtime_updates: Real-time delay data (fetched if not provided)

        Returns:
            Adjusted route option with updated times
        """
        if realtime_updates is None:
            realtime_updates = self.get_realtime_updates()

        if not realtime_updates or not realtime_updates.line_delays:
            # No delay data available
            return route_option

        adjusted_segments = []
        cumulative_delay = 0.0

        for segment in route_option.segments:
            line_delay = realtime_updates.line_delays.get(segment.line)

            if line_delay:
                # Add average delay for this line
                delay_to_add = line_delay.average_delay_minutes
                cumulative_delay += delay_to_add

                logger.debug(f"Adding {delay_to_add:.1f} min delay to {segment.line}")

            # Create adjusted segment
            adjusted_segment = RouteSegment(
                line=segment.line,
                from_stop_id=segment.from_stop_id,
                from_stop_name=segment.from_stop_name,
                to_stop_id=segment.to_stop_id,
                to_stop_name=segment.to_stop_name,
                departure_time=segment.departure_time + timedelta(minutes=cumulative_delay),
                arrival_time=segment.arrival_time + timedelta(minutes=cumulative_delay),
                duration_minutes=segment.duration_minutes,
                vehicle_type=segment.vehicle_type,
                distance_meters=segment.distance_meters,
            )
            adjusted_segments.append(adjusted_segment)

        # Create adjusted route option
        adjusted_option = RouteOption(
            segments=adjusted_segments,
            total_duration_minutes=route_option.total_duration_minutes + int(cumulative_delay),
            transfers=route_option.transfers,
            total_distance_meters=route_option.total_distance_meters,
            departure_time=route_option.departure_time,
            arrival_time=route_option.arrival_time + timedelta(minutes=cumulative_delay),
            estimated_cost=route_option.estimated_cost,
        )

        return adjusted_option

    def rank_routes_by_reliability(
        self, routes: list["RouteOption"], realtime_updates: Optional[RealTimeUpdate] = None
    ) -> list[tuple["RouteOption", float]]:
        """Rank routes by reliability considering real-time delays.

        Args:
            routes: List of route options
            realtime_updates: Real-time delay data

        Returns:
            List of (route, reliability_score) tuples, sorted by score
        """
        if realtime_updates is None:
            realtime_updates = self.get_realtime_updates()

        ranked = []

        for route in routes:
            score = self._calculate_reliability_score(route, realtime_updates)
            ranked.append((route, score))

        # Sort by score (higher is better)
        ranked.sort(key=lambda x: x[1], reverse=True)

        return ranked

    def _calculate_reliability_score(
        self, route: "RouteOption", realtime_updates: RealTimeUpdate
    ) -> float:
        """Calculate reliability score for a route (0-100).

        Factors:
        - Number of transfers (fewer is better)
        - Lines with delays (penalized)
        - Severity of delays
        - Route complexity

        Args:
            route: Route option to score
            realtime_updates: Current delay data

        Returns:
            Reliability score (0-100, higher is better)
        """
        score = 100.0

        # Penalize transfers
        score -= route.transfers * 5

        # Penalize affected lines
        for segment in route.segments:
            line_delay = realtime_updates.line_delays.get(segment.line)
            if line_delay:
                if line_delay.severity == "severe":
                    score -= 20
                elif line_delay.severity == "moderate":
                    score -= 10
                elif line_delay.severity == "minor":
                    score -= 3

        # Penalize long routes (more chance of issues)
        if route.total_duration_minutes > 30:
            score -= (route.total_duration_minutes - 30) * 0.5

        return max(0.0, score)


# Singleton instance
_realtime_service: Optional[RealTimeDelayService] = None


def get_realtime_service(vehicle_service_module=None) -> RealTimeDelayService:
    """Get or create real-time delay service instance."""
    global _realtime_service
    if _realtime_service is None:
        _realtime_service = RealTimeDelayService(vehicle_service_module)
    return _realtime_service
