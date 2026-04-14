import sys
from pathlib import Path
from unittest.mock import patch

from backend.runtime_paths import bundle_root, frontend_dist, is_frozen


def test_is_frozen_false():
    assert is_frozen() is False


def test_is_frozen_true():
    with patch.object(sys, "frozen", True, create=True):
        assert is_frozen() is True


def test_bundle_root_dev():
    root = bundle_root()
    assert root == Path(__file__).resolve().parent.parent.parent


def test_bundle_root_frozen(tmp_path):
    with patch.object(sys, "frozen", True, create=True), \
         patch.object(sys, "_MEIPASS", str(tmp_path), create=True):
        assert bundle_root() == tmp_path


def test_frontend_dist_dev():
    dist = frontend_dist()
    expected = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    assert dist == expected


def test_frontend_dist_frozen(tmp_path):
    with patch.object(sys, "frozen", True, create=True), \
         patch.object(sys, "_MEIPASS", str(tmp_path), create=True):
        assert frontend_dist() == tmp_path / "frontend" / "dist"
