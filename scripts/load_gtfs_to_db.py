import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

try:
    import faulthandler

    faulthandler.enable()
except Exception:
    pass

try:
    from models.gtfs_models import (
        Agency,
        Route,
        Shape,
        Stop,
        StopTime,
        Trip,
        engine,
        init_db,
    )
except ImportError:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.append(str(project_root))
    from models.gtfs_models import (  # type: ignore
        Agency,
        Route,
        Shape,
        Stop,
        StopTime,
        Trip,
        engine,
        init_db,
    )

try:
    from .rbl_mapper import MetadataDownloadError, build_stop_rbl_mapping
except ImportError:  # pragma: no cover - support direct execution
    from rbl_mapper import MetadataDownloadError, build_stop_rbl_mapping  # type: ignore

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("gtfs-loader")

HEARTBEAT_FILE = Path(os.environ.get("GTFS_HEARTBEAT_PATH", "/app/data/gtfs_loader_heartbeat.json"))
LOG_DIR = Path(os.environ.get("GTFS_LOG_DIR", "")) if os.environ.get("GTFS_LOG_DIR") else None

if LOG_DIR:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        logfile = LOG_DIR / "gtfs_loader.log"
        file_handler = logging.FileHandler(logfile, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)
        logging.getLogger().addHandler(file_handler)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Unable to create loader logfile at %s: %s", LOG_DIR, exc)


def record_heartbeat(stage: str, **details: Any) -> None:
    """Emit a structured heartbeat for monitoring/alerting.”"""
    payload: Dict[str, Any] = {
        "stage": stage,
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "details": details,
    }
    summary = " ".join(f"{key}={value}" for key, value in details.items())
    logger.info("HEARTBEAT stage=%s %s", stage, summary.strip())
    try:
        HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with HEARTBEAT_FILE.open("w", encoding="utf-8") as heartbeat_handle:
            json.dump(payload, heartbeat_handle, ensure_ascii=False, indent=2)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to write heartbeat file: %s", exc, exc_info=True)


def _safe(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):  # type: ignore[arg-type]
            return None
    except TypeError:
        pass
    return value


def _safe_float(value: Any) -> Optional[float]:
    raw = _safe(value)
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> Optional[int]:
    raw = _safe(value)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _get_table(feed: Any, table_name: str, candidates: Iterable[str]) -> Optional[pd.DataFrame]:
    for attr in candidates:
        table = getattr(feed, attr, None)
        if table is not None:
            return table
    logger.warning("Feed missing expected table '%s' (candidates: %s)", table_name, ", ".join(candidates))
    return None


def disable_materialized_view_triggers(session: Session) -> None:
    """Disable triggers that refresh the materialized view during bulk loading."""
    logger.info("Disabling materialized view refresh triggers for bulk load...")
    # Map trigger names to their table names
    trigger_table_map = [
        ("refresh_route_stop_patterns_routes", "routes"),
        ("refresh_route_stop_patterns_trips", "trips"),
        ("refresh_route_stop_patterns_stop_times", "stop_times"),
        ("refresh_route_stop_patterns_stops", "stops"),
    ]
    disabled_count = 0
    for trigger_name, table_name in trigger_table_map:
        try:
            session.execute(
                text(f'ALTER TABLE {table_name} DISABLE TRIGGER {trigger_name};')
            )
            disabled_count += 1
        except Exception as exc:
            logger.warning("Could not disable trigger %s on table %s: %s", trigger_name, table_name, exc)
    session.commit()
    logger.info("Disabled %d materialized view refresh triggers.", disabled_count)


def disable_indexes(session: Session) -> None:
    """Disable indexes during bulk loading for better performance."""
    logger.info("Disabling indexes for bulk load performance...")
    indexes_to_disable = [
        ("idx_stop_times_trip_id", "stop_times"),
        ("idx_stop_times_stop_id", "stop_times"),
        ("idx_stops_location", "stops"),
        ("idx_routes_agency_id", "routes"),
        ("idx_trips_route_id", "trips"),
        ("idx_shapes_shape_id", "shapes"),
        ("idx_stops_geom", "stops"),  # Spatial index
    ]
    disabled_count = 0
    for index_name, table_name in indexes_to_disable:
        try:
            session.execute(text(f"DROP INDEX IF EXISTS {index_name};"))
            disabled_count += 1
        except Exception as exc:
            logger.warning("Could not drop index %s: %s", index_name, exc)
    session.commit()
    logger.info("Disabled %d indexes.", disabled_count)


