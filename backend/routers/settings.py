import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.config import SETTINGS_PATH, DEFAULT_ICLOUD_FOLDER
from backend.models.schemas import SettingsResponse, SettingsUpdateRequest

router = APIRouter(prefix="/api/settings", tags=["settings"])

_AUTO_DETECT_PATHS = [
    Path.home() / "Pictures" / "iCloud Photos" / "Photos",
    Path.home() / "iCloudPhotos",
    Path.home() / "Pictures" / "iCloud Photos",
]


def _detect_icloud_folder() -> str:
    for p in _AUTO_DETECT_PATHS:
        if p.exists():
            return str(p)
    return DEFAULT_ICLOUD_FOLDER


def _get_defaults() -> dict[str, str]:
    return {"icloud_folder": _detect_icloud_folder()}


def _load_settings() -> dict[str, str]:
    defaults = _get_defaults()
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r") as f:
                stored = json.load(f)
            defaults.update(stored)
        except (json.JSONDecodeError, OSError):
            pass
    return defaults


def _save_settings(settings: dict[str, str]) -> None:
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
