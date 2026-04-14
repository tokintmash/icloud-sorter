"""PyInstaller entry point for iCloud Photo Sorter.

Starts the uvicorn server in a background thread, waits for it to become
ready, then opens a pywebview native window. Closing the window shuts
everything down.
"""

import sys
import threading
import time
from pathlib import Path

# Ensure project root on sys.path for dev runs
_project_root = str(Path(__file__).resolve().parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import uvicorn

HOST = "127.0.0.1"
PORT = 8000
HEALTH_URL = f"http://{HOST}:{PORT}/api/app/health"
STARTUP_TIMEOUT = 30


def _start_server() -> uvicorn.Server:
    """Create and start a uvicorn server in a background thread."""
    from backend.app import app
    from backend.lifecycle import register_shutdown_callback

    config = uvicorn.Config(
        app=app,
        host=HOST,
        port=PORT,
        reload=False,
        workers=1,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    register_shutdown_callback(lambda: setattr(server, "should_exit", True))

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return server


def _wait_for_ready() -> bool:
    """Poll the health endpoint until the server is ready."""
    import urllib.request
    import urllib.error

    deadline = time.time() + STARTUP_TIMEOUT
    while time.time() < deadline:
        try:
            resp = urllib.request.urlopen(HEALTH_URL, timeout=2)
            if resp.status == 200:
                return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.25)
    return False


def _show_error(message: str) -> None:
    """Show a native error dialog."""
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, "iCloud Photo Sorter", 0x10)
    else:
        print(f"ERROR: {message}", file=sys.stderr)


def main() -> None:
    server = _start_server()

    if not _wait_for_ready():
        _show_error(
            "Failed to start the server.\n\n"
            "Port 8000 may already be in use, or the application failed to initialize."
        )
        server.should_exit = True
        sys.exit(1)

    try:
        import webview

        window = webview.create_window(
            "iCloud Photo Sorter",
            f"http://{HOST}:{PORT}",
            width=1024,
            height=768,
            min_size=(800, 600),
        )
        webview.start()
    except Exception as e:
        _show_error(f"Failed to open application window:\n{e}")
        server.should_exit = True
        sys.exit(1)

    server.should_exit = True


if __name__ == "__main__":
    main()
