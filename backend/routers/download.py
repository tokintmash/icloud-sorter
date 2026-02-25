import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from backend.models.schemas import DownloadStartRequest
from backend.services.download_service import download_service

router = APIRouter(prefix="/api/download", tags=["download"])


@router.post("/start")
async def start_download(request: DownloadStartRequest) -> JSONResponse:
    result = download_service.start(request.album_ids, request.download_path)
    if "error" in result:
        status_map = {
            "download_in_progress": 409,
            "not_authenticated": 401,
            "not_found": 404,
            "insufficient_disk_space": 507,
            "internal_error": 500,
        }
        status_code = status_map.get(result["error"], 400)
        return JSONResponse(status_code=status_code, content=result)
    return JSONResponse(status_code=200, content=result)


@router.get("/progress")
async def download_progress(request: Request) -> StreamingResponse:
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            progress = download_service.get_progress()
            yield f"data: {json.dumps(progress)}\n\n"
            if progress["status"] in ("complete", "cancelled", "error"):
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/pause")
async def pause_download() -> JSONResponse:
    download_service.pause()
    return JSONResponse(status_code=200, content={"status": "paused"})


@router.post("/resume")
async def resume_download() -> JSONResponse:
    download_service.resume()
    return JSONResponse(status_code=200, content={"status": "resumed"})


@router.post("/cancel")
async def cancel_download() -> JSONResponse:
    download_service.cancel()
    return JSONResponse(status_code=200, content={"status": "cancelled"})
