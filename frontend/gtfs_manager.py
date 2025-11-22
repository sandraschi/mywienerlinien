"""GTFS data lifecycle management for the Wiener Linien application."""

from __future__ import annotations

import importlib
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

try:
    from .database import db
    from .data_loader import data_loader
except ImportError:  # pragma: no cover - runtime fallback when package context missing
    from database import db  # type: ignore
    from data_loader import data_loader  # type: ignore

try:
    download_module = importlib.import_module("scripts.download_wienerlinien_data")
    load_module = importlib.import_module("scripts.load_gtfs_to_db")
    city_config_module = importlib.import_module("scripts.city_config")
except ImportError:  # pragma: no cover - defensive fallback
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    try:
        download_module = importlib.import_module("scripts.download_wienerlinien_data")
        load_module = importlib.import_module("scripts.load_gtfs_to_db")
        city_config_module = importlib.import_module("scripts.city_config")
    except ImportError as inner_error:
        logger = logging.getLogger(__name__)
        logger.error("GTFS manager import error: %s", inner_error, exc_info=True)
        raise RuntimeError(
            "GTFS manager could not import supporting scripts"
        ) from inner_error

DATA_DIR = download_module.DATA_DIR  # Used for metadata storage
GTFS_DIR = download_module.GTFS_DIR
GTFS_EXTRACT_DIR = download_module.GTFS_EXTRACT_DIR
GTFS_MAX_AGE_DAYS = download_module.GTFS_MAX_AGE_DAYS
get_city_config = city_config_module.get_city_config
get_gtfs_filename = city_config_module.get_gtfs_filename
download_file = download_module.download_file
extract_gtfs = download_module.extract_gtfs
is_gtfs_fresh = download_module.is_gtfs_fresh
load_gtfs_to_db = load_module.load_gtfs_to_db

# Default configuration (can be overridden via environment)
DEFAULT_CITY = os.getenv("GTFS_CITY", "vienna")
DEFAULT_GTFS_URL = os.getenv("GTFS_URL", "https://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/gtfs.zip")


def _now_utc() -> datetime:
    return datetime.utcnow().replace(tzinfo=None)


class GTFSPipelineError(RuntimeError):
    """Fatal GTFS pipeline failure."""


