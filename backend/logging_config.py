import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from backend.config import APP_STATE_DIR


_HANDLER_MARKER = "_icloud_sorter_diagnostic_handler"
_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(
    *,
    log_path: Path | None = None,
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> Path:
    """Configure backend diagnostic logging to a bounded local file."""
    resolved_log_path = log_path or APP_STATE_DIR / "logs" / "app.log"
    resolved_log_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    formatter = logging.Formatter(_LOG_FORMAT)
    for handler in root_logger.handlers:
        if getattr(handler, _HANDLER_MARKER, False):
            handler.setLevel(level)
            handler.setFormatter(formatter)
            return resolved_log_path

    handler = RotatingFileHandler(
        resolved_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    setattr(handler, _HANDLER_MARKER, True)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    return resolved_log_path
