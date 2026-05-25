import base64
import logging
import re
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
_SAFE_ERROR_CODE_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")


def _safe_icloud_api_code(code: Any) -> str | int | None:
    if isinstance(code, int):
        return code
    if isinstance(code, str) and _SAFE_ERROR_CODE_RE.fullmatch(code):
        return code
    return None


def _safe_icloud_api_status(response: Any) -> int | None:
    status_code = getattr(response, "status_code", None)
    return status_code if isinstance(status_code, int) else None


def _safe_icloud_api_message(exc: PyiCloudAPIResponseException) -> str:
    code = _safe_icloud_api_code(getattr(exc, "code", None))
    if code is None:
        return "iCloud API error"
    return f"iCloud API error ({code})"


def _log_icloud_api_error(message: str, exc: PyiCloudAPIResponseException) -> None:
    logger.error(
        "%s: exception=%s code=%s status_code=%s",
        message,
        exc.__class__.__name__,
        _safe_icloud_api_code(getattr(exc, "code", None)),
        _safe_icloud_api_status(getattr(exc, "response", None)),
    )


def _get_asset_filename(asset: Any) -> str | None:
    """Extract filename from a pyicloud PhotoAsset, handling base64 and plain-text filenameEnc."""
    try:
        return asset.filename
    except Exception:
        pass
    # Fallback: read filenameEnc directly
    try:
        record = asset._master_record
        raw = record["fields"]["filenameEnc"]["value"]
        # Try base64 decode first (some assets are actually encoded)
        try:
            padded = raw + "=" * (-len(raw) % 4)
            return base64.b64decode(padded).decode("utf-8")
        except Exception:
            pass
        # filenameEnc is already a plain-text filename
        if isinstance(raw, str) and raw:
            return raw
    except Exception:
        pass
    return None

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

    logger.info("Login attempt started")
    COOKIE_DIR.mkdir(parents=True, exist_ok=True)
    cookie_dir = str(COOKIE_DIR)

    try:
        _icloud = PyiCloudService(apple_id, password, cookie_directory=cookie_dir)
    except PyiCloudFailedLoginException:
        _icloud = None
        _apple_id = None
        _requires_2fa = False
        logger.info("Login failed: invalid credentials")
        return {"error": "invalid_credentials", "message": "Invalid Apple ID or password"}
    except PyiCloudAPIResponseException as e:
        _icloud = None
        _apple_id = None
        _requires_2fa = False
        _log_icloud_api_error("Login failed: iCloud API error", e)
        return {"error": "internal_error", "message": _safe_icloud_api_message(e)}
    except Exception as e:
        _icloud = None
        _apple_id = None
        _requires_2fa = False
        logger.error("Unexpected error during login: exception=%s", e.__class__.__name__)
        return {"error": "internal_error", "message": f"Unexpected error: {e}"}

    _apple_id = apple_id

    if _icloud.requires_2fa or _icloud.requires_2sa:
        _requires_2fa = True
        state_service.save_session(apple_id, cookie_dir)
        logger.info("Login requires two-factor authentication")
        return {"authenticated": False, "requires_2fa": True}

    _requires_2fa = False
    state_service.save_session(apple_id, cookie_dir)
    logger.info("Login succeeded")
    return {"authenticated": True, "requires_2fa": False}


def validate_2fa(code: str) -> dict[str, Any]:
    global _requires_2fa

    logger.info("Two-factor authentication validation started")
    if _icloud is None:
        logger.info("Two-factor authentication validation failed: no active session")
        return {"error": "not_authenticated", "message": "No active login session. Please login first."}

    try:
        result = _icloud.validate_2fa_code(code)
        if not result:
            logger.info("Two-factor authentication validation failed: invalid code")
            return {"error": "2fa_failed", "message": "Invalid 2FA code"}

        _requires_2fa = False
        logger.info("Two-factor authentication validation succeeded")
        return {"authenticated": True}
    except PyiCloudAPIResponseException as e:
        _log_icloud_api_error("Two-factor authentication validation failed: iCloud API error", e)
        return {"error": "2fa_failed", "message": _safe_icloud_api_message(e)}
    except Exception as e:
        logger.error("Error validating 2FA code: exception=%s", e.__class__.__name__)
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
        logger.info("Album fetch blocked: not authenticated")
        return {"error": "not_authenticated", "message": "Not authenticated. Please login first."}

    logger.info("Album fetch started")
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
                logger.warning("Album fetch could not determine asset count")

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

        logger.info("Album fetch completed: albums=%s", len(albums_list))
        return albums_list
    except PyiCloudAPIResponseException as e:
        _log_icloud_api_error("iCloud API error fetching albums", e)
        return {"error": "internal_error", "message": _safe_icloud_api_message(e)}
    except Exception as e:
        logger.exception("Error fetching albums")
        return {"error": "internal_error", "message": f"Failed to fetch albums: {e}"}


def sync_album_metadata(folder_map: dict[str, str], album_ids: list[str] | None = None) -> dict[str, Any] | int:
    """Sync per-asset metadata into the album_files table.

    If *album_ids* is given, only those albums are synced; otherwise all albums.
    """
    if not _is_authenticated():
        logger.info("Album metadata sync blocked: not authenticated")
        return {"error": "not_authenticated", "message": "Not authenticated. Please login first."}

    logger.info("Album metadata sync started: selected_albums=%s", len(album_ids) if album_ids else "all")
    try:
        photos = _icloud.photos  # type: ignore[union-attr]
        rows: list[dict[str, str]] = []
        filter_ids = set(album_ids) if album_ids else None
        skipped_assets = 0

        for album in photos.albums:
            name = getattr(album, "title", None) or getattr(album, "name", "")
            album_id = getattr(album, "id", None) or str(id(album))

            if filter_ids and album_id not in filter_ids:
                continue

            folder_name = folder_map.get(album_id, _sanitize_folder_name(name))

            for asset in album:
                fn = _get_asset_filename(asset)
                if not fn:
                    skipped_assets += 1
                    continue
                rows.append({
                    "album_id": album_id,
                    "album_name": name,
                    "filename": fn,
                    "folder_name": folder_name,
                })

        state_service.replace_album_files(rows, album_ids)
        if skipped_assets:
            logger.warning("Album metadata sync skipped assets without filenames: count=%s", skipped_assets)
        logger.info("Album metadata sync completed: files=%s", len(rows))
        return len(rows)
    except PyiCloudAPIResponseException as e:
        _log_icloud_api_error("iCloud API error syncing metadata", e)
        return {"error": "internal_error", "message": _safe_icloud_api_message(e)}
    except Exception as e:
        logger.exception("Error syncing album metadata")
        return {"error": "internal_error", "message": f"Failed to sync metadata: {e}"}
