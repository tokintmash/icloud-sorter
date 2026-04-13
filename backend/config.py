import json
from pathlib import Path

APP_STATE_DIR: Path = Path.home() / ".icloud-sorter"
STATE_DB_PATH: Path = APP_STATE_DIR / "state.db"
COOKIE_DIR: Path = APP_STATE_DIR / "cookies"
SETTINGS_PATH: Path = APP_STATE_DIR / "settings.json"

DEFAULT_ICLOUD_FOLDER: str = ""

_AUTO_DETECT_PATHS = [
    Path.home() / "Pictures" / "iCloud Photos" / "Photos",
    Path.home() / "iCloudPhotos",
    Path.home() / "Pictures" / "iCloud Photos",
]


def _detect_icloud_folder() -> str:
    for p in _AUTO_DETECT_PATHS:
        if p.exists():
            return str(p)
    return DEFAULT_ICLOUD_FOLDER


def _get_defaults() -> dict[str, str]:
    return {"icloud_folder": _detect_icloud_folder(), "duplicate_handling": "move_only"}


def load_settings() -> dict[str, str]:
    defaults = _get_defaults()
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r") as f:
                stored = json.load(f)
            defaults.update(stored)
        except (json.JSONDecodeError, OSError):
            pass
    return defaults


def save_settings(settings: dict[str, str]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)
