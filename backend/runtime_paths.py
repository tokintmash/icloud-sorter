"""PyInstaller-safe path resolution."""

import sys
from pathlib import Path


def is_frozen() -> bool:
    """Return True when running inside a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def bundle_root() -> Path:
    """Return the bundle root (sys._MEIPASS when frozen, project root in dev)."""
    if is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def frontend_dist() -> Path:
    """Return the path to the frontend build directory."""
    return bundle_root() / "frontend" / "dist"
