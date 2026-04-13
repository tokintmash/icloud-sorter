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