def optimize_database_for_bulk_load(session: Session) -> str:
    """Optimize database settings for bulk loading. Returns original synchronous_commit value."""
    logger.info("Optimizing database settings for bulk load...")
    try:
        # Get current synchronous_commit setting
        result = session.execute(text("SHOW synchronous_commit;"))
        original_value = result.scalar() or "on"
        
        # Disable synchronous commits for much faster bulk loading
        # This is safe because we're doing a full reload (truncate + insert)
        session.execute(text("SET synchronous_commit = off;"))
        session.commit()
        logger.info("Disabled synchronous_commit for bulk load (was: %s)", original_value)
        return original_value
    except Exception as exc:
        logger.warning("Could not optimize database settings: %s", exc)
        return "on"


def restore_database_settings(session: Session, original_sync_commit: str) -> None:
    """Restore database settings after bulk loading."""
    logger.info("Restoring database settings...")
    try:
        # Validate value is safe (should only be 'on', 'off', 'local', 'remote_write', or 'remote_apply')
        safe_values = {'on', 'off', 'local', 'remote_write', 'remote_apply'}
        value = original_sync_commit.lower() if original_sync_commit.lower() in safe_values else 'on'
        session.execute(text(f"SET synchronous_commit = {value};"))
        session.commit()
        logger.info("Restored synchronous_commit to %s", value)
    except Exception as exc:
        logger.warning("Could not restore database settings: %s", exc)


def recreate_indexes(session: Session) -> None:
    """Recreate indexes after bulk loading."""
    logger.info("Recreating indexes after bulk load...")
    start = time.perf_counter()
    indexes_to_create = [
        ("idx_stop_times_trip_id", "CREATE INDEX idx_stop_times_trip_id ON stop_times(trip_id);"),
        ("idx_stop_times_stop_id", "CREATE INDEX idx_stop_times_stop_id ON stop_times(stop_id);"),
        ("idx_stops_location", "CREATE INDEX idx_stops_location ON stops(stop_lat, stop_lon);"),
        ("idx_routes_agency_id", "CREATE INDEX idx_routes_agency_id ON routes(agency_id);"),
        ("idx_trips_route_id", "CREATE INDEX idx_trips_route_id ON trips(route_id);"),
        ("idx_shapes_shape_id", "CREATE INDEX idx_shapes_shape_id ON shapes(shape_id);"),
        ("idx_stops_geom", "CREATE INDEX idx_stops_geom ON stops USING GIST (ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326));"),
    ]
    created_count = 0
    for index_name, create_sql in indexes_to_create:
        try:
            session.execute(text(create_sql))
            created_count += 1
        except Exception as exc:
            logger.warning("Could not create index %s: %s", index_name, exc)
    session.commit()
    logger.info("Recreated %d indexes in %.1f seconds.", created_count, time.perf_counter() - start)


def enable_materialized_view_triggers(session: Session) -> None:
    """Re-enable triggers and refresh the materialized view."""
    logger.info("Re-enabling materialized view refresh triggers...")
    trigger_table_map = [
        ("refresh_route_stop_patterns_routes", "routes"),
        ("refresh_route_stop_patterns_trips", "trips"),
        ("refresh_route_stop_patterns_stop_times", "stop_times"),
        ("refresh_route_stop_patterns_stops", "stops"),
    ]
    enabled_count = 0
    for trigger_name, table_name in trigger_table_map:
        try:
            session.execute(
                text(f'ALTER TABLE {table_name} ENABLE TRIGGER {trigger_name};')
            )
            enabled_count += 1
        except Exception as exc:
            logger.warning("Could not enable trigger %s on table %s: %s", trigger_name, table_name, exc)
    session.commit()
    logger.info("Enabled %d materialized view refresh triggers.", enabled_count)
    
    logger.info("Refreshing materialized view route_stop_patterns...")
    start = time.perf_counter()
    try:
        # Use non-concurrent refresh for faster completion (blocks reads briefly)
        session.execute(text("REFRESH MATERIALIZED VIEW route_stop_patterns;"))
        session.commit()
        logger.info("Materialized view refreshed in %.1f seconds.", time.perf_counter() - start)
    except Exception as exc:
        logger.warning("Could not refresh materialized view (non-concurrent): %s", exc, exc_info=True)
        # Try concurrent refresh as fallback
        try:
            session.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY route_stop_patterns;"))
            session.commit()
            logger.info("Materialized view refreshed (concurrent) in %.1f seconds.", time.perf_counter() - start)
        except Exception as exc2:
            logger.error("Failed to refresh materialized view: %s", exc2, exc_info=True)


