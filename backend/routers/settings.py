import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.config import (
    SETTINGS_PATH,
    DEFAULT_DOWNLOAD_PATH,
    DEFAULT_CONCURRENT_DOWNLOADS,
    DEFAULT_METADATA_DELAY_MS,
    DEFAULT_MAX_RETRIES,
)
from backend.models.schemas import SettingsResponse, SettingsUpdateRequest

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_defaults() -> dict[str, str | int]:
    return {
        "download_path": DEFAULT_DOWNLOAD_PATH,
        "concurrent_downloads": DEFAULT_CONCURRENT_DOWNLOADS,
        "metadata_delay_ms": DEFAULT_METADATA_DELAY_MS,
        "max_retries": DEFAULT_MAX_RETRIES,
    }


def _load_settings() -> dict[str, str | int]:
    defaults = _get_defaults()
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r") as f:
                stored = json.load(f)
            defaults.update(stored)
        except (json.JSONDecodeError, OSError):
            pass
    return defaults


def _save_settings(settings: dict[str, str | int]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)


@router.get("")
async def get_settings() -> SettingsResponse:
    settings = _load_settings()
    return SettingsResponse(**settings)


@router.put("")
async def update_settings(request: SettingsUpdateRequest) -> SettingsResponse:
    settings = _load_settings()

    update_data = request.model_dump(exclude_none=True)
    settings.update(update_data)

    _save_settings(settings)
    return SettingsResponse(**settings)
