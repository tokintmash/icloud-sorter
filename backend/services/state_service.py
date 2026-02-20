from datetime import datetime, timezone
from typing import Any

from backend.models.db import get_db


def save_session(apple_id: str, cookie_dir: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    db = get_db()
    try:
        db.execute(
            """
            INSERT INTO sessions (id, apple_id, cookie_dir, created_at, last_used)
            VALUES (1, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                apple_id = excluded.apple_id,
                cookie_dir = excluded.cookie_dir,
                last_used = excluded.last_used
            """,
            (apple_id, cookie_dir, now, now),
        )
        db.commit()
    finally:
        db.close()


def get_session() -> dict[str, Any] | None:
    db = get_db()
    try:
        row = db.execute(
            "SELECT apple_id, cookie_dir, created_at, last_used FROM sessions ORDER BY last_used DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        db.close()


def save_albums(albums: list[dict[str, Any]]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    db = get_db()
    try:
        for album in albums:
            db.execute(
                """
                INSERT INTO albums (id, name, asset_count, last_synced_at, folder_name)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    asset_count = excluded.asset_count,
                    last_synced_at = excluded.last_synced_at,
                    folder_name = excluded.folder_name
                """,
                (album["id"], album["name"], album["asset_count"], now, album["folder_name"]),
            )
        db.commit()
    finally:
        db.close()


def get_albums() -> list[dict[str, Any]]:
    db = get_db()
    try:
        rows = db.execute("SELECT id, name, asset_count, folder_name FROM albums").fetchall()
        return [dict(row) for row in rows]
    finally:
        db.close()


def save_assets(album_id: str, assets: list[dict[str, Any]]) -> None:
    db = get_db()
    try:
        for i, asset in enumerate(assets):
            db.execute(
                """
                INSERT INTO assets (id, filename, size_bytes, item_type, created_at, width, height)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    filename = excluded.filename,
                    size_bytes = excluded.size_bytes,
                    item_type = excluded.item_type,
                    created_at = excluded.created_at,
                    width = excluded.width,
                    height = excluded.height
                """,
                (
                    asset["id"],
                    asset["filename"],
                    asset.get("size_bytes", 0),
                    asset.get("item_type", ""),
                    asset.get("created_at", ""),
                    asset.get("width", 0),
                    asset.get("height", 0),
                ),
            )
            db.execute(
                """
                INSERT INTO album_assets (album_id, asset_id, position)
                VALUES (?, ?, ?)
                ON CONFLICT(album_id, asset_id) DO UPDATE SET
                    position = excluded.position
                """,
                (album_id, asset["id"], i),
            )
        db.commit()
    finally:
        db.close()
