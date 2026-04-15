"""Shutdown callback system for desktop mode.

In desktop mode, the launcher registers a callback so the /api/app/quit
endpoint can trigger a graceful shutdown. In dev mode, no callback is
registered and shutdown requests are rejected.
"""

from typing import Callable

_shutdown_callbacks: list[Callable[[], None]] = []


def register_shutdown_callback(callback: Callable[[], None]) -> None:
    """Register a callback to invoke on shutdown request."""
    _shutdown_callbacks.append(callback)


def can_shutdown() -> bool:
    """Return True if a shutdown callback has been registered (desktop mode)."""
    return len(_shutdown_callbacks) > 0


def request_shutdown() -> None:
    """Invoke all registered shutdown callbacks."""
    for cb in _shutdown_callbacks:
        cb()
