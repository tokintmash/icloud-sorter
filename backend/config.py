from pathlib import Path


STATE_DB_PATH: Path = Path.home() / ".icloud-downloader" / "state.db"
COOKIE_DIR: Path = Path.home() / ".icloud-downloader" / "cookies"
SETTINGS_PATH: Path = Path.home() / ".icloud-downloader" / "settings.json"

DEFAULT_DOWNLOAD_PATH: str = str(Path.home() / "icloud-photos")
DEFAULT_CONCURRENT_DOWNLOADS: int = 3
DEFAULT_METADATA_DELAY_MS: int = 200
DEFAULT_MAX_RETRIES: int = 3
