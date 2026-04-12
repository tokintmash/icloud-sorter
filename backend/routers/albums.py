from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.models.schemas import AlbumListResponse
from backend.services import icloud_service

router = APIRouter(prefix="/api/albums", tags=["albums"])


@router.get("", response_model=None)
async def list_albums() -> AlbumListResponse | JSONResponse:
    result = icloud_service.get_albums()

    if isinstance(result, dict) and "error" in result:
        status_code = 401 if result["error"] == "not_authenticated" else 500
        return JSONResponse(status_code=status_code, content=result)

    return AlbumListResponse(albums=result)
