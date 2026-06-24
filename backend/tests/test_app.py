from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.app import app


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_api_404(client):
    resp = client.get("/api/nonexistent")
    assert resp.status_code == 404
    assert resp.json()["error"] == "not_found"


def test_health_endpoint(client):
    resp = client.get("/api/app/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_quit_endpoint_dev_mode(client):
    resp = client.post("/api/app/quit")
    assert resp.status_code == 409
    assert resp.json()["error"] == "not_available"


def test_expired_build_leaves_status_health_and_quit_available(client):
    with patch("backend.app.is_app_expired", return_value=True), \
         patch(
             "backend.beta.get_beta_status",
             return_value={"is_beta": True, "expired": True, "expires_on": "2026-01-01", "days_remaining": 0},
         ):
        beta_resp = client.get("/api/app/beta")
        health_resp = client.get("/api/app/health")
        quit_resp = client.post("/api/app/quit")

    assert beta_resp.status_code == 200
    assert beta_resp.json()["expired"] is True
    assert health_resp.status_code == 200
    assert health_resp.json() == {"ok": True}
    assert quit_resp.status_code == 409
    assert quit_resp.json()["error"] == "not_available"


def test_expired_build_blocks_protected_routes_before_work(client):
    with patch("backend.app.is_app_expired", return_value=True), \
         patch("backend.routers.auth.icloud_service.login") as login, \
         patch("backend.routers.albums.icloud_service.get_albums") as get_albums, \
         patch("backend.routers.sort.sorter_service.start") as start_sort, \
         patch("backend.routers.settings.save_settings") as save_settings:
        responses = [
            client.post("/api/auth/login", json={"apple_id": "test@example.com", "password": "pass"}),
            client.get("/api/albums"),
            client.post("/api/sort/start", json={"album_ids": ["a1"]}),
            client.put("/api/settings", json={"icloud_folder": "C:/Photos"}),
        ]

    for resp in responses:
        assert resp.status_code == 403
        assert resp.json() == {
            "error": "app_expired",
            "message": "This beta has expired. Contact the author of the app to get an up-to-date version.",
        }
    login.assert_not_called()
    get_albums.assert_not_called()
    start_sort.assert_not_called()
    save_settings.assert_not_called()


def test_quit_endpoint_desktop_mode(client):
    called = []
    from backend import lifecycle

    lifecycle.register_shutdown_callback(lambda: called.append(True))
    try:
        resp = client.post("/api/app/quit")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
        assert called == [True]
    finally:
        lifecycle._shutdown_callbacks.clear()


def test_spa_fallback_serves_index(client, tmp_path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html>app</html>")

    with patch("backend.app.FRONTEND_DIST", dist_dir):
        resp = client.get("/some-route")
    assert resp.status_code == 200
    assert "<html>app</html>" in resp.text


def test_spa_fallback_no_frontend(client):
    with patch("backend.app.FRONTEND_DIST", Path("/nonexistent/path")):
        resp = client.get("/some-route")
    assert resp.status_code == 404
    assert resp.json()["error"] == "not_found"
