from unittest.mock import patch

from backend.config import (
    _detect_icloud_folder,
    _detect_icloud_folder_registry,
    load_settings,
    save_settings,
)


def test_detect_icloud_folder_returns_first_existing(tmp_path):
    path1 = tmp_path / "first"
    path2 = tmp_path / "second"
    path2.mkdir()  # only second exists

    with patch("backend.config._detect_icloud_folder_registry", return_value=None), \
         patch("backend.config._AUTO_DETECT_PATHS", [path1, path2]):
        result = _detect_icloud_folder()
    assert result == str(path2)


def test_detect_icloud_folder_returns_empty_if_none(tmp_path):
    path1 = tmp_path / "nonexistent"
    with patch("backend.config._detect_icloud_folder_registry", return_value=None), \
         patch("backend.config._AUTO_DETECT_PATHS", [path1]):
        result = _detect_icloud_folder()
    assert result == ""


def test_detect_icloud_folder_prefers_registry(tmp_path):
    registry_path = tmp_path / "registry_photos"
    registry_path.mkdir()
    fs_path = tmp_path / "fs_photos"
    fs_path.mkdir()

    with patch("backend.config._detect_icloud_folder_registry", return_value=str(registry_path)), \
         patch("backend.config._AUTO_DETECT_PATHS", [fs_path]):
        result = _detect_icloud_folder()
    assert result == str(registry_path)


def test_detect_registry_non_windows():
    with patch("backend.config.sys") as mock_sys:
        mock_sys.platform = "linux"
        result = _detect_icloud_folder_registry()
    assert result is None


def test_load_save_settings_roundtrip(tmp_path):
    settings_path = tmp_path / "settings.json"
    with patch("backend.config.SETTINGS_PATH", settings_path), \
         patch("backend.config._detect_icloud_folder", return_value=""):
        save_settings({"icloud_folder": "/test/path"})
        result = load_settings()
    assert result["icloud_folder"] == "/test/path"


def test_load_settings_missing_file(tmp_path):
    settings_path = tmp_path / "settings.json"
    with patch("backend.config.SETTINGS_PATH", settings_path), \
         patch("backend.config._detect_icloud_folder", return_value=""):
        result = load_settings()
    assert result["icloud_folder"] == ""


def test_load_settings_corrupt_json(tmp_path):
    settings_path = tmp_path / "settings.json"
    settings_path.write_text("not json{{{")
    with patch("backend.config.SETTINGS_PATH", settings_path), \
         patch("backend.config._detect_icloud_folder", return_value=""):
        result = load_settings()
    assert result["icloud_folder"] == ""
