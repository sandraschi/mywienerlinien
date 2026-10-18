"""GTFS static reads against a gtfs-mcp snapshot (no Postgres required).

The snapshot file below mirrors the Phase 1 contract DDL
(gtfs-mcp/src/gtfs_mcp/core/snapshot.py) at small scale; the methods under
test live in frontend/database.py and must behave identically on SQLite.
"""

import sqlite3

import pytest

from frontend.database import db, resolve_snapshot_path

DDL = """
CREATE TABLE agencies(agency_id TEXT PRIMARY KEY, agency_name TEXT);
CREATE TABLE stops(
    stop_id TEXT PRIMARY KEY, stop_code TEXT, stop_name TEXT,
    stop_lat REAL, stop_lon REAL, zone_id TEXT,
    parent_station TEXT, location_type INTEGER, wheelchair_boarding INTEGER
);
CREATE TABLE routes(
    route_id TEXT PRIMARY KEY, agency_id TEXT, route_short_name TEXT,
    route_long_name TEXT, route_type INTEGER, route_color TEXT,
    route_text_color TEXT
);
CREATE TABLE trips(
    trip_id TEXT PRIMARY KEY, route_id TEXT, service_id TEXT,
    trip_headsign TEXT, direction_id INTEGER, shape_id TEXT
);
CREATE TABLE stop_times(
    trip_id TEXT, arrival_time TEXT, departure_time TEXT,
    stop_id TEXT, stop_sequence INTEGER
);
CREATE INDEX idx_stop_times_stop ON stop_times(stop_id);
CREATE INDEX idx_stop_times_trip ON stop_times(trip_id);
CREATE INDEX idx_trips_route ON trips(route_id);
CREATE INDEX idx_trips_shape ON trips(shape_id);
CREATE TABLE shapes(
    shape_id TEXT, shape_pt_lat REAL, shape_pt_lon REAL, shape_pt_sequence INTEGER
);
CREATE INDEX idx_shapes_id ON shapes(shape_id, shape_pt_sequence);
"""


@pytest.fixture()
def snap_db(tmp_path):
    """Minimal Vienna-like snapshot wired into the shared db singleton."""
    path = tmp_path / "vienna.db"
    con = sqlite3.connect(path)
    con.executescript(DDL)
    con.execute("INSERT INTO agencies VALUES ('1', 'Wiener Linien')")
    con.executemany(
        "INSERT INTO stops VALUES (?,?,?,?,?,?,?,?,?)",
        [
            ("S1", "5001", "Stephansplatz", 48.2082, 16.3738, "100", None, 1, 1),
            ("S2", "5002", "Stephansplatz U", 48.2080, 16.3730, "100", "S1", 0, 1),
            ("S3", "5003", "Praterstern", 48.2180, 16.3910, "100", None, 0, 1),
        ],
    )
    con.executemany(
        "INSERT INTO routes VALUES (?,?,?,?,?,?,?)",
        [("R1", "1", "U1", "Leopoldau-Oberlaa", 1, "FF0000", "FFFFFF")],
    )
    con.executemany(
        "INSERT INTO trips VALUES (?,?,?,?,?,?)",
        [("T1", "R1", "1", "Leopoldau", 0, "SH1"), ("T2", "R1", "1", "Oberlaa", 1, "SH1")],
    )
    con.executemany(
        "INSERT INTO stop_times VALUES (?,?,?,?,?)",
        [
            ("T1", "08:00:00", "08:01:00", "S2", 1),
            ("T1", "08:10:00", "08:11:00", "S3", 2),
            ("T2", "08:05:00", "08:06:00", "S3", 1),
            ("T2", "08:15:00", "08:16:00", "S2", 2),
        ],
    )
    con.executemany(
        "INSERT INTO shapes VALUES (?,?,?,?)",
        [("SH1", 48.20, 16.37, 1), ("SH1", 48.21, 16.38, 2), ("SH1", 48.22, 16.39, 3)],
    )
    con.commit()
    con.close()
    saved = (db.snapshot_engine, db.snapshot_factory)
    db.snapshot_engine = None
    db.snapshot_factory = None
    assert db.snapshot_engine is None
    db.init_snapshot(path)
    yield db
    if db.snapshot_engine is not None:
        db.snapshot_engine.dispose()
    db.snapshot_engine, db.snapshot_factory = saved


def test_resolve_snapshot_path_prefers_env(tmp_path, monkeypatch):
    target = tmp_path / "custom.db"
    target.write_text("x")
    monkeypatch.setenv("GTFS_SNAPSHOT_PATH", str(target))
    assert resolve_snapshot_path() == target


def test_resolve_snapshot_path_missing_file_is_none(tmp_path, monkeypatch):
    monkeypatch.setenv("GTFS_SNAPSHOT_PATH", str(tmp_path / "nope.db"))
    assert resolve_snapshot_path() is None


def test_init_snapshot_refuses_without_file(tmp_path, monkeypatch):
    saved = (db.snapshot_engine, db.snapshot_factory)
    db.snapshot_engine = None
    db.snapshot_factory = None
    try:
        monkeypatch.setenv("GTFS_SNAPSHOT_PATH", str(tmp_path / "nope.db"))
        with pytest.raises(RuntimeError, match="GTFS snapshot not found"):
            db.init_snapshot()
        assert db.snapshot_engine is None
    finally:
        db.snapshot_engine, db.snapshot_factory = saved


def test_get_routes(snap_db):
    routes = snap_db.get_routes()
    assert len(routes) == 1
    assert routes[0]["agency_name"] == "Wiener Linien"
    assert int(routes[0]["trip_count"]) == 2
    assert int(routes[0]["stop_count"]) == 2


def test_get_line_overview(snap_db):
    ov = snap_db.get_line_overview("u1")
    assert ov["line"] == "U1"
    assert ov["route_type_name"] == "Metro"
    assert ov["color"] == "#FF0000"
    assert ov["trip_count"] == 2


def test_get_line_route_data_shapes(snap_db):
    data = snap_db.get_line_route_data("U1")
    assert data["line"] == "U1"
    assert len(data["segments"]) == 1
    seg = data["segments"][0]
    assert seg["shape_id"] == "SH1"
    assert seg["coordinates"][0] == [48.20, 16.37]
    assert len(seg["coordinates"]) == 3
    assert len(data["stops"]) >= 2


def test_get_line_stations_rbl(snap_db):
    stations = snap_db.get_line_stations("U1")
    by_id = {s["id"]: s for s in stations}
    assert by_id["S2"]["rbl"] == "5002"
    assert by_id["S2"]["lat"] == pytest.approx(48.2080)


def test_get_stations_types(snap_db):
    stations = {s["id"]: s for s in snap_db.get_stations()}
    assert stations["S1"]["type"] == "station"
    assert stations["S1"]["rbl"] == "5001"
    assert stations["S3"]["type"] == "accessible"
    assert set(stations) == {"S1", "S3"}  # child platform S2 folds into its parent


def test_get_stops_normalizes_lists(snap_db):
    stops = {s["stop_id"]: s for s in snap_db.get_stops()}
    assert stops["S2"]["route_numbers"] == ["U1"]
    assert stops["S2"]["route_types"] == [1]


def test_get_route_stops_ordered(snap_db):
    stops = snap_db.get_route_stops("R1", direction_id=0)
    assert [s["stop_id"] for s in stops] == ["S2", "S3"]