class GTFSManager:
    """Downloads, processes, and refreshes GTFS data on demand."""

    def __init__(self) -> None:
        self.logger = logging.getLogger('gtfs_manager')
        self.test_mode = os.getenv('WIENER_LINIEN_TEST_MODE', '').strip() == '1'
        self.refresh_interval = timedelta(
            days=int(os.getenv('GTFS_REFRESH_INTERVAL_DAYS', str(GTFS_MAX_AGE_DAYS)))
        )
        self.metadata_path = Path(DATA_DIR) / 'gtfs_metadata.json'
        self._lock = threading.Lock()
        self._background_thread: threading.Thread | None = None
        
        # City configuration
        city_name = os.getenv('GTFS_CITY', DEFAULT_CITY)
        gtfs_url_env = os.getenv('GTFS_URL')
        
        if gtfs_url_env:
            self.city_config = None
            self.gtfs_url = gtfs_url_env
            self.gtfs_zip = GTFS_DIR / get_gtfs_filename("custom")
        else:
            self.city_config = get_city_config(city_name)
            if self.city_config:
                self.gtfs_url = self.city_config.gtfs_url
                self.gtfs_zip = GTFS_DIR / get_gtfs_filename(city_name)
            else:
                # Fallback to default
                self.city_config = get_city_config(DEFAULT_CITY)
                self.gtfs_url = DEFAULT_GTFS_URL
                self.gtfs_zip = GTFS_DIR / get_gtfs_filename(DEFAULT_CITY)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ensure_data_ready(self) -> None:
        """Ensure GTFS assets exist and schedule background refreshes."""

        if self.test_mode:
            self.logger.info('Test mode detected; skipping GTFS bootstrap.')
            return

        with self._lock:
            if self._needs_refresh(check_database=True):
                self.logger.info('GTFS data is missing or stale. Starting bootstrap…')
                self._run_pipeline(force_download=True)
            else:
                self.logger.info('Existing GTFS data is fresh.')

        self._start_background_refresh()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _start_background_refresh(self) -> None:
        if self.test_mode or self._background_thread:
            return

        def refresher() -> None:
            while True:
                time.sleep(self.refresh_interval.total_seconds())
                with self._lock:
                    if self._needs_refresh(check_database=False):
                        self.logger.info('Scheduled GTFS refresh triggered.')
                        try:
                            self._run_pipeline(force_download=False)
                        except Exception:
                            self.logger.exception('Scheduled GTFS refresh failed.')

        thread = threading.Thread(target=refresher, name='gtfs-refresh', daemon=True)
        thread.start()
        self._background_thread = thread

    def _needs_refresh(self, *, check_database: bool) -> bool:
        if check_database and not self._database_has_routes():
            return True

        if not self.gtfs_zip.exists():
            return True

        if not is_gtfs_fresh(self.gtfs_zip):
            return True

        metadata = self._load_metadata()
        if not metadata:
            return True

        last_updated_str = metadata.get('last_updated')
        if not last_updated_str:
            return True

        try:
            last_updated = datetime.fromisoformat(last_updated_str)
        except ValueError:
            return True

        return _now_utc() - last_updated > self.refresh_interval

    def _database_has_routes(self) -> bool:
        try:
            result = db.execute_query('SELECT COUNT(*) AS count FROM routes')
            return bool(result and result[0].get('count', 0) > 0)
        except Exception as exc:  # pragma: no cover - safety net
            self.logger.warning('Unable to count routes: %s', exc)
            return False

    def _run_pipeline(self, *, force_download: bool) -> None:
        GTFS_DIR.mkdir(parents=True, exist_ok=True)

        self._download_gtfs(force=force_download)
        self._extract_gtfs()
        self._load_database()
        # Markdown generation removed - data now read directly from database
        self._write_metadata()
        data_loader.clear_cache()

    def _download_gtfs(self, *, force: bool) -> None:
        success, message = download_file(self.gtfs_url, self.gtfs_zip, force=force)
        if not success:
            raise GTFSPipelineError(f'Download failed: {message}')

    def _extract_gtfs(self) -> None:
        success, message = extract_gtfs(self.gtfs_zip, GTFS_EXTRACT_DIR, force=True)
        if not success:
            raise GTFSPipelineError(f'Extraction failed: {message}')

    def _load_database(self) -> None:
        try:
            # Pass metadata_dir only if RBL mapping is enabled (Vienna-specific)
            metadata_dir = None
            if self.city_config and self.city_config.enable_rbl_mapping:
                metadata_dir = GTFS_DIR
            
            load_gtfs_to_db(str(self.gtfs_zip), metadata_dir=metadata_dir)
        except Exception as exc:
            raise GTFSPipelineError(f'Failed to load GTFS into database: {exc}') from exc

    # Markdown generation removed - data now read directly from database
    # def _generate_markdown(self) -> None:
    #     """Legacy method - no longer needed since we read directly from database."""

    def _load_metadata(self) -> Dict[str, Any] | None:
        if not self.metadata_path.exists():
            return None
        try:
            return json.loads(self.metadata_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return None

    def _write_metadata(self) -> None:
        metadata = {
            'last_updated': _now_utc().isoformat(),
            'gtfs_zip': str(self.gtfs_zip),
            'gtfs_url': self.gtfs_url,
            'city': self.city_config.name if self.city_config else 'custom',
            'timezone': self.city_config.timezone if self.city_config else 'UTC',
            'refresh_interval_days': self.refresh_interval.days,
        }
        self.metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')


manager = GTFSManager()

