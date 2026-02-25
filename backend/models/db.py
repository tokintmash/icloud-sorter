import sqlite3
from pathlib import Path

from backend.config import STATE_DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id          INTEGER PRIMARY KEY,
    apple_id    TEXT NOT NULL,
    cookie_dir  TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    expires_at  TEXT,
    last_used   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS albums (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    asset_count     INTEGER,
    last_synced_at  TEXT,
    folder_name     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    id              TEXT PRIMARY KEY,
    filename        TEXT NOT NULL,
    size_bytes      INTEGER,
    item_type       TEXT,
    created_at      TEXT,
    has_adjustments INTEGER DEFAULT 0,
    width           INTEGER,
    height          INTEGER
);

CREATE TABLE IF NOT EXISTS album_assets (
    album_id    TEXT NOT NULL REFERENCES albums(id),
    asset_id    TEXT NOT NULL REFERENCES assets(id),
    position    INTEGER,
    PRIMARY KEY (album_id, asset_id)
);

CREATE TABLE IF NOT EXISTS downloads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id        TEXT NOT NULL REFERENCES assets(id),
    album_id        TEXT NOT NULL REFERENCES albums(id),
    version         TEXT NOT NULL,
    local_path      TEXT,
    status          TEXT NOT NULL DEFAULT 'pending',
    file_size       INTEGER,
    bytes_downloaded INTEGER DEFAULT 0,
    error_message   TEXT,
    attempts        INTEGER DEFAULT 0,
    started_at      TEXT,
    completed_at    TEXT,
    UNIQUE(asset_id, album_id, version)
);

CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status);
CREATE INDEX IF NOT EXISTS idx_downloads_album ON downloads(album_id, status);
CREATE INDEX IF NOT EXISTS idx_album_assets_album ON album_assets(album_id);
"""


def init_db() -> None:
    db_dir = STATE_DB_PATH.parent
    db_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(STATE_DB_PATH))
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(STATE_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
