"""
Analytics API endpoints for transit data visualization.
Phase 3C Enhancement: Historical analytics and ML predictions dashboard.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/line-reliability")
async def get_line_reliability(
    days: int = Query(30, ge=1, le=365, description="Days to analyze"),
    lines: Optional[str] = Query(None, description="Comma-separated line filter"),
) -> JSONResponse:
    """Get reliability statistics for transit lines.

    Args:
        days: Number of days to analyze (1-365)
        lines: Optional filter by specific lines

    Returns:
        Reliability statistics per line
    """
    try:
        from ..database import db
        from ..mcp_server.historical_data import get_historical_collector

        collector = get_historical_collector(db)
        stats = collector.get_line_reliability_stats(days=days)

        # Filter if requested
        if lines:
            line_list = [line_str.strip() for line_str in lines.split(",")]
            stats = {k: v for k, v in stats.items() if k in line_list}

        return JSONResponse(
            {
                "stats": stats,
                "days_analyzed": days,
                "lines_count": len(stats),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting line reliability: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get reliability stats")


@router.get("/delay-patterns")
async def get_delay_patterns(
    line: Optional[str] = Query(None, description="Line filter"),
) -> JSONResponse:
    """Get identified delay patterns.

    Args:
        line: Optional filter by specific line

    Returns:
        Delay patterns by time/day
    """
    try:
        from ..database import db
        from ..mcp_server.historical_data import get_historical_collector

        collector = get_historical_collector(db)
        patterns = collector.analyze_delay_patterns(line=line)

        patterns_data = [p.to_dict() for p in patterns]

        return JSONResponse(
            {
                "patterns": patterns_data,
                "pattern_count": len(patterns),
                "line_filter": line,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting delay patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get delay patterns")


@router.get("/predictions/{line}")
async def get_line_prediction(
    line: str, target_time: Optional[str] = Query(None, description="ISO format target time")
) -> JSONResponse:
    """Get ML prediction for line delay.

    Args:
        line: Line to predict for
        target_time: Optional target time (defaults to now)

    Returns:
        Delay prediction with confidence
    """
    try:
        from ..mcp_server.prediction_service import get_prediction_service

        predictor = get_prediction_service()

        # Parse target time
        if target_time:
            try:
                target_dt = datetime.fromisoformat(target_time.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                target_dt = datetime.now()
        else:
            target_dt = datetime.now()

        # Get prediction
        prediction = predictor.predict_delay(line, target_dt, use_fallback=True)

        if not prediction:
            raise HTTPException(status_code=404, detail=f"No prediction available for {line}")

        return JSONResponse(
            {
                "line": prediction.line,
                "predicted_delay_minutes": round(prediction.predicted_delay_minutes, 2),
                "confidence": round(prediction.confidence, 3),
                "factors": prediction.factors,
                "target_time": target_dt.isoformat(),
                "prediction_time": prediction.timestamp.isoformat(),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Prediction failed")


@router.get("/heatmap")
async def get_delay_heatmap(
    line: str, days: int = Query(30, ge=7, le=90, description="Days to analyze")
) -> JSONResponse:
    """Get delay heatmap data (day x hour matrix).

    Args:
        line: Line to analyze
        days: Days of data to include

    Returns:
        Matrix of delays by day/hour
    """
    try:
        from ..database import db

        query = """
        SELECT
            EXTRACT(DOW FROM timestamp)::INTEGER as day_of_week,
            EXTRACT(HOUR FROM timestamp)::INTEGER as hour,
            AVG(delay_minutes) as avg_delay,
            COUNT(*) as sample_count
        FROM historical_vehicles
        WHERE line = :line
            AND timestamp > NOW() - INTERVAL ':days days'
            AND delay_minutes IS NOT NULL
        GROUP BY day_of_week, hour
        ORDER BY day_of_week, hour
        """

        results = db.execute_query(query, {"line": line, "days": days})

        # Build 7x24 matrix
        heatmap = [[0.0 for _ in range(24)] for _ in range(7)]
        counts = [[0 for _ in range(24)] for _ in range(7)]

        for row in results:
            dow = int(row["day_of_week"])
            hour = int(row["hour"])
            heatmap[dow][hour] = float(row["avg_delay"])
            counts[dow][hour] = row["sample_count"]

        return JSONResponse(
            {
                "line": line,
                "heatmap": heatmap,
                "sample_counts": counts,
                "days_analyzed": days,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error generating heatmap: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Heatmap generation failed")


@router.get("/summary")
async def get_analytics_summary() -> JSONResponse:
    """Get overall analytics summary.

    Returns:
        Summary of historical data, patterns, and predictions
    """
    try:
        from ..database import db
        from ..mcp_server.historical_data import get_historical_collector
        from ..mcp_server.prediction_service import ML_AVAILABLE, get_prediction_service

        collector = get_historical_collector(db)
        predictor = get_prediction_service()

        # Get data counts
        vehicle_count_query = "SELECT COUNT(*) as count FROM historical_vehicles"
        journey_count_query = "SELECT COUNT(*) as count FROM historical_journeys"
        pattern_count_query = "SELECT COUNT(*) as count FROM delay_patterns"

        vehicle_count = db.execute_query(vehicle_count_query)[0]["count"]
        journey_count = db.execute_query(journey_count_query)[0]["count"]
        pattern_count = db.execute_query(pattern_count_query)[0]["count"]

        # Get model status
        models_loaded = len(predictor.models)

        # Get reliability stats
        reliability_stats = collector.get_line_reliability_stats(days=30)

        return JSONResponse(
            {
                "data_collection": {
                    "vehicle_snapshots": vehicle_count,
                    "journey_records": journey_count,
                    "delay_patterns": pattern_count,
                },
                "ml_models": {
                    "models_loaded": models_loaded,
                    "ml_available": ML_AVAILABLE,
                    "trained_lines": list(predictor.models.keys()),
                },
                "reliability": {
                    "lines_analyzed": len(reliability_stats),
                    "most_reliable": max(
                        reliability_stats.items(), key=lambda x: x[1]["reliability_score"]
                    )[0]
                    if reliability_stats
                    else None,
                    "least_reliable": min(
                        reliability_stats.items(), key=lambda x: x[1]["reliability_score"]
                    )[0]
                    if reliability_stats
                    else None,
                },
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get analytics summary")
