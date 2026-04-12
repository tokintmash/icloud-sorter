import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse

from backend.models.schemas import SortStartRequest, SortStartResponse
from backend.services.sorter_service import sorter_service

router = APIRouter(prefix="/api/sort", tags=["sort"])


@router.post("/start", response_model=None)
async def start_sort(request: SortStartRequest) -> SortStartResponse | JSONResponse:
    result = sorter_service.start(request.album_ids)

    if "error" in result:
        status_map = {
            "sort_in_progress": 409,
            "not_authenticated": 401,
            "not_found": 404,
            "file_not_found": 400,
            "permission_denied": 403,
        }
        status_code = status_map.get(result["error"], 500)
        return JSONResponse(status_code=status_code, content=result)

    return SortStartResponse(**result)


@router.get("/progress")
async def sort_progress() -> StreamingResponse:
    async def event_stream():
        while True:
            progress = sorter_service.get_progress()
            data = json.dumps(progress)
            yield f"data: {data}\n\n"

            if progress["status"] in ("complete", "error"):
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
