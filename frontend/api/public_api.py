"""
Public API with rate limiting and authentication.
Phase 4 Enhancement: Developer-friendly public API for third-party integration.
"""

import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["public-api"])


# Simple in-memory rate limiter (production would use Redis)
class RateLimiter:
    """Simple rate limiter for API endpoints."""

    def __init__(self, requests_per_minute: int = 60):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute per API key
        """
        self.requests_per_minute = requests_per_minute
        self.requests: defaultdict = defaultdict(list)

    def is_allowed(self, api_key: str) -> bool:
        """Check if request is allowed under rate limit.

        Args:
            api_key: API key making the request

        Returns:
            True if request allowed
        """
        now = time.time()
        minute_ago = now - 60

        # Clean old requests
        self.requests[api_key] = [
            req_time for req_time in self.requests[api_key] if req_time > minute_ago
        ]

        # Check limit
        if len(self.requests[api_key]) >= self.requests_per_minute:
            return False

        # Record request
        self.requests[api_key].append(now)
        return True

    def get_remaining(self, api_key: str) -> int:
        """Get remaining requests in current minute."""
        now = time.time()
        minute_ago = now - 60

        recent = [req for req in self.requests[api_key] if req > minute_ago]
        return max(0, self.requests_per_minute - len(recent))


# Global rate limiter
rate_limiter = RateLimiter(requests_per_minute=60)


async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> str:
    """Verify API key from request header.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key invalid or missing
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Get your key at /api/v1/docs",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Simple validation (production would check database)
    if len(x_api_key) < 32:
        raise HTTPException(status_code=401, detail="Invalid API key format")

    # Check rate limit
    if not rate_limiter.is_allowed(x_api_key):
        remaining_time = 60  # seconds until reset
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {remaining_time} seconds.",
            headers={"Retry-After": str(remaining_time)},
        )

    return x_api_key


@router.get("/")
async def api_info() -> JSONResponse:
    """Public API information and documentation.

    Returns:
        API overview and endpoints
    """
    return JSONResponse(
        {
            "name": "Wiener Linien Live Map Public API",
            "version": "1.0.0",
            "description": "Public API for Vienna (and Austrian) public transport data",
            "documentation": "/api/v1/docs",
            "authentication": "X-API-Key header required",
            "rate_limit": "60 requests per minute",
            "endpoints": {
                "departures": "/api/v1/departures",
                "stations": "/api/v1/stations",
                "journey": "/api/v1/journey",
                "predictions": "/api/v1/predictions",
                "cities": "/api/v1/cities",
            },
            "get_api_key": "Contact: admin@mywienerlinien.com (placeholder)",
            "timestamp": datetime.now().isoformat(),
        }
    )


