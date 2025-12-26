"""
Utilities for enriching GTFS stop records with Wiener Linien RBL numbers.

This module downloads the public OGD "Haltestellen" and "Steige" datasets,
derives a mapping between GTFS stops (identified by stop_id/coordinates) and
the corresponding RBL monitor numbers that are required for the realtime API.
"""

from __future__ import annotations

import csv
import logging
import math
import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

OGD_BASE_URL = "https://www.data.wien.gv.at/csv/"
HALTESTELLEN_FILE = "wienerlinien-ogd-haltestellen.csv"
STEIGE_FILE = "wienerlinien-ogd-steige.csv"
DEFAULT_TIMEOUT = 30


class MetadataDownloadError(RuntimeError):
    """Raised when required OGD datasets cannot be downloaded and no cache exists."""


@dataclass
class Haltestelle:
    haltestellen_id: str
    name: str
    diva: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    norm_name: str


@dataclass
class Steig:
    haltestellen_id: str
    rbl: str
    lat: Optional[float]
    lon: Optional[float]


def _normalize_directory(cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _download_dataset(filename: str, cache_dir: Path, logger: logging.Logger) -> Path:
    cache_dir = _normalize_directory(cache_dir)
    target_path = cache_dir / filename
    url = f"{OGD_BASE_URL}{filename}"

    try:
        response = requests.get(url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        target_path.write_bytes(response.content)
        logger.info("Downloaded %s (%d bytes)", filename, len(response.content))
    except Exception as exc:  # noqa: BLE001 - any failure should fall back to cache
        if target_path.exists():
            logger.warning(
                "Failed to download %s from %s (%s); using cached copy",
                filename,
                url,
                exc,
            )
        else:
            raise MetadataDownloadError(
                f"Unable to download required dataset {filename} from {url}"
            ) from exc

    return target_path


def _read_csv_dicts(path: Path, logger: logging.Logger) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="iso-8859-1", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=";")
            return [row for row in reader]
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to read CSV file %s: %s", path, exc)
        raise


def _normalize_name(value: str) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _safe_float(value: Optional[str]) -> Optional[float]:
    if value in (None, "", "NULL"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_haltestellen(cache_dir: Path, logger: logging.Logger) -> list[Haltestelle]:
    path = _download_dataset(HALTESTELLEN_FILE, cache_dir, logger)
    raw_rows = _read_csv_dicts(path, logger)
    haltestellen: list[Haltestelle] = []

    for row in raw_rows:
        haltestellen_id = row.get("HALTESTELLEN_ID")
        if not haltestellen_id:
            continue
        name = row.get("NAME", "").strip()
        haltestellen.append(
            Haltestelle(
                haltestellen_id=haltestellen_id,
                name=name,
                diva=(row.get("DIVA") or "").strip() or None,
                lat=_safe_float(row.get("WGS84_LAT")),
                lon=_safe_float(row.get("WGS84_LON")),
                norm_name=_normalize_name(name),
            )
        )

    logger.info("Loaded %d haltestellen entries", len(haltestellen))
    return haltestellen


def _load_steige(cache_dir: Path, logger: logging.Logger) -> list[Steig]:
    path = _download_dataset(STEIGE_FILE, cache_dir, logger)
    raw_rows = _read_csv_dicts(path, logger)
    steige: list[Steig] = []

    for row in raw_rows:
        haltestellen_id = row.get("FK_HALTESTELLEN_ID")
        rbl = (row.get("RBL_NUMMER") or "").strip()
        if not haltestellen_id or not rbl:
            continue
        steige.append(
            Steig(
                haltestellen_id=haltestellen_id,
                rbl=rbl,
                lat=_safe_float(row.get("STEIG_WGS84_LAT")),
                lon=_safe_float(row.get("STEIG_WGS84_LON")),
            )
        )

    logger.info("Loaded %d steige entries", len(steige))
    return steige


def _build_haltestellen_index(
    haltestellen: Sequence[Haltestelle],
) -> tuple[dict[str, list[Haltestelle]], list[Haltestelle]]:
    by_name: dict[str, list[Haltestelle]] = defaultdict(list)
    for entry in haltestellen:
        if entry.norm_name:
            by_name[entry.norm_name].append(entry)
    return by_name, list(haltestellen)


def _distance(a_lat: Optional[float], a_lon: Optional[float], b_lat: float, b_lon: float) -> float:
    if a_lat is None or a_lon is None:
        return math.inf
    return abs(a_lat - b_lat) + abs(a_lon - b_lon)


def _match_haltestelle(
    stop_name: str,
    stop_lat: Optional[float],
    stop_lon: Optional[float],
    haltestellen_by_name: dict[str, list[Haltestelle]],
    haltestellen: Sequence[Haltestelle],
) -> Optional[Haltestelle]:
    norm_name = _normalize_name(stop_name)
    candidates = haltestellen_by_name.get(norm_name, [])

    best: Optional[Haltestelle] = None
    best_distance = math.inf

    def consider(entry: Haltestelle) -> None:
        nonlocal best, best_distance
        distance = _distance(entry.lat, entry.lon, stop_lat or 0.0, stop_lon or 0.0)
        if distance < best_distance:
            best = entry
            best_distance = distance

    for entry in candidates:
        consider(entry)

    # Fallback: nearest by coordinates if name match missing or too imprecise
    if best is None or best_distance > 0.01:
        for entry in haltestellen:
            consider(entry)

    if best_distance > 0.02:  # ~2 km threshold - avoid obviously wrong matches
        return None

    return best


def build_stop_rbl_mapping(
    gtfs_stops: Iterable[dict[str, object]],
    cache_dir: Path,
    logger: logging.Logger,
) -> dict[str, dict[str, object]]:
    """
    Return mapping from GTFS stop_id to RBL metadata.

    Args:
        gtfs_stops: Iterable of dicts that contain at least stop_id, stop_name and
            latitude/longitude fields (`lat` and `lon` or `stop_lat`, `stop_lon`).
        cache_dir: Directory used to cache downloaded datasets.
        logger: Logger instance for diagnostics.

    Returns:
        Dictionary keyed by stop_id with entries:
            {
              "rbl_numbers": [...],
              "diva": Optional[str],
              "haltestellen_id": Optional[str],
            }
    """

    haltestellen = _load_haltestellen(cache_dir, logger)
    steige = _load_steige(cache_dir, logger)

    haltestellen_by_name, haltestellen_list = _build_haltestellen_index(haltestellen)

    rbl_by_haltestelle: dict[str, list[str]] = defaultdict(list)
    for entry in steige:
        if entry.haltestellen_id and entry.rbl:
            rbl_by_haltestelle[entry.haltestellen_id].append(entry.rbl)

    mapping: dict[str, dict[str, object]] = {}
    matched = 0
    unmatched = 0

    for stop in gtfs_stops:
        stop_id = str(stop.get("stop_id") or "").strip()
        if not stop_id:
            continue

        lat = stop.get("lat")
        if lat is None:
            lat = stop.get("stop_lat")
        lon = stop.get("lon")
        if lon is None:
            lon = stop.get("stop_lon")
        try:
            lat_f = float(lat) if lat not in (None, "", "NULL") else None
            lon_f = float(lon) if lon not in (None, "", "NULL") else None
        except (TypeError, ValueError):
            lat_f = None
            lon_f = None

        stop_name = str(stop.get("stop_name") or "").strip()
        haltestelle = _match_haltestelle(
            stop_name,
            lat_f,
            lon_f,
            haltestellen_by_name,
            haltestellen_list,
        )

        if not haltestelle:
            unmatched += 1
            continue

        rbls = sorted(set(rbl_by_haltestelle.get(haltestelle.haltestellen_id, [])))

        mapping[stop_id] = {
            "rbl_numbers": rbls,
            "diva": haltestelle.diva,
            "haltestellen_id": haltestelle.haltestellen_id,
            "matched_name": haltestelle.name,
            "distance": (
                None
                if lat_f is None
                or lon_f is None
                or haltestelle.lat is None
                or haltestelle.lon is None
                else _distance(haltestelle.lat, haltestelle.lon, lat_f, lon_f)
            ),
        }
        matched += 1

    logger.info(
        "Mapped %d GTFS stops to RBL metadata (%d unmatched)",
        matched,
        unmatched,
    )
    return mapping


__all__ = [
    "MetadataDownloadError",
    "build_stop_rbl_mapping",
]
