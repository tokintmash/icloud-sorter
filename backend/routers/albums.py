import asyncio

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.models.schemas import AlbumListResponse
from backend.services import icloud_service

router = APIRouter(prefix="/api/albums", tags=["albums"])


@router.get("", response_model=None)
async def list_albums() -> AlbumListResponse | JSONResponse:
    result = await asyncio.to_thread(icloud_service.get_albums)

    if isinstance(result, dict) and "error" in result:
        status_code = 401 if result["error"] == "not_authenticated" else 500
        return JSONResponse(status_code=status_code, content=result)

    # Build folder_map from the album list for sync_album_metadata
    folder_map = {a["id"]: a["folder_name"] for a in result}

    # Sync per-asset metadata into album_files table (heavy, run off event loop)
    sync_result = await asyncio.to_thread(icloud_service.sync_album_metadata, folder_map)
    if isinstance(sync_result, dict) and "error" in sync_result:
        return JSONResponse(status_code=500, content=sync_result)

    return AlbumListResponse(albums=result)
