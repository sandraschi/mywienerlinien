import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure we can import project modules when run in container
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR / "frontend") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "frontend"))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def _parse_int(value: str, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def main() -> int:
    # Config via env vars
    refresh_days = _parse_int(os.getenv("GTFS_REFRESH_DAYS", "7"), 7)
    log_dir = Path(os.getenv("GTFS_LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    marker_path = log_dir / "gtfs_last_success.txt"

    gtfs_path = os.getenv(
        "GTFS_ZIP_PATH", str(BASE_DIR / "scripts" / "gtfs_data" / "wienerlinien-gtfs.zip")
    )

    # Optional force refresh
    force = os.getenv("GTFS_FORCE_REFRESH", "0").lower() in ("1", "true", "yes")

    # Check staleness
    is_stale = True
    if marker_path.exists():
        try:
            ts_str = marker_path.read_text(encoding="utf-8").strip()
            last_dt = datetime.fromisoformat(ts_str)
            if last_dt > datetime.utcnow() - timedelta(days=refresh_days):
                is_stale = False
        except Exception:
            is_stale = True

    if not force and not is_stale:
        print(
            f"[GTFS] Up-to-date (last success: {marker_path.read_text(encoding='utf-8').strip()}). Skipping reload."
        )
        return 0

    print(f"[GTFS] Running import (reason: {'force' if force else f'stale>{refresh_days}d'})")

    # Run the loader
    try:
        # Import here to avoid overhead when skipping
        from scripts.load_gtfs_to_db import load_gtfs_to_db, record_heartbeat

        record_heartbeat("scheduled_start", refresh_days=refresh_days, force=force)
        # Use optimized chunk size (default 5000, can override via env var)
        chunk_size = _parse_int(os.getenv("GTFS_CHUNK_SIZE", "5000"), 5000)
        summary = load_gtfs_to_db(
            gtfs_path=gtfs_path,
            chunk_size=chunk_size,
            max_shapes=None,
            max_trips=None,
        )
        record_heartbeat("scheduled_complete", **summary)

        # Write marker
        marker_path.write_text(datetime.utcnow().isoformat(timespec="seconds"), encoding="utf-8")
        print("[GTFS] Import completed and marker updated.")
        return 0
    except Exception as exc:
        print(f"[GTFS] Import failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
