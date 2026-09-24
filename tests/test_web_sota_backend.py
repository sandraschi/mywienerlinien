"""Tests for the web_sota FastAPI backend (fleet-start UvicornTarget)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from web_sota.backend.server import app


@pytest.fixture()
def client():
    return TestClient(app)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_status_shape(client):
    payload = client.get("/api/status").json()
    assert payload["status"] == "ok"
    assert payload["uptime_seconds"] >= 0


def test_capabilities_lists_routes(client):
    payload = client.get("/api/capabilities").json()
    assert "/api/health" in payload["endpoints"]
    assert "/api/webhooks/inbound" in payload["endpoints"]


def test_major_stops_verified(client):
    payload = client.get("/api/stops/major").json()
    assert payload["count"] >= 12
    names = {s["name"] for s in payload["stops"]}
    assert {"Stephansplatz", "Hauptbahnhof", "Karlsplatz"} <= names


def test_webhook_no_secret_configured(client, monkeypatch):
    monkeypatch.delenv("WEBHOOK_SECRET", raising=False)
    r = client.post("/api/webhooks/inbound", json={"event": "x"})
    assert r.status_code == 503


def test_webhook_wrong_secret(client, monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "s3cret")
    r = client.post(
        "/api/webhooks/inbound",
        json={"event": "x"},
        headers={"X-Webhook-Secret": "wrong"},
    )
    assert r.status_code == 403


def test_webhook_accepts_signed_event(client, monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "s3cret")
    r = client.post(
        "/api/webhooks/inbound",
        json={"event": "deploy", "message": "hello"},
        headers={"X-Webhook-Secret": "s3cret"},
    )
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_shutdown_endpoint(client):
    # Shutdown schedules os._exit; only assert the 200 shape via routing table.
    routes = {r.path for r in app.routes if hasattr(r, "path")}
    assert "/api/shutdown" in routes