def truncate_tables(session: Session) -> None:
    start = time.perf_counter()
    logger.info("Clearing existing GTFS tables before reload (TRUNCATE)...")
    session.execute(
        text(
            """
            TRUNCATE TABLE 
                stop_times,
                trips,
                routes,
                stops,
                agencies,
                shapes
            RESTART IDENTITY CASCADE
            """
        )
    )
    session.commit()
    logger.info("GTFS tables truncated in %.1f seconds.", time.perf_counter() - start)
    record_heartbeat("truncate_complete", duration_seconds=round(time.perf_counter() - start, 1))


def load_agencies(session: Session, feed: Any, default_timezone: str = "Europe/Vienna") -> int:
    agencies_df = _get_table(feed, "agency", ("agencies", "agency"))
    if agencies_df is None or agencies_df.empty:
        logger.warning("No agencies found; skipping agency load.")
        return 0

    start = time.perf_counter()
    agencies = [
        Agency(
            agency_id=_safe(row.get("agency_id")) or "",
            agency_name=_safe(row.get("agency_name")) or "",
            agency_url=_safe(row.get("agency_url")),
            agency_timezone=_safe(row.get("agency_timezone")) or default_timezone,
            agency_lang=_safe(row.get("agency_lang")) or "de",
            agency_phone=_safe(row.get("agency_phone")),
        )
        for _, row in agencies_df.iterrows()
    ]

    if not agencies:
        logger.warning("No agency records to insert.")
        return 0

    # Use bulk_insert_mappings for better performance (skips ORM overhead)
    mappings = [
        {
            "agency_id": a.agency_id,
            "agency_name": a.agency_name,
            "agency_url": a.agency_url,
            "agency_timezone": a.agency_timezone,
            "agency_lang": a.agency_lang,
            "agency_phone": a.agency_phone,
        }
        for a in agencies
    ]
    session.bulk_insert_mappings(Agency, mappings)
    session.commit()
    logger.info("Agencies loaded: %d (%.1f seconds)", len(agencies), time.perf_counter() - start)
    record_heartbeat("agencies_loaded", count=len(agencies), duration_seconds=round(time.perf_counter() - start, 1))
    return len(agencies)


def load_stops(session: Session, feed: Any, metadata_dir: Optional[Path] = None, enable_rbl_mapping: bool = True) -> int:
    stops_df = getattr(feed, "stops", None)
    if stops_df is None or stops_df.empty:
        logger.warning("No stops found; skipping stop load.")
        return 0

    start = time.perf_counter()
    rows = stops_df.to_dict(orient="records")

    rbl_mapping: Dict[str, Dict[str, object]] = {}
    if metadata_dir is not None and enable_rbl_mapping:
        try:
            rbl_mapping = build_stop_rbl_mapping(rows, metadata_dir, logger)
        except MetadataDownloadError as exc:
            logger.warning("RBL enrichment skipped during stop load: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to build RBL mapping for stops: %s", exc, exc_info=True)

    stops = []
    for row in rows:
        stop_id = _safe(row.get("stop_id"))
        mapped = rbl_mapping.get(str(stop_id) if stop_id is not None else "")
        rbl_numbers = mapped.get("rbl_numbers") if isinstance(mapped, dict) else None
        if isinstance(rbl_numbers, list):
            rbl_string = ",".join(str(r) for r in rbl_numbers if r)
        else:
            rbl_string = ""
        diva_value = mapped.get("diva") if isinstance(mapped, dict) else None

        stop_object = Stop(
            stop_id=stop_id,
            stop_code=rbl_string or (_safe(row.get("stop_code")) or ""),
            stop_name=_safe(row.get("stop_name")) or "",
            stop_desc=_safe(row.get("stop_desc")),
            stop_lat=_safe(row.get("stop_lat")),
            stop_lon=_safe(row.get("stop_lon")),
            zone_id=_safe(row.get("zone_id")),
            stop_url=_safe(row.get("stop_url")),
            location_type=int(_safe(row.get("location_type")) or 0),
            parent_station=_safe(row.get("parent_station")),
            wheelchair_boarding=_safe(row.get("wheelchair_boarding")),
        )
        if diva_value:
            if stop_object.stop_desc:
                stop_object.stop_desc = f"{stop_object.stop_desc} (DIVA:{diva_value})"
            else:
                stop_object.stop_desc = f"DIVA:{diva_value}"
        stops.append(stop_object)


    if not stops:
        logger.warning("No stop records to insert.")
        return 0

    # Use bulk_insert_mappings for better performance
    mappings = [
        {
            "stop_id": s.stop_id,
            "stop_code": s.stop_code,
            "stop_name": s.stop_name,
            "stop_desc": s.stop_desc,
            "stop_lat": s.stop_lat,
            "stop_lon": s.stop_lon,
            "zone_id": s.zone_id,
            "stop_url": s.stop_url,
            "location_type": s.location_type,
            "parent_station": s.parent_station,
            "wheelchair_boarding": s.wheelchair_boarding,
        }
        for s in stops
    ]
    session.bulk_insert_mappings(Stop, mappings)
    session.commit()
    logger.info("Stops loaded: %d (%.1f seconds)", len(stops), time.perf_counter() - start)
    record_heartbeat("stops_loaded", count=len(stops), duration_seconds=round(time.perf_counter() - start, 1))
    return len(stops)


