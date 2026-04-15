"""Dev server entry point. Used by `python backend/app.py`."""

import uvicorn


def run() -> None:
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
