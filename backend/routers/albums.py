from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from backend.models.schemas import AlbumListResponse, AssetListResponse
from backend.services import icloud_service

router = APIRouter(prefix="/api/albums", tags=["albums"])


@router.get("", response_model=None)
async def list_albums() -> AlbumListResponse | JSONResponse:
    result = icloud_service.get_albums()

    if isinstance(result, dict) and "error" in result:
        status_code = 401 if result["error"] == "not_authenticated" else 500
        return JSONResponse(status_code=status_code, content=result)

    return AlbumListResponse(albums=result)


@router.get("/{album_id}/assets", response_model=None)
async def list_assets(
    album_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1),
) -> AssetListResponse | JSONResponse:
    result = icloud_service.get_album_assets(album_id, offset, limit)

    if "error" in result:
        status_map = {
            "not_authenticated": 401,
            "not_found": 404,
        }
        status_code = status_map.get(result["error"], 500)
        return JSONResponse(status_code=status_code, content=result)

    return AssetListResponse(**result)
