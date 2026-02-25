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


def create_download_records(album_id: str, assets: list[dict[str, Any]], version: str = "original") -> int:
    db = get_db()
    try:
        inserted = 0
        for asset in assets:
            cursor = db.execute(
                """
                INSERT OR IGNORE INTO downloads (asset_id, album_id, version, file_size, status)
                VALUES (?, ?, ?, ?, 'pending')
                """,
                (asset["id"], album_id, version, asset.get("size_bytes", 0)),
            )
            inserted += cursor.rowcount
        db.commit()
        return inserted
    finally:
        db.close()


def get_pending_downloads(album_ids: list[str]) -> list[dict[str, Any]]:
    db = get_db()
    try:
        placeholders = ",".join("?" for _ in album_ids)
        rows = db.execute(
            f"""
            SELECT id, asset_id, album_id, version, file_size, attempts
            FROM downloads
            WHERE album_id IN ({placeholders})
              AND (status = 'pending' OR (status = 'failed' AND attempts < ?))
            ORDER BY id
            """,
            (*album_ids, 3),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        db.close()


def update_download_status(
    asset_id: str,
    album_id: str,
    version: str,
    status: str,
    local_path: str | None = None,
    file_size: int | None = None,
    bytes_downloaded: int | None = None,
    error_message: str | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    db = get_db()
    try:
        sets = ["status = ?", "attempts = attempts + 1"]
        params: list[Any] = [status]

        if local_path is not None:
            sets.append("local_path = ?")
            params.append(local_path)
        if file_size is not None:
            sets.append("file_size = ?")
            params.append(file_size)
        if bytes_downloaded is not None:
            sets.append("bytes_downloaded = ?")
            params.append(bytes_downloaded)
        if error_message is not None:
            sets.append("error_message = ?")
            params.append(error_message)

        if status == "downloading":
            sets.append("started_at = ?")
            params.append(now)
        elif status in ("complete", "failed"):
            sets.append("completed_at = ?")
            params.append(now)

        params.extend([asset_id, album_id, version])
        db.execute(
            f"UPDATE downloads SET {', '.join(sets)} WHERE asset_id = ? AND album_id = ? AND version = ?",
            params,
        )
        db.commit()
    finally:
        db.close()


def get_completed_download_path(asset_id: str, version: str) -> str | None:
    db = get_db()
    try:
        row = db.execute(
            "SELECT local_path FROM downloads WHERE asset_id = ? AND version = ? AND status = 'complete' LIMIT 1",
            (asset_id, version),
        ).fetchone()
        if row and row["local_path"]:
            return row["local_path"]
        return None
    finally:
        db.close()


def get_download_stats(album_ids: list[str]) -> dict[str, int]:
    db = get_db()
    try:
        placeholders = ",".join("?" for _ in album_ids)
        row = db.execute(
            f"""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) AS skipped,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending,
                COALESCE(SUM(file_size), 0) AS total_bytes,
                COALESCE(SUM(CASE WHEN status = 'complete' THEN bytes_downloaded ELSE 0 END), 0) AS completed_bytes
            FROM downloads
            WHERE album_id IN ({placeholders})
            """,
            album_ids,
        ).fetchone()
        return {
            "total": row["total"] or 0,
            "completed": row["completed"] or 0,
            "failed": row["failed"] or 0,
            "skipped": row["skipped"] or 0,
            "pending": row["pending"] or 0,
            "total_bytes": row["total_bytes"] or 0,
            "completed_bytes": row["completed_bytes"] or 0,
        }
    finally:
        db.close()


def get_download_errors(album_ids: list[str]) -> list[dict[str, Any]]:
    db = get_db()
    try:
        placeholders = ",".join("?" for _ in album_ids)
        rows = db.execute(
            f"""
            SELECT d.asset_id, a.filename, d.error_message, d.attempts
            FROM downloads d
            LEFT JOIN assets a ON d.asset_id = a.id
            WHERE d.album_id IN ({placeholders}) AND d.status = 'failed'
            """,
            album_ids,
        ).fetchall()
        return [
            {
                "asset_id": row["asset_id"],
                "filename": row["filename"] or row["asset_id"],
                "error_message": row["error_message"] or "",
                "attempts": row["attempts"] or 0,
            }
            for row in rows
        ]
    finally:
        db.close()


def mark_remaining_pending_as_skipped(album_ids: list[str]) -> None:
    db = get_db()
    try:
        placeholders = ",".join("?" for _ in album_ids)
        db.execute(
            f"UPDATE downloads SET status = 'skipped' WHERE album_id IN ({placeholders}) AND status = 'pending'",
            album_ids,
        )
        db.commit()
    finally:
        db.close()


def get_album_folder_name(album_id: str) -> str | None:
    db = get_db()
    try:
        row = db.execute(
            "SELECT folder_name FROM albums WHERE id = ?",
            (album_id,),
        ).fetchone()
        if row:
            return row["folder_name"]
        return None
    finally:
        db.close()
