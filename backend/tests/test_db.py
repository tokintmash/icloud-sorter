import sqlite3
from unittest.mock import patch

from backend.models.db import SCHEMA, init_db, get_db


def test_init_db_idempotent(tmp_path):
    db_path = tmp_path / "state.db"
    with patch("backend.models.db.STATE_DB_PATH", db_path):
        init_db()
        init_db()  # second call should not error

    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='album_files'")
    assert cursor.fetchone() is not None
    conn.close()


def test_schema_columns(tmp_path):
    db_path = tmp_path / "state.db"
    with patch("backend.models.db.STATE_DB_PATH", db_path):
        init_db()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("PRAGMA table_info(album_files)")
    columns = {row[1] for row in cursor.fetchall()}
    conn.close()

    expected = {"album_id", "album_name", "filename", "folder_name", "status", "error"}
    assert columns == expected


def test_schema_indexes(tmp_path):
    db_path = tmp_path / "state.db"
    with patch("backend.models.db.STATE_DB_PATH", db_path):
        init_db()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("PRAGMA index_list(album_files)")
    indexes = {row[1] for row in cursor.fetchall()}
    conn.close()

    assert "idx_album_files_status" in indexes
    assert "idx_album_files_album" in indexes
