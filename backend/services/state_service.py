import json
from typing import Any

from backend.config import APP_STATE_DIR
from backend.models.db import get_db


_SESSION_PATH = APP_STATE_DIR / "session.json"


def save_session(apple_id: str, cookie_dir: str) -> None:
    APP_STATE_DIR.mkdir(parents=True, exist_ok=True)
    data = {"apple_id": apple_id, "cookie_dir": cookie_dir}
    with open(_SESSION_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_session() -> dict[str, Any] | None:
    if not _SESSION_PATH.exists():
        return None
    try:
        with open(_SESSION_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def replace_album_files(rows: list[dict[str, str]], album_ids: list[str] | None = None) -> None:
    db = get_db()
    try:
        if album_ids:
            placeholders = ",".join("?" * len(album_ids))
            db.execute(f"DELETE FROM album_files WHERE album_id IN ({placeholders})", album_ids)
        else:
            db.execute("DELETE FROM album_files")
        db.executemany(
            "INSERT OR IGNORE INTO album_files (album_id, album_name, filename, folder_name, status, error) VALUES (?, ?, ?, ?, 'pending', NULL)",
            [(r["album_id"], r["album_name"], r["filename"], r.get("folder_name", "")) for r in rows],
        )
        db.commit()
    finally:
        db.close()


def get_album_summaries() -> list[dict[str, Any]]:
    db = get_db()
    try:
        rows = db.execute(
            """
            SELECT
                album_id AS id,
                album_name AS name,
                COUNT(*) AS asset_count,
                SUM(CASE WHEN status = 'sorted' THEN 1 ELSE 0 END) AS sorted_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count
            FROM album_files
            GROUP BY album_id, album_name
            ORDER BY LOWER(album_name), album_id
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        db.close()


def reset_album_files(album_ids: list[str]) -> None:
    db = get_db()
    try:
        placeholders = ",".join("?" for _ in album_ids)
        db.execute(
            f"UPDATE album_files SET status = 'pending', error = NULL WHERE album_id IN ({placeholders})",
            album_ids,
        )
        db.commit()
    finally:
        db.close()


def get_pending_album_files(album_ids: list[str]) -> list[dict[str, str]]:
    db = get_db()
    try:
        placeholders = ",".join("?" for _ in album_ids)
        rows = db.execute(
            f"""
            SELECT album_id, album_name, filename, folder_name
            FROM album_files
            WHERE album_id IN ({placeholders}) AND status = 'pending'
            ORDER BY LOWER(album_name), LOWER(filename)
            """,
            album_ids,
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        db.close()


def mark_album_file_sorted(album_id: str, filename: str) -> None:
    db = get_db()
    try:
        db.execute(
            "UPDATE album_files SET status = 'sorted', error = NULL WHERE album_id = ? AND filename = ?",
            (album_id, filename),
        )
        db.commit()
    finally:
        db.close()


def mark_album_file_failed(album_id: str, filename: str, error: str) -> None:
    db = get_db()
    try:
        db.execute(
            "UPDATE album_files SET status = 'failed', error = ? WHERE album_id = ? AND filename = ?",
            (error, album_id, filename),
        )
        db.commit()
    finally:
        db.close()