def load_shapes(session: Session, feed: Any, chunk_size: int, max_shapes: Optional[int]) -> int:
    shapes_df = getattr(feed, "shapes", None)
    if shapes_df is None or shapes_df.empty:
        logger.warning("No shapes found; route polylines will be unavailable.")
        return 0

    shapes_df = shapes_df.sort_values(["shape_id", "shape_pt_sequence"])
    total_rows = len(shapes_df)
    if max_shapes:
        total_rows = min(total_rows, max_shapes)
        shapes_df = shapes_df.iloc[:total_rows]
        logger.info("Shape import limited to first %d rows.", total_rows)
    else:
        logger.info("Loading shapes (%d rows)...", total_rows)

    start = time.perf_counter()
    buffered = []
    processed = 0
    last_heartbeat = time.perf_counter()

    for _, row in shapes_df.iterrows():
        shape_id = _safe(row.get("shape_id"))
        lat = _safe_float(row.get("shape_pt_lat"))
        lon = _safe_float(row.get("shape_pt_lon"))
        if not shape_id or lat is None or lon is None:
            continue

        seq_value = _safe(row.get("shape_pt_sequence"))
        try:
            sequence = int(seq_value)
        except (TypeError, ValueError):
            continue

        buffered.append(
            Shape(
                shape_id=shape_id,
                shape_pt_lat=lat,
                shape_pt_lon=lon,
                shape_pt_sequence=sequence,
                shape_dist_traveled=_safe_float(row.get("shape_dist_traveled")),
            )
        )
        processed += 1

        if len(buffered) >= chunk_size:
            # Use bulk_insert_mappings for better performance
            mappings = [
                {
                    "shape_id": s.shape_id,
                    "shape_pt_lat": s.shape_pt_lat,
                    "shape_pt_lon": s.shape_pt_lon,
                    "shape_pt_sequence": s.shape_pt_sequence,
                    "shape_dist_traveled": s.shape_dist_traveled,
                }
                for s in buffered
            ]
            session.bulk_insert_mappings(Shape, mappings)
            session.commit()
            buffered.clear()
            logger.info("Shapes committed: %d/%d", processed, total_rows)
            last_heartbeat = time.perf_counter()
            record_heartbeat("shapes_progress", processed=processed, total=total_rows)
        elif time.perf_counter() - last_heartbeat > 30:
            logger.info("Shape loading heartbeat: %d/%d processed.", processed, total_rows)
            last_heartbeat = time.perf_counter()
            record_heartbeat("shapes_progress", processed=processed, total=total_rows)

    if buffered:
        # Use bulk_insert_mappings for better performance
        mappings = [
            {
                "shape_id": s.shape_id,
                "shape_pt_lat": s.shape_pt_lat,
                "shape_pt_lon": s.shape_pt_lon,
                "shape_pt_sequence": s.shape_pt_sequence,
                "shape_dist_traveled": s.shape_dist_traveled,
            }
            for s in buffered
        ]
        session.bulk_insert_mappings(Shape, mappings)
        session.commit()

    logger.info("Shapes loaded: %d (%.1f seconds)", processed, time.perf_counter() - start)
    record_heartbeat("shapes_loaded", count=processed, duration_seconds=round(time.perf_counter() - start, 1))
    return processed


