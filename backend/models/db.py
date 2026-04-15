import sqlite3

from backend.config import STATE_DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS album_files (
    album_id    TEXT NOT NULL,
    album_name  TEXT NOT NULL,
    filename    TEXT NOT NULL,
    folder_name TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'pending',
    error       TEXT,
    PRIMARY KEY (album_id, filename)
);

CREATE INDEX IF NOT EXISTS idx_album_files_status ON album_files(status);
CREATE INDEX IF NOT EXISTS idx_album_files_album ON album_files(album_id);
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
    needs_init = not STATE_DB_PATH.exists()
    conn = sqlite3.connect(str(STATE_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if needs_init:
        conn.executescript(SCHEMA)
        conn.commit()
    return conn
