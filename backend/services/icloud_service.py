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
        albums_list: list[dict[str, Any]] = []
        seen_folder_names: dict[str, int] = {}

        for album in photos.albums:
            name = getattr(album, "title", None) or getattr(album, "name", "")
            album_id = getattr(album, "id", None) or str(id(album))

            try:
                asset_count = len(album)
            except Exception:
                asset_count = 0

            folder_name = _sanitize_folder_name(name)
            if folder_name in seen_folder_names:
                seen_folder_names[folder_name] += 1
                folder_name = f"{folder_name} ({seen_folder_names[folder_name]})"
            else:
                seen_folder_names[folder_name] = 1

            albums_list.append({
                "id": album_id,
                "name": name,
                "asset_count": asset_count,
                "folder_name": folder_name,
            })

        state_service.save_albums(albums_list)
        return albums_list
    except PyiCloudAPIResponseException as e:
        logger.exception("iCloud API error fetching albums")
        return {"error": "internal_error", "message": f"iCloud API error: {e}"}
    except Exception as e:
        logger.exception("Error fetching albums")
        return {"error": "internal_error", "message": f"Failed to fetch albums: {e}"}


def get_album_assets(
    album_id: str, offset: int = 0, limit: int = 200
) -> dict[str, Any]:
    if not _is_authenticated():
        return {"error": "not_authenticated", "message": "Not authenticated. Please login first."}

    try:
        photos = _icloud.photos  # type: ignore[union-attr]
        target_album = None
        for album in photos.albums:
            aid = getattr(album, "id", None) or str(id(album))
            if aid == album_id:
                target_album = album
                break

        if target_album is None:
            return {"error": "not_found", "message": f"Album '{album_id}' not found"}

        all_assets = list(target_album)
        total = len(all_assets)
        sliced = all_assets[offset : offset + limit]

        assets_list: list[dict[str, Any]] = []
        for asset in sliced:
            asset_id = getattr(asset, "id", str(id(asset)))
            filename = getattr(asset, "filename", "unknown")
            size_bytes = getattr(asset, "size", 0) or 0
            item_type = getattr(asset, "item_type", "image")
            created = getattr(asset, "created", None)
            created_at = created.isoformat() if created else ""
            dimensions = getattr(asset, "dimensions", (0, 0)) or (0, 0)
            width = dimensions[0] if len(dimensions) > 0 else 0
            height = dimensions[1] if len(dimensions) > 1 else 0

            assets_list.append({
                "id": asset_id,
                "filename": filename,
                "size_bytes": size_bytes,
                "item_type": item_type,
                "created_at": created_at,
                "width": width,
                "height": height,
            })

        state_service.save_assets(album_id, assets_list)

        return {
            "assets": assets_list,
            "total": total,
            "offset": offset,
            "limit": limit,
        }
    except PyiCloudAPIResponseException as e:
        logger.exception("iCloud API error fetching assets")
        return {"error": "internal_error", "message": f"iCloud API error: {e}"}
    except Exception as e:
        logger.exception("Error fetching album assets")
        return {"error": "internal_error", "message": f"Failed to fetch assets: {e}"}
