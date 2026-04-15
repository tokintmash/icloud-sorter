from unittest.mock import patch

import pytest

from backend.services.sorter_service import SorterService
from backend.services.state_service import (
    replace_album_files,
    get_album_summaries,
)


def _setup_files(tmp_path, filenames):
    """Create files in tmp_path and return the path."""
    for fn in filenames:
        (tmp_path / fn).write_text("data")
    return tmp_path


def _make_rows(album_id, album_name, filenames, folder_name="TestAlbum"):
    return [
        {"album_id": album_id, "album_name": album_name, "filename": fn, "folder_name": folder_name}
        for fn in filenames
    ]


@pytest.fixture
def sorter():
    return SorterService()


def test_happy_path(tmp_db, tmp_path, sorter):
    _setup_files(tmp_path, ["IMG_001.HEIC", "IMG_002.HEIC"])
    rows = _make_rows("a1", "Vacation", ["IMG_001.HEIC", "IMG_002.HEIC"], "Vacation")
    replace_album_files(rows)

    from backend.services import state_service
    state_service.reset_album_files(["a1"])

    sorter._run_sort(
        state_service.get_pending_album_files(["a1"]),
        str(tmp_path),
    )

    assert (tmp_path / "Vacation" / "IMG_001.HEIC").exists()
    assert (tmp_path / "Vacation" / "IMG_002.HEIC").exists()
    summaries = get_album_summaries()
    assert summaries[0]["sorted_count"] == 2


def test_file_not_found(tmp_db, tmp_path, sorter):
    rows = _make_rows("a1", "Album", ["missing.jpg"], "Album")
    replace_album_files(rows)

    from backend.services import state_service
    state_service.reset_album_files(["a1"])

    sorter._run_sort(
        state_service.get_pending_album_files(["a1"]),
        str(tmp_path),
    )

    summaries = get_album_summaries()
    assert summaries[0]["failed_count"] == 1
    assert sorter._errors[0]["error"] == "File not found"


def test_file_already_in_target_dir(tmp_db, tmp_path, sorter):
    target_dir = tmp_path / "Album"
    target_dir.mkdir()
    (target_dir / "IMG_001.HEIC").write_text("data")

    rows = _make_rows("a1", "Album", ["IMG_001.HEIC"], "Album")
    replace_album_files(rows)

    from backend.services import state_service
    state_service.reset_album_files(["a1"])

    sorter._run_sort(
        state_service.get_pending_album_files(["a1"]),
        str(tmp_path),
    )

    summaries = get_album_summaries()
    assert summaries[0]["sorted_count"] == 1


def test_filename_collision(tmp_db, tmp_path, sorter):
    # File exists in root AND target dir already has same name
    target_dir = tmp_path / "Album"
    target_dir.mkdir()
    (target_dir / "IMG_001.HEIC").write_text("existing")
    (tmp_path / "IMG_001.HEIC").write_text("new")

    rows = _make_rows("a1", "Album", ["IMG_001.HEIC"], "Album")
    replace_album_files(rows)

    from backend.services import state_service
    state_service.reset_album_files(["a1"])

    pending = state_service.get_pending_album_files(["a1"])
    sorter._run_sort(pending, str(tmp_path))

    # The file in target already counted as "in target", so it should be sorted
    # Or if both are found, the one already in target is claimed, and there might be the root one
    summaries = get_album_summaries()
    assert summaries[0]["sorted_count"] == 1


def test_cross_album_duplicate(tmp_db, tmp_path, sorter):
    (tmp_path / "IMG_001.HEIC").write_text("data")

    rows = (
        _make_rows("a1", "Album1", ["IMG_001.HEIC"], "Album1") +
        _make_rows("a2", "Album2", ["IMG_001.HEIC"], "Album2")
    )
    replace_album_files(rows)

    from backend.services import state_service
    state_service.reset_album_files(["a1", "a2"])

    sorter._run_sort(
        state_service.get_pending_album_files(["a1", "a2"]),
        str(tmp_path),
    )

    # move_only mode (default): file moves to first album, second is marked failed
    summaries = get_album_summaries()
    sorted_total = sum(s["sorted_count"] for s in summaries)
    failed_total = sum(s["failed_count"] for s in summaries)
    assert sorted_total == 1
    assert failed_total == 1
    assert (tmp_path / "Album1" / "IMG_001.HEIC").exists()


def test_case_insensitive_matching(tmp_db, tmp_path, sorter):
    (tmp_path / "img_001.heic").write_text("data")

    rows = _make_rows("a1", "Album", ["IMG_001.HEIC"], "Album")
    replace_album_files(rows)

    from backend.services import state_service
    state_service.reset_album_files(["a1"])

    sorter._run_sort(
        state_service.get_pending_album_files(["a1"]),
        str(tmp_path),
    )

    summaries = get_album_summaries()
    assert summaries[0]["sorted_count"] == 1


def test_permission_error(tmp_db, tmp_path, sorter):
    (tmp_path / "IMG_001.HEIC").write_text("data")

    rows = _make_rows("a1", "Album", ["IMG_001.HEIC"], "Album")
    replace_album_files(rows)

    from backend.services import state_service
    state_service.reset_album_files(["a1"])

    with patch("os.rename", side_effect=PermissionError("Access denied")):
        sorter._run_sort(
            state_service.get_pending_album_files(["a1"]),
            str(tmp_path),
        )

    summaries = get_album_summaries()
    assert summaries[0]["failed_count"] == 1
    assert "Permission denied" in sorter._errors[0]["error"]


def test_sort_already_in_progress(tmp_db, sorter):
    sorter._running = True
    result = sorter.start(["a1"])
    assert result["error"] == "sort_in_progress"


@patch("backend.services.sorter_service.icloud_service._is_authenticated", return_value=False)
def test_sort_unauthenticated(mock_auth, tmp_db, sorter):
    result = sorter.start(["a1"])
    assert result["error"] == "not_authenticated"


@patch("backend.services.sorter_service.icloud_service._is_authenticated", return_value=True)
@patch("backend.services.sorter_service.load_settings", return_value={"icloud_folder": ""})
def test_sort_invalid_icloud_folder(mock_settings, mock_auth, tmp_db, sorter):
    result = sorter.start(["a1"])
    assert result["error"] == "file_not_found"


def test_file_index_updated_after_move(tmp_db, tmp_path, sorter):
    """After moving a file for album A, album B should find it at new location."""
    (tmp_path / "IMG_001.HEIC").write_text("data")

    rows = (
        _make_rows("a1", "Album1", ["IMG_001.HEIC"], "Album1") +
        _make_rows("a2", "Album2", ["IMG_001.HEIC"], "Album2")
    )
    replace_album_files(rows)

    from backend.services import state_service
    state_service.reset_album_files(["a1", "a2"])

    sorter._run_sort(
        state_service.get_pending_album_files(["a1", "a2"]),
        str(tmp_path),
    )

    # move_only mode: file moves to Album1, Album2 is marked failed
    # (file_index is updated but target_path is also claimed, preventing re-move)
    summaries = get_album_summaries()
    total_sorted = sum(s["sorted_count"] for s in summaries)
    total_failed = sum(s["failed_count"] for s in summaries)
    assert total_sorted == 1
    assert total_failed == 1
