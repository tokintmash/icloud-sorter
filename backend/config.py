import json
import sys
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


def _detect_icloud_folder_registry() -> str | None:
    """Try to find the iCloud Photos folder via the Windows registry."""
    if sys.platform != "win32":
        return None
    try:
        import winreg

        _REG_PATHS = [
            (r"Software\Apple Inc.\iCloud\iCloudDriveDesktop", "PhotosPath"),
            (r"Software\Apple Inc.\Internet Services", "PhotosPath"),
        ]
        for subkey, val_name in _REG_PATHS:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey)
                try:
                    value, _ = winreg.QueryValueEx(key, val_name)
                    if value and Path(value).exists():
                        return str(Path(value))
                finally:
                    winreg.CloseKey(key)
            except (OSError, FileNotFoundError):
                continue
    except (OSError, ImportError, FileNotFoundError):
        pass
    return None


def _detect_icloud_folder() -> str:
    registry_path = _detect_icloud_folder_registry()
    if registry_path:
        return registry_path
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
