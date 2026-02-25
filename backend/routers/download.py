from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.models.schemas import DownloadStartRequest

router = APIRouter(prefix="/api/download", tags=["download"])

_NOT_IMPLEMENTED = {"error": "not_implemented", "message": "Download endpoints coming in Phase 2"}


@router.post("/start")
async def start_download(request: DownloadStartRequest) -> JSONResponse:
    return JSONResponse(status_code=501, content=_NOT_IMPLEMENTED)


@router.get("/progress")
async def download_progress() -> JSONResponse:
    return JSONResponse(status_code=501, content=_NOT_IMPLEMENTED)


@router.post("/pause")
async def pause_download() -> JSONResponse:
    return JSONResponse(status_code=501, content=_NOT_IMPLEMENTED)


@router.post("/cancel")
async def cancel_download() -> JSONResponse:
    return JSONResponse(status_code=501, content=_NOT_IMPLEMENTED)
