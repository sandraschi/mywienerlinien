"""App-table CRUD on SQLite app.db (no Postgres anywhere in this file)."""

from datetime import datetime, timedelta

import pytest

from frontend.database import db


@pytest.fixture()
def appdb(tmp_path, monkeypatch):
    """Point the shared manager at a scratch app.db (WAL, fresh schema).

    Save/restore: other tests may legitimately init the engines (e.g. via
    initialize_app); isolation means leaving them exactly as found.
    """
    saved = (db.engine, db.session_factory)
    db.engine = None
    db.session_factory = None
    monkeypatch.setenv("APP_DB_PATH", str(tmp_path / "app.db"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db.init_app(None)
    yield db
    if db.engine is not None:
        db.engine.dispose()
    db.engine, db.session_factory = saved


def test_api_keys_cycle(appdb):
    from frontend.api.api_keys import APIKeyManager

    mgr = APIKeyManager(appdb)
    key, obj = mgr.generate_api_key("test", "pytest")
    assert mgr.verify_api_key(key).key_id == obj.key_id
    assert mgr.verify_api_key("bogus") is None
    assert mgr.revoke_api_key(obj.key_id) is True
    assert mgr.verify_api_key(key) is None
    mgr.log_api_request(obj.key_id, "/api/x", "GET", 200, 12)
    stats = mgr.get_usage_statistics(obj.key_id)
    assert stats["total_requests"] == 1
    assert stats["endpoints_used"] == 1


def test_city_seed_and_switch(appdb):
    from frontend.mcp_server.city_manager import CityManager

    cm = CityManager(appdb)
    codes = {c["code"] for c in cm.get_available_cities()}
    assert "vienna" in codes
    assert cm.switch_city("vienna") is True
    assert cm.switch_city("atlantis") is False


def test_notifications_active_window(appdb):
    from frontend.mcp_server.notification_service import get_notification_service

    svc = get_notification_service(appdb, None, None)
    now = datetime.now()
    # Wide margins: writers store naive-local times while SQL windows use
    # UTC datetime('now') — keeps this TZ-robust on any host clock.
    for nid, created, expires in [
        ("active-1", now - timedelta(minutes=10), now + timedelta(hours=1)),
        ("expired-1", now - timedelta(hours=5), now - timedelta(hours=4)),
    ]:
        appdb.execute_query(
            """
            INSERT INTO notifications
            (notification_id, notification_type, priority, title, message,
             line, station, action_url, created_at, expires_at, sent, sent_at)
            VALUES (:nid, 'delay_alert', 2, 't', 'm', 'U1', NULL, NULL,
                    :created, :expires, FALSE, NULL)
            """,
            {"nid": nid, "created": created, "expires": expires},
        )
    active = svc.get_active_notifications()
    assert [n.notification_id for n in active] == ["active-1"]


def test_social_rating_stddev_python(appdb):
    import statistics

    from frontend.mcp_server.social_service import get_social_service

    svc = get_social_service(appdb)
    for user, rating in [("a", 5), ("b", 4), ("c", 3)]:
        appdb.execute_query(
            "INSERT INTO line_ratings (user_id, line, rating) VALUES (:u, 'U1', :r)",
            {"u": user, "r": rating},
        )
    result = svc.get_line_community_rating("U1")
    assert result["total_ratings"] == 3
    assert result["stddev"] == pytest.approx(statistics.stdev([5, 4, 3]))
    assert svc.get_line_community_rating("U9") is None


def test_historical_reliability_python_stats(appdb, tmp_path):
    from frontend.mcp_server.historical_data import HistoricalDataCollector

    collector = HistoricalDataCollector(appdb, storage_dir=tmp_path)
    now = datetime.now()
    for i in range(12):
        appdb.execute_query(
            """
            INSERT INTO historical_vehicles
            (vehicle_id, line, station, delay_minutes, latitude, longitude,
             direction, vehicle_type, timestamp)
            VALUES (:vid, 'U1', 'S', :delay, 48.2, 16.37, 'out', 'metro', :ts)
            """,
            {"vid": f"v{i}", "delay": i, "ts": now - timedelta(minutes=i)},
        )
    stats = collector.get_line_reliability_stats(days=30)
    u1 = stats["U1"]
    assert u1["total_samples"] == 12
    assert u1["median_delay"] == pytest.approx(5.5)
    assert u1["p95_delay"] > u1["median_delay"]
    assert u1["stddev_delay"] > 0
    patterns = collector.analyze_delay_patterns(line="U1")
    assert len(patterns) == 1
    history = collector.get_delay_history(line="U1")
    assert len(history) == 12
    assert isinstance(history[0]["day_of_week"], int)
