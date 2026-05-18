import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from backend.config import (
    DEFAULT_LOG_LEVEL,
    LOG_FILE_PATH,
    LOG_ROTATION_BACKUP_COUNT,
    LOG_ROTATION_MAX_BYTES,
)


_HANDLER_MARKER = "_icloud_sorter_diagnostic_handler"
_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(
    *,
    log_path: Path | None = None,
    level: int | str = DEFAULT_LOG_LEVEL,
    max_bytes: int = LOG_ROTATION_MAX_BYTES,
    backup_count: int = LOG_ROTATION_BACKUP_COUNT,
) -> Path:
    """Configure backend diagnostic logging to a bounded local file."""
    resolved_log_path = log_path or LOG_FILE_PATH
    resolved_log_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_level = logging.getLevelName(level) if isinstance(level, str) else level

    root_logger = logging.getLogger()
    root_logger.setLevel(resolved_level)

    formatter = logging.Formatter(_LOG_FORMAT)
    for handler in root_logger.handlers:
        if getattr(handler, _HANDLER_MARKER, False):
            handler.setLevel(resolved_level)
            handler.setFormatter(formatter)
            return resolved_log_path

    handler = RotatingFileHandler(
        resolved_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    setattr(handler, _HANDLER_MARKER, True)
    handler.setLevel(resolved_level)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    return resolved_log_path
