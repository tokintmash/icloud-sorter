import json
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.app import app


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# --- Auth ---

@patch("backend.routers.auth.icloud_service")
def test_login_success(mock_svc, client):
    mock_svc.login.return_value = {"authenticated": True, "requires_2fa": False}
    resp = client.post("/api/auth/login", json={"apple_id": "test@apple.com", "password": "pass"})
    assert resp.status_code == 200
    assert resp.json()["authenticated"] is True


@patch("backend.routers.auth.icloud_service")
def test_login_invalid_credentials(mock_svc, client):
    mock_svc.login.return_value = {"error": "invalid_credentials", "message": "Bad creds"}
    resp = client.post("/api/auth/login", json={"apple_id": "bad", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["error"] == "invalid_credentials"


@patch("backend.routers.auth.icloud_service")
def test_login_requires_2fa(mock_svc, client):
    mock_svc.login.return_value = {"authenticated": False, "requires_2fa": True}
    resp = client.post("/api/auth/login", json={"apple_id": "test@apple.com", "password": "pass"})
    assert resp.status_code == 200
    assert resp.json()["requires_2fa"] is True


@patch("backend.routers.auth.icloud_service")
def test_2fa_success(mock_svc, client):
    mock_svc.validate_2fa.return_value = {"authenticated": True}
    resp = client.post("/api/auth/2fa", json={"code": "123456"})
    assert resp.status_code == 200
    assert resp.json()["authenticated"] is True


@patch("backend.routers.auth.icloud_service")
def test_2fa_invalid_code(mock_svc, client):
    mock_svc.validate_2fa.return_value = {"error": "2fa_failed", "message": "Invalid code"}
    resp = client.post("/api/auth/2fa", json={"code": "000000"})
    assert resp.status_code == 401
    assert resp.json()["error"] == "2fa_failed"


@patch("backend.routers.auth.icloud_service")
def test_session(mock_svc, client):
    mock_svc.get_session_status.return_value = {"authenticated": True, "apple_id": "test@apple.com", "requires_2fa": False}
    resp = client.get("/api/auth/session")
    assert resp.status_code == 200
    data = resp.json()
    assert data["authenticated"] is True
    assert data["apple_id"] == "test@apple.com"


# --- Albums ---

@patch("backend.routers.albums.icloud_service")
def test_albums_success(mock_svc, client):
    mock_svc.get_albums.return_value = [
        {"id": "a1", "name": "Vacation", "asset_count": 10, "folder_name": "Vacation"},
    ]
    resp = client.get("/api/albums")
    assert resp.status_code == 200
    assert len(resp.json()["albums"]) == 1


@patch("backend.routers.albums.icloud_service")
def test_albums_unauthenticated(mock_svc, client):
    mock_svc.get_albums.return_value = {"error": "not_authenticated", "message": "Not authenticated"}
    resp = client.get("/api/albums")
    assert resp.status_code == 401


# --- Sort ---

@patch("backend.routers.sort.sorter_service")
def test_sort_start_success(mock_sorter, client):
    mock_sorter.start.return_value = {"total_files": 42}
    resp = client.post("/api/sort/start", json={"album_ids": ["a1"]})
    assert resp.status_code == 200
    assert resp.json()["total_files"] == 42


@patch("backend.routers.sort.sorter_service")
def test_sort_start_already_running(mock_sorter, client):
    mock_sorter.start.return_value = {"error": "sort_in_progress", "message": "Already running"}
    resp = client.post("/api/sort/start", json={"album_ids": ["a1"]})
    assert resp.status_code == 409


@patch("backend.routers.sort.sorter_service")
def test_sort_start_not_authenticated(mock_sorter, client):
    mock_sorter.start.return_value = {"error": "not_authenticated", "message": "Not authenticated"}
    resp = client.post("/api/sort/start", json={"album_ids": ["a1"]})
    assert resp.status_code == 401


@patch("backend.routers.sort.sorter_service")
def test_sort_start_empty_album_ids(mock_sorter, client):
    mock_sorter.start.return_value = {"error": "file_not_found", "message": "No files"}
    resp = client.post("/api/sort/start", json={"album_ids": []})
    assert resp.status_code == 400


@patch("backend.routers.sort.sorter_service")
def test_sort_start_unconfigured_folder(mock_sorter, client):
    mock_sorter.start.return_value = {"error": "file_not_found", "message": "iCloud folder not found"}
    resp = client.post("/api/sort/start", json={"album_ids": ["a1"]})
    assert resp.status_code == 400


@patch("backend.routers.sort.sorter_service")
def test_sort_progress_no_active_sort(mock_sorter, client):
    mock_sorter.is_running.return_value = False
    mock_sorter.get_progress.return_value = {"status": "idle"}
    resp = client.get("/api/sort/progress")
    assert resp.status_code == 409


@patch("backend.routers.sort.sorter_service")
def test_sort_progress_sse_stream(mock_sorter, client):
    mock_sorter.is_running.return_value = True
    mock_sorter.get_progress.return_value = {
        "status": "complete",
        "total_files": 10,
        "completed_files": 10,
        "failed_files": 0,
        "current_file": "",
        "current_album": "",
        "errors": [],
    }

    resp = client.get("/api/sort/progress")
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    # Parse first SSE event
    lines = resp.text.strip().split("\n")
    data_line = [l for l in lines if l.startswith("data: ")][0]
    event_data = json.loads(data_line[6:])
    assert event_data["status"] == "complete"
    assert event_data["total_files"] == 10


# --- Settings ---

@patch("backend.routers.settings.load_settings")
def test_get_settings(mock_load, client):
    mock_load.return_value = {"icloud_folder": "/test/path", "duplicate_handling": "move_only"}
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    assert resp.json()["icloud_folder"] == "/test/path"
    assert resp.json()["duplicate_handling"] == "move_only"


@patch("backend.routers.settings.save_settings")
@patch("backend.routers.settings.load_settings")
def test_put_settings(mock_load, mock_save, client):
    mock_load.return_value = {"icloud_folder": "/old/path", "duplicate_handling": "move_only"}
    resp = client.put("/api/settings", json={"icloud_folder": "/new/path"})
    assert resp.status_code == 200
    assert resp.json()["icloud_folder"] == "/new/path"
    mock_save.assert_called_once()