@router.get("/departures")
async def public_departures(
    station: str, limit: int = 5, api_key: str = Depends(verify_api_key)
) -> JSONResponse:
    """Get real-time departures for a station (Public API).

    Args:
        station: Station name
        limit: Maximum departures (1-10)
        api_key: API key (from X-API-Key header)

    Returns:
        List of departures
    """
    try:
        # Import MCP tool
        from mcp_server.tools.departures import get_next_departures_internal

        departures = await get_next_departures_internal(station, min(10, max(1, limit)))

        return JSONResponse(
            {
                "station": station,
                "departures": departures,
                "count": len(departures),
                "rate_limit_remaining": rate_limiter.get_remaining(api_key),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as exc:
        logger.error(f"Public API departures error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get departures")


@router.get("/stations")
async def public_stations(
    query: Optional[str] = None, limit: int = 10, api_key: str = Depends(verify_api_key)
) -> JSONResponse:
    """Search stations (Public API).

    Args:
        query: Search query (returns all if None)
        limit: Maximum results (1-50)
        api_key: API key

    Returns:
        List of stations
    """
    try:
        from database import db

        if query:
            # Search by name
            results = db.execute_query(
                """
            SELECT stop_id, stop_name, stop_lat, stop_lon
            FROM stops
            WHERE LOWER(stop_name) LIKE LOWER(:query)
            LIMIT :limit
            """,
                {"query": f"%{query}%", "limit": min(50, max(1, limit))},
            )
        else:
            # All stations
            results = db.execute_query(
                """
            SELECT stop_id, stop_name, stop_lat, stop_lon
            FROM stops
            WHERE location_type = 1 OR parent_station IS NULL
            ORDER BY stop_name
            LIMIT :limit
            """,
                {"limit": min(50, max(1, limit))},
            )

        stations = [
            {"id": r["stop_id"], "name": r["stop_name"], "lat": r["stop_lat"], "lng": r["stop_lon"]}
            for r in results
        ]

        return JSONResponse(
            {
                "stations": stations,
                "count": len(stations),
                "query": query,
                "rate_limit_remaining": rate_limiter.get_remaining(api_key),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as exc:
        logger.error(f"Public API stations error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to search stations")


@router.get("/journey")
async def public_journey(
    from_station: str,
    to_station: str,
    alternatives: int = 3,
    api_key: str = Depends(verify_api_key),
) -> JSONResponse:
    """Plan journey between stations (Public API).

    Args:
        from_station: Origin station name
        to_station: Destination station name
        alternatives: Number of route options (1-5)
        api_key: API key

    Returns:
        Journey plan with routes
    """
    try:
        from mcp_server.tools.journey import get_journey_planner
        from mcp_server.utils import find_station_by_name

        # Find stations
        from_info = find_station_by_name(from_station)
        to_info = find_station_by_name(to_station)

        if not from_info:
            raise HTTPException(
                status_code=404, detail=f"Origin station '{from_station}' not found"
            )
        if not to_info:
            raise HTTPException(
                status_code=404, detail=f"Destination station '{to_station}' not found"
            )

        # Plan journey
        planner = get_journey_planner()
        route_options = planner.plan_journey(
            from_info["id"],
            to_info["id"],
            datetime.now(),
            num_alternatives=min(5, max(1, alternatives)),
        )

        if not route_options:
            raise HTTPException(status_code=404, detail="No routes found")

        # Format response
        routes_data = []
        for route in route_options:
            routes_data.append(
                {
                    "from": from_info["name"],
                    "to": to_info["name"],
                    "duration_minutes": route.total_duration_minutes,
                    "transfers": route.transfers,
                    "cost": route.estimated_cost,
                    "segments": [
                        {
                            "line": seg.line,
                            "from": seg.from_stop_name,
                            "to": seg.to_stop_name,
                            "duration": seg.duration_minutes,
                            "vehicle_type": seg.vehicle_type,
                        }
                        for seg in route.segments
                    ],
                }
            )

        return JSONResponse(
            {
                "routes": routes_data,
                "count": len(routes_data),
                "rate_limit_remaining": rate_limiter.get_remaining(api_key),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Public API journey error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Journey planning failed")


@router.get("/predictions/{line}")
async def public_prediction(line: str, api_key: str = Depends(verify_api_key)) -> JSONResponse:
    """Get ML delay prediction for a line (Public API).

    Args:
        line: Line code (e.g., "U1", "U3")
        api_key: API key

    Returns:
        Delay prediction
    """
    try:
        from mcp_server.prediction_service import get_prediction_service

        predictor = get_prediction_service()
        prediction = predictor.predict_delay(line, datetime.now(), use_fallback=True)

        if not prediction:
            raise HTTPException(status_code=404, detail=f"No prediction available for {line}")

        return JSONResponse(
            {
                "line": prediction.line,
                "predicted_delay_minutes": round(prediction.predicted_delay_minutes, 2),
                "confidence": round(prediction.confidence, 3),
                "timestamp": prediction.timestamp.isoformat(),
                "rate_limit_remaining": rate_limiter.get_remaining(api_key),
            }
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Public API prediction error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Prediction failed")
