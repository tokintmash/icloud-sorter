import re
import logging
from typing import Any

from pyicloud import PyiCloudService
from pyicloud.exceptions import (
    PyiCloudFailedLoginException,
    PyiCloudAPIResponseException,
)

from backend.config import COOKIE_DIR
from backend.services import state_service

logger = logging.getLogger(__name__)


_INVALID_CHARS_RE = re.compile(r'[/\\:*?"<>|]')

_icloud: PyiCloudService | None = None
_apple_id: str | None = None
_requires_2fa: bool = False


def _sanitize_folder_name(name: str) -> str:
    sanitized = _INVALID_CHARS_RE.sub("_", name)
    sanitized = sanitized.strip().strip(".")
    sanitized = sanitized[:200]
    if not sanitized:
        sanitized = "Unnamed Album"
    return sanitized


def _compute_folder_names(albums: list[dict[str, str]]) -> dict[str, str]:
    """Given a list of {"id": ..., "name": ...} dicts, return {album_id: folder_name} with dedup."""
    sorted_albums = sorted(albums, key=lambda a: (a["name"].casefold(), a["id"]))
    seen: dict[str, int] = {}
    result: dict[str, str] = {}
    for album in sorted_albums:
        folder_name = _sanitize_folder_name(album["name"])
        if folder_name in seen:
            seen[folder_name] += 1
            folder_name = f"{folder_name} ({seen[folder_name]})"
        else:
            seen[folder_name] = 1
        result[album["id"]] = folder_name
    return result


def login(apple_id: str, password: str) -> dict[str, Any]:
    global _icloud, _apple_id, _requires_2fa

    COOKIE_DIR.mkdir(parents=True, exist_ok=True)
    cookie_dir = str(COOKIE_DIR)

    try:
        _icloud = PyiCloudService(apple_id, password, cookie_directory=cookie_dir)
    except PyiCloudFailedLoginException:
        _icloud = None
        _apple_id = None
        _requires_2fa = False
        return {"error": "invalid_credentials", "message": "Invalid Apple ID or password"}
    except PyiCloudAPIResponseException as e:
        _icloud = None
        _apple_id = None
        _requires_2fa = False
        return {"error": "internal_error", "message": f"iCloud API error: {e}"}
    except Exception as e:
        _icloud = None
        _apple_id = None
        _requires_2fa = False
        logger.exception("Unexpected error during login")
        return {"error": "internal_error", "message": f"Unexpected error: {e}"}

    _apple_id = apple_id

    if _icloud.requires_2fa or _icloud.requires_2sa:
        _requires_2fa = True
        state_service.save_session(apple_id, cookie_dir)
        return {"authenticated": False, "requires_2fa": True}

    _requires_2fa = False
    state_service.save_session(apple_id, cookie_dir)
    return {"authenticated": True, "requires_2fa": False}


def validate_2fa(code: str) -> dict[str, Any]:
    global _requires_2fa

    if _icloud is None:
        return {"error": "not_authenticated", "message": "No active login session. Please login first."}

    try:
        result = _icloud.validate_2fa_code(code)
        if not result:
            return {"error": "2fa_failed", "message": "Invalid 2FA code"}

        _requires_2fa = False
        return {"authenticated": True}
    except Exception as e:
        logger.exception("Error validating 2FA code")
        return {"error": "2fa_failed", "message": f"2FA validation failed: {e}"}


def get_session_status() -> dict[str, Any]:
    if _icloud is None:
        return {"authenticated": False, "apple_id": None, "requires_2fa": False}

    if _requires_2fa:
        return {"authenticated": False, "apple_id": _apple_id, "requires_2fa": True}

    try:
        authenticated = _icloud.is_trusted_session
    except Exception:
        authenticated = not (_icloud.requires_2fa or _icloud.requires_2sa)

    return {
        "authenticated": authenticated,
        "apple_id": _apple_id,
        "requires_2fa": False,
    }


def _is_authenticated() -> bool:
    if _icloud is None:
        return False
    if _requires_2fa:
        return False
    return True


def get_albums() -> dict[str, Any] | list[dict[str, Any]]:
    if not _is_authenticated():
        return {"error": "not_authenticated", "message": "Not authenticated. Please login first."}

    try:
        photos = _icloud.photos  # type: ignore[union-attr]
        albums_raw: list[dict[str, Any]] = []

        for album in photos.albums:
            name = getattr(album, "title", None) or getattr(album, "name", "")
            album_id = getattr(album, "id", None) or str(id(album))

            try:
                asset_count = len(album)
            except Exception:
                asset_count = 0

            albums_raw.append({
                "id": album_id,
                "name": name,
                "asset_count": asset_count,
            })

        folder_map = _compute_folder_names(albums_raw)

        albums_list = []
        for a in albums_raw:
            albums_list.append({
                "id": a["id"],
                "name": a["name"],
                "asset_count": a["asset_count"],
                "folder_name": folder_map[a["id"]],
            })

        return albums_list
    except PyiCloudAPIResponseException as e:
        logger.exception("iCloud API error fetching albums")
        return {"error": "internal_error", "message": f"iCloud API error: {e}"}
    except Exception as e:
        logger.exception("Error fetching albums")
        return {"error": "internal_error", "message": f"Failed to fetch albums: {e}"}


def sync_album_metadata() -> dict[str, Any] | int:
    if not _is_authenticated():
        return {"error": "not_authenticated", "message": "Not authenticated. Please login first."}

    try:
        photos = _icloud.photos  # type: ignore[union-attr]
        rows: list[dict[str, str]] = []

        for album in photos.albums:
            name = getattr(album, "title", None) or getattr(album, "name", "")
            album_id = getattr(album, "id", None) or str(id(album))

            for asset in album:
                filename = getattr(asset, "filename", None)
                if not filename:
                    continue
                rows.append({
                    "album_id": album_id,
                    "album_name": name,
                    "filename": filename,
                })

        state_service.replace_album_files(rows)
        return len(rows)
    except PyiCloudAPIResponseException as e:
        logger.exception("iCloud API error syncing metadata")
        return {"error": "internal_error", "message": f"iCloud API error: {e}"}
    except Exception as e:
        logger.exception("Error syncing album metadata")
        return {"error": "internal_error", "message": f"Failed to sync metadata: {e}"}