def load_routes(session: Session, feed: Any) -> int:
    routes_df = getattr(feed, "routes", None)
    if routes_df is None or routes_df.empty:
        logger.warning("No routes found; skipping route load.")
        return 0

    start = time.perf_counter()
    routes = []
    for _, row in routes_df.iterrows():
        routes.append(
            Route(
                route_id=_safe(row.get("route_id")),
                agency_id=_safe(row.get("agency_id")),
                route_short_name=_safe(row.get("route_short_name")) or "",
                route_long_name=_safe(row.get("route_long_name")) or "",
                route_desc=_safe(row.get("route_desc")),
                route_type=int(_safe(row.get("route_type")) or 3),
                route_url=_safe(row.get("route_url")),
                route_color=(_safe(row.get("route_color")) or "FFFFFF").upper(),
                route_text_color=(_safe(row.get("route_text_color")) or "000000").upper(),
            )
        )

    if not routes:
        logger.warning("No route records to insert.")
        return 0

    # Use bulk_insert_mappings for better performance
    mappings = [
        {
            "route_id": r.route_id,
            "agency_id": r.agency_id,
            "route_short_name": r.route_short_name,
            "route_long_name": r.route_long_name,
            "route_desc": r.route_desc,
            "route_type": r.route_type,
            "route_url": r.route_url,
            "route_color": r.route_color,
            "route_text_color": r.route_text_color,
        }
        for r in routes
    ]
    session.bulk_insert_mappings(Route, mappings)
    session.commit()
    logger.info("Routes loaded: %d (%.1f seconds)", len(routes), time.perf_counter() - start)
    record_heartbeat("routes_loaded", count=len(routes), duration_seconds=round(time.perf_counter() - start, 1))
    return len(routes)


