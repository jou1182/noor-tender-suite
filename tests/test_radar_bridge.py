# -*- coding: utf-8 -*-
"""Tests for the Tender Radar REST bridge (app/api/v1/endpoints/radar.py)."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from app.main import app
    return TestClient(app)


class _FakeRadarHandler(BaseHTTPRequestHandler):
    """Minimal stand-in for the vendored Node sync service (port 4318 API shape)."""

    def log_message(self, *args):  # silence test output
        pass

    def _send(self, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send({
                "online": True,
                "serviceVersion": "test",
                "state": {"phase": "idle", "message": "جاهز"},
                "database": {"online": True, "schemaVersion": 10},
            })
        elif self.path == "/status":
            self._send({"phase": "idle", "syncing": False, "message": "جاهز"})
        elif self.path == "/tenders":
            self._send({
                "lastSyncAt": None, "checked": 0, "regions": 0,
                "newItems": 0, "changedItems": 0, "items": [],
            })
        elif self.path == "/dashboard/regions":
            self._send({"regions": []})
        else:
            self.send_response(404)
            self.end_headers()


@pytest.fixture()
def fake_radar(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), _FakeRadarHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("NOOR_RADAR_URL", f"http://127.0.0.1:{port}")
    # القيمة تُقرأ عند استيراد الوحدة — أعد تحميلها لالتقاط المتغير
    import app.api.v1.endpoints.radar as radar_module
    monkeypatch.setattr(radar_module, "RADAR_BASE", f"http://127.0.0.1:{port}")
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()


class TestRadarBridgeOffline:
    """When the vendored service is not running, the bridge degrades gracefully."""

    def test_health_offline_shape(self, client, monkeypatch):
        import app.api.v1.endpoints.radar as radar_module
        monkeypatch.setattr(radar_module, "RADAR_BASE", "http://127.0.0.1:9")  # closed port
        r = client.get("/api/v1/radar/health")
        assert r.status_code == 200
        body = r.json()
        assert body["online"] is False
        assert "الرادار" in body["message"]

    def test_status_offline_shape(self, client, monkeypatch):
        import app.api.v1.endpoints.radar as radar_module
        monkeypatch.setattr(radar_module, "RADAR_BASE", "http://127.0.0.1:9")
        r = client.get("/api/v1/radar/status")
        assert r.status_code == 200
        assert r.json()["online"] is False

    def test_tenders_offline_shape(self, client, monkeypatch):
        import app.api.v1.endpoints.radar as radar_module
        monkeypatch.setattr(radar_module, "RADAR_BASE", "http://127.0.0.1:9")
        r = client.get("/api/v1/radar/tenders")
        assert r.status_code == 200
        assert r.json()["online"] is False

    def test_regions_offline_shape(self, client, monkeypatch):
        import app.api.v1.endpoints.radar as radar_module
        monkeypatch.setattr(radar_module, "RADAR_BASE", "http://127.0.0.1:9")
        r = client.get("/api/v1/radar/regions")
        assert r.status_code == 200
        assert r.json()["online"] is False


class TestRadarBridgeOnline:
    """When the service answers, the bridge passes its payload through."""

    def test_health_online(self, client, fake_radar):
        r = client.get("/api/v1/radar/health")
        assert r.status_code == 200
        body = r.json()
        assert body["online"] is True
        assert body["database"]["online"] is True

    def test_status_online(self, client, fake_radar):
        r = client.get("/api/v1/radar/status")
        assert r.status_code == 200
        body = r.json()
        assert body["online"] is True
        assert body["phase"] == "idle"

    def test_tenders_online(self, client, fake_radar):
        r = client.get("/api/v1/radar/tenders")
        assert r.status_code == 200
        body = r.json()
        assert body["online"] is True
        assert body["items"] == []

    def test_regions_online(self, client, fake_radar):
        r = client.get("/api/v1/radar/regions")
        assert r.status_code == 200
        assert r.json()["online"] is True
