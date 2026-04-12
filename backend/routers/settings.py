from fastapi import APIRouter

from backend.config import load_settings, save_settings
from backend.models.schemas import SettingsResponse, SettingsUpdateRequest

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings() -> SettingsResponse:
    settings = load_settings()
    return SettingsResponse(**settings)


@router.put("")
async def update_settings(request: SettingsUpdateRequest) -> SettingsResponse:
    settings = load_settings()

    update_data = request.model_dump(exclude_none=True)
    settings.update(update_data)

    save_settings(settings)
    return SettingsResponse(**settings)
