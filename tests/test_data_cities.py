"""Tests for per-city feed-data availability (gtfs-mcp cities/ contract)."""

import json

import pytest

from frontend.gtfs_service import data_cities_root, list_data_cities, resolve_data_city


@pytest.fixture()
def data_tree(tmp_path, monkeypatch):
    """Fake repo tree: legacy extracted/ Vienna + one gtfs-mcp export."""
    root = tmp_path / "repo"
    extracted = root / "scripts" / "gtfs_data" / "extracted"
    extracted.mkdir(parents=True)
    (extracted / "stops.txt").write_text("stop_id,stop_name,stop_lat,stop_lon\n")
    cities = root / "scripts" / "gtfs_data" / "cities"
    munich = cities / "munich"
    munich.mkdir(parents=True)
    (munich / "stops.txt").write_text("stop_id,stop_name,stop_lat,stop_lon\n")
    (munich / "manifest.json").write_text(
        json.dumps(
            {
                "feed_id": "munich",
                "exported_at": "2026-10-17T00:00:00",
                "source": "gtfs-mcp depot",
                "files": ["stops.txt"],
                "counts": {"stops": 10, "routes": 2, "trips": 5, "stop_times": 50},
            }
        )
    )
    (cities / "empty").mkdir(parents=True)  # no manifest: not a city
    monkeypatch.setattr("frontend.gtfs_service._REPO_ROOT", root)
    monkeypatch.delenv("PUBLICtransport_GTFS_CITIES", raising=False)
    monkeypatch.delenv("MYWIENERLINIEN_GTFS_CITIES", raising=False)
    return root


def test_env_alias_old_name_still_honored(tmp_path, monkeypatch):
    other = tmp_path / "legacy"
    (other / "graz").mkdir(parents=True)
    ((other / "graz") / "manifest.json").write_text("{}")
    monkeypatch.delenv("PUBLICtransport_GTFS_CITIES", raising=False)
    monkeypatch.setenv("MYWIENERLINIEN_GTFS_CITIES", str(other))
    from frontend.gtfs_service import data_cities_root as _root

    assert _root() == other


def test_vienna_resolves_to_legacy_extracted(data_tree):
    resolved = resolve_data_city("vienna")
    assert resolved is not None
    assert resolved.name == "extracted"


def test_vienna_missing_data_resolves_none(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    monkeypatch.setattr("frontend.gtfs_service._REPO_ROOT", root)
    monkeypatch.delenv("PUBLICtransport_GTFS_CITIES", raising=False)
    monkeypatch.delenv("MYWIENERLINIEN_GTFS_CITIES", raising=False)
    assert resolve_data_city("vienna") is None


def test_export_city_resolves_with_manifest(data_tree):
    resolved = resolve_data_city("munich")
    assert resolved is not None
    assert resolved.name == "munich"


def test_dir_without_manifest_is_not_a_city(data_tree):
    assert resolve_data_city("empty") is None


@pytest.mark.parametrize("bad", ["", "../x", "..", "München", "a/b", "."])
def test_traversal_and_bad_ids_rejected(data_tree, bad):
    assert resolve_data_city(bad) is None


def test_env_override_repoints_cities_root(tmp_path, monkeypatch):
    other = tmp_path / "alt"
    (other / "graz").mkdir(parents=True)
    ((other / "graz") / "manifest.json").write_text("{}")
    monkeypatch.setenv("PUBLICtransport_GTFS_CITIES", str(other))
    assert data_cities_root() == other
    assert resolve_data_city("graz") is not None


def test_list_data_cities_merges_legacy_and_exports(data_tree):
    cities = {c["id"]: c for c in list_data_cities()}
    assert cities["vienna"]["source"] == "extracted-legacy"
    assert cities["munich"]["source"] == "gtfs-mcp-export"
    assert cities["munich"]["counts"]["stops"] == 10
    assert "empty" not in cities


def test_api_cities_reports_data_loaded(app_client, tmp_path, monkeypatch):
    """GET /api/cities flags gtfs-mcp exports the switcher UI can offer."""
    cities = tmp_path / "cities"
    munich = cities / "munich"
    munich.mkdir(parents=True)
    (munich / "manifest.json").write_text(json.dumps({"feed_id": "munich", "counts": {}}))
    monkeypatch.setenv("PUBLICtransport_GTFS_CITIES", str(cities))
    response = app_client.get("/api/cities")
    assert response.status_code == 200
    entries = {c["key"]: c for c in response.json()["cities"]}
    assert entries["munich"]["code"] == "munich"
    assert entries["munich"]["data_loaded"] is True
    assert entries["munich"]["data_source"] == "gtfs-mcp-export"
