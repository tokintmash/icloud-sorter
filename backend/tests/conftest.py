import sqlite3
from unittest.mock import patch

import pytest

from backend.models.db import SCHEMA


@pytest.fixture
def tmp_db(tmp_path):
    """Create an in-memory-style SQLite DB in tmp_path and patch STATE_DB_PATH."""
    db_path = tmp_path / "state.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

    with patch("backend.models.db.STATE_DB_PATH", db_path), \
         patch("backend.config.STATE_DB_PATH", db_path):
        yield db_path