def load_trips_and_stop_times(
    session: Session,
    feed: Any,
    chunk_size: int,
    max_trips: Optional[int],
) -> Tuple[int, int]:
    trips_df = getattr(feed, "trips", None)
    if trips_df is None or trips_df.empty:
        logger.warning("No trips found; skipping trips and stop times.")
        return 0, 0

    if max_trips:
        trips_df = trips_df.iloc[:max_trips]
        logger.info("Trip import limited to first %d rows.", len(trips_df))

    total_trips = len(trips_df)
    if total_trips == 0:
        logger.warning("No trips to insert after applying limits.")
        return 0, 0

    logger.info(
        "Loading trips and stop times (trips=%d, chunk_size=%d)...",
        total_trips,
        chunk_size,
    )

    stop_times_df = getattr(feed, "stop_times", None)
    if stop_times_df is None or stop_times_df.empty:
        logger.warning("No stop_times found; trips will be inserted without stop sequences.")
        stop_times_df = pd.DataFrame(columns=["trip_id"])
        stop_times_indices = {}
    else:
        # Filter to the subset of stop_times that correspond to the trips we plan to insert,
        # then sort once and build an index for quick lookups.
        stop_times_df = stop_times_df[stop_times_df["trip_id"].isin(trips_df["trip_id"])].copy()
        stop_times_df = stop_times_df.sort_values(["trip_id", "stop_sequence"]).reset_index(drop=True)
        stop_times_indices = {}
        if not stop_times_df.empty:
            raw_indices = stop_times_df.groupby("trip_id").indices
            for key, positions in raw_indices.items():
                safe_key = _safe(key)
                if safe_key is None:
                    continue
                stop_times_indices[safe_key] = positions

    start = time.perf_counter()
    total_stop_times_inserted = 0
    total_trips_inserted = 0
    last_heartbeat = time.perf_counter()

    for chunk_start in range(0, total_trips, chunk_size):
        chunk = trips_df.iloc[chunk_start : chunk_start + chunk_size]
        if chunk.empty:
            continue

        trip_objects = []
        stop_time_objects = []

        for trip_row in chunk.itertuples(index=False):
            trip_id = _safe(getattr(trip_row, "trip_id", None))
            if not trip_id:
                continue

            trip_objects.append(
                Trip(
                    trip_id=trip_id,
                    route_id=_safe(getattr(trip_row, "route_id", None)),
                    service_id=_safe(getattr(trip_row, "service_id", None)) or "",
                    trip_headsign=_safe(getattr(trip_row, "trip_headsign", None)),
                    trip_short_name=_safe(getattr(trip_row, "trip_short_name", None)),
                    direction_id=_safe_int(getattr(trip_row, "direction_id", None)),
                    block_id=_safe(getattr(trip_row, "block_id", None)),
                    shape_id=_safe(getattr(trip_row, "shape_id", None)),
                    wheelchair_accessible=_safe_int(getattr(trip_row, "wheelchair_accessible", None)) or 0,
                    bikes_allowed=_safe_int(getattr(trip_row, "bikes_allowed", None)) or 0,
                )
            )

            positions = stop_times_indices.get(trip_id)
            if positions is None:
                continue

            trip_stop_times = stop_times_df.iloc[positions]
            for st_row in trip_stop_times.itertuples(index=False):
                stop_time_objects.append(
                    StopTime(
                        trip_id=trip_id,
                        arrival_time=_safe(getattr(st_row, "arrival_time", None)) or "",
                        departure_time=_safe(getattr(st_row, "departure_time", None)) or "",
                        stop_id=_safe(getattr(st_row, "stop_id", None)),
                        stop_sequence=int(_safe(getattr(st_row, "stop_sequence", None)) or 0),
                        stop_headsign=_safe(getattr(st_row, "stop_headsign", None)),
                        pickup_type=int(_safe(getattr(st_row, "pickup_type", None)) or 0),
                        drop_off_type=int(_safe(getattr(st_row, "drop_off_type", None)) or 0),
                        shape_dist_traveled=_safe(getattr(st_row, "shape_dist_traveled", None)),
                        timepoint=int(_safe(getattr(st_row, "timepoint", None)) or 1),
                    )
                )

        if trip_objects:
            # Use bulk_insert_mappings for better performance
            trip_mappings = [
                {
                    "trip_id": t.trip_id,
                    "route_id": t.route_id,
                    "service_id": t.service_id,
                    "trip_headsign": t.trip_headsign,
                    "trip_short_name": t.trip_short_name,
                    "direction_id": t.direction_id,
                    "block_id": t.block_id,
                    "shape_id": t.shape_id,
                    "wheelchair_accessible": t.wheelchair_accessible,
                    "bikes_allowed": t.bikes_allowed,
                }
                for t in trip_objects
            ]
            session.bulk_insert_mappings(Trip, trip_mappings)
            total_trips_inserted += len(trip_objects)
        if stop_time_objects:
            # Use bulk_insert_mappings for better performance
            stop_time_mappings = [
                {
                    "trip_id": st.trip_id,
                    "arrival_time": st.arrival_time,
                    "departure_time": st.departure_time,
                    "stop_id": st.stop_id,
                    "stop_sequence": st.stop_sequence,
                    "stop_headsign": st.stop_headsign,
                    "pickup_type": st.pickup_type,
                    "drop_off_type": st.drop_off_type,
                    "shape_dist_traveled": st.shape_dist_traveled,
                    "timepoint": st.timepoint,
                }
                for st in stop_time_objects
            ]
            session.bulk_insert_mappings(StopTime, stop_time_mappings)
            total_stop_times_inserted += len(stop_time_objects)

        session.commit()

        logger.info(
            "Trip chunk %d/%d committed (trips=%d, stop_times=%d, totals trips=%d stop_times=%d)",
            (chunk_start // chunk_size) + 1,
            (total_trips + chunk_size - 1) // chunk_size,
            len(trip_objects),
            len(stop_time_objects),
            total_trips_inserted,
            total_stop_times_inserted,
        )

        if time.perf_counter() - last_heartbeat > 60:
            logger.info(
                "Trip loading heartbeat: processed %.1f%% of trips.",
                (total_trips_inserted / total_trips) * 100,
            )
            last_heartbeat = time.perf_counter()
            record_heartbeat(
                "trips_progress",
                trips_inserted=total_trips_inserted,
                stop_times_inserted=total_stop_times_inserted,
                total_trips=total_trips,
            )

    logger.info(
        "Trips loaded: %d, stop_times loaded: %d (%.1f seconds)",
        total_trips_inserted,
        total_stop_times_inserted,
        time.perf_counter() - start,
    )
    record_heartbeat(
        "trips_loaded",
        trips_inserted=total_trips_inserted,
        stop_times_inserted=total_stop_times_inserted,
        duration_seconds=round(time.perf_counter() - start, 1),
    )
    return total_trips_inserted, total_stop_times_inserted


def load_gtfs_to_db(
    gtfs_path: str,
    chunk_size: int = 5000,
    max_shapes: Optional[int] = None,
    max_trips: Optional[int] = None,
    metadata_dir: Optional[Path] = None,
    default_timezone: str = "Europe/Vienna",
) -> dict:
    record_heartbeat("start", gtfs_path=gtfs_path, chunk_size=chunk_size)
    try:
        import gtfs_kit as gk
    except ImportError:
        logger.error("gtfs_kit not found. Please install it with: pip install gtfs-kit")
        sys.exit(1)

    logger.info("Initializing database models...")
    init_db()

    logger.info("Reading GTFS feed from %s ...", gtfs_path)
    start = time.perf_counter()
    feed = gk.read_feed(gtfs_path, dist_units="km")
    logger.info("Feed loaded in %.1f seconds.", time.perf_counter() - start)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Use provided metadata_dir or default location
    if metadata_dir is None:
        metadata_dir = Path(gtfs_path).resolve().parent / "metadata"
    else:
        metadata_dir = Path(metadata_dir)

    summary = {
        "agencies": 0,
        "stops": 0,
        "shapes": 0,
        "routes": 0,
        "trips": 0,
        "stop_times": 0,
    }

    original_sync_commit = "on"
    try:
        # Optimize database settings for bulk loading (disable synchronous_commit)
        original_sync_commit = optimize_database_for_bulk_load(session)
        
        # Disable triggers and indexes before bulk loading for maximum performance
        disable_materialized_view_triggers(session)
        disable_indexes(session)
        
        # Determine if RBL mapping should be enabled (Vienna-specific, only if metadata_dir exists)
        enable_rbl = metadata_dir.exists() and metadata_dir.is_dir()
        
        truncate_tables(session)
        summary["agencies"] = load_agencies(session, feed, default_timezone=default_timezone)
        summary["stops"] = load_stops(session, feed, metadata_dir=metadata_dir if enable_rbl else None, enable_rbl_mapping=enable_rbl)
        summary["shapes"] = load_shapes(session, feed, chunk_size, max_shapes)
        summary["routes"] = load_routes(session, feed)
        trips_loaded, stop_times_loaded = load_trips_and_stop_times(session, feed, chunk_size, max_trips)
        summary["trips"] = trips_loaded
        summary["stop_times"] = stop_times_loaded
        
        # Recreate indexes before re-enabling triggers (indexes needed for view refresh)
        recreate_indexes(session)
        
        # Re-enable triggers and refresh materialized view once at the end
        enable_materialized_view_triggers(session)
        
        # Restore database settings
        restore_database_settings(session, original_sync_commit)
        
        logger.info("GTFS import completed: %s", summary)
        record_heartbeat("completed", **summary)
    except Exception as exc:
        logger.error("Error loading GTFS data: %s", exc, exc_info=True)
        session.rollback()
        # Try to restore indexes, triggers, and database settings even on error
        try:
            restore_database_settings(session, original_sync_commit)
            recreate_indexes(session)
            enable_materialized_view_triggers(session)
        except Exception:
            pass
        record_heartbeat("error", message=str(exc))
        raise
    finally:
        session.close()

    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load GTFS data into the database.")
    parser.add_argument("gtfs_path", help="Path to the GTFS zip file.")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=5000,
        help="Number of records to process per batch (default: 5000). Larger chunks = faster but more memory.",
    )
    parser.add_argument(
        "--max-shapes",
        type=int,
        default=None,
        help="Limit the number of shapes to import (useful for testing).",
    )
    parser.add_argument(
        "--max-trips",
        type=int,
        default=None,
        help="Limit the number of trips (and corresponding stop_times) to import.",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Enable test mode (implies max-shapes=200, max-trips=500 unless explicitly provided).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.test_mode:
        if args.max_shapes is None:
            args.max_shapes = 200
        if args.max_trips is None:
            args.max_trips = 500
        logger.info(
            "Test mode enabled: max_shapes=%s, max_trips=%s",
            args.max_shapes,
            args.max_trips,
        )

    if not os.path.exists(args.gtfs_path):
        logger.error("GTFS file not found: %s", args.gtfs_path)
        sys.exit(1)

    load_gtfs_to_db(
        gtfs_path=args.gtfs_path,
        chunk_size=args.chunk_size,
        max_shapes=args.max_shapes,
        max_trips=args.max_trips,
    )




