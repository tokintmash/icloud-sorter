import json
from unittest.mock import patch

from backend.config import _detect_icloud_folder, load_settings, save_settings


def test_detect_icloud_folder_returns_first_existing(tmp_path):
    path1 = tmp_path / "first"
    path2 = tmp_path / "second"
    path2.mkdir()  # only second exists

    with patch("backend.config._AUTO_DETECT_PATHS", [path1, path2]):
        result = _detect_icloud_folder()
    assert result == str(path2)


def test_detect_icloud_folder_returns_empty_if_none(tmp_path):
    path1 = tmp_path / "nonexistent"
    with patch("backend.config._AUTO_DETECT_PATHS", [path1]):
        result = _detect_icloud_folder()
    assert result == ""


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
