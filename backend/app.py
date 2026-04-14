import sys
from pathlib import Path

# Ensure the project root is on sys.path so that `python app.py` works
# (must run before any `backend.*` imports)
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.models.db import init_db
from backend.routers import auth, albums, sort, settings
from backend.runtime_paths import frontend_dist
from backend.lifecycle import can_shutdown, request_shutdown


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="iCloud Photo Sorter", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(albums.router)
app.include_router(sort.router)
app.include_router(settings.router)

FRONTEND_DIST = frontend_dist()

if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static-assets")


@app.get("/api/app/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/api/app/quit")
async def quit_app() -> JSONResponse:
    if not can_shutdown():
        return JSONResponse(
            status_code=409,
            content={"error": "not_available", "message": "Quit is only available in desktop mode"},
        )
    request_shutdown()
    return JSONResponse(content={"ok": True})


@app.get("/{full_path:path}", response_model=None)
async def spa_fallback(request: Request, full_path: str) -> FileResponse | JSONResponse:
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"error": "not_found", "message": "API endpoint not found"})

    if FRONTEND_DIST.is_dir():
        file_path = (FRONTEND_DIST / full_path).resolve()
        if file_path.is_relative_to(FRONTEND_DIST.resolve()) and file_path.is_file():
            return FileResponse(str(file_path))

        index_path = FRONTEND_DIST / "index.html"
        if index_path.is_file():
            return FileResponse(str(index_path))

    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "message": "Frontend not built. Run 'npm run build' in frontend/"},
    )


if __name__ == "__main__":
    from backend.dev_server import run

    run()
