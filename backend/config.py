from pathlib import Path

APP_STATE_DIR: Path = Path.home() / ".icloud-sorter"
STATE_DB_PATH: Path = APP_STATE_DIR / "state.db"
COOKIE_DIR: Path = APP_STATE_DIR / "cookies"
SETTINGS_PATH: Path = APP_STATE_DIR / "settings.json"

DEFAULT_ICLOUD_FOLDER: str = ""
