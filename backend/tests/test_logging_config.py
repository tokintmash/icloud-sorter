import logging
from logging.handlers import RotatingFileHandler

import pytest

from backend.logging_config import configure_logging


def _diagnostic_handlers() -> list[logging.Handler]:
    return [
        handler
        for handler in logging.getLogger().handlers
        if getattr(handler, "_icloud_sorter_diagnostic_handler", False)
    ]


@pytest.fixture(autouse=True)
def clean_diagnostic_handlers():
    root_logger = logging.getLogger()
    original_level = root_logger.level
    for handler in _diagnostic_handlers():
        root_logger.removeHandler(handler)
        handler.close()
    yield
    for handler in _diagnostic_handlers():
        root_logger.removeHandler(handler)
        handler.close()
    root_logger.setLevel(original_level)


def test_configure_logging_creates_log_directory_and_file_handler(tmp_path):
    log_path = tmp_path / "logs" / "app.log"

    result = configure_logging(log_path=log_path)

    handlers = _diagnostic_handlers()
    assert result == log_path
    assert log_path.parent.is_dir()
    assert len(handlers) == 1
    assert isinstance(handlers[0], RotatingFileHandler)
    assert log_path.exists()


def test_configure_logging_is_idempotent(tmp_path):
    log_path = tmp_path / "logs" / "app.log"

    configure_logging(log_path=log_path)
    first_handlers = _diagnostic_handlers()
    configure_logging(log_path=log_path)

    assert _diagnostic_handlers() == first_handlers
    assert len(first_handlers) == 1


def test_default_logging_excludes_debug_records(tmp_path, monkeypatch):
    log_path = tmp_path / "logs" / "app.log"
    monkeypatch.delenv("ICLOUD_SORTER_DEBUG_LOGS", raising=False)
    configure_logging(log_path=log_path)

    logger = logging.getLogger("backend.tests.diagnostic")
    logger.debug("debug should be filtered")
    logger.info("info should be written")
    for handler in _diagnostic_handlers():
        handler.flush()

    contents = log_path.read_text(encoding="utf-8")
    assert "info should be written" in contents
    assert "debug should be filtered" not in contents


def test_debug_logging_requires_explicit_opt_in(tmp_path, monkeypatch):
    log_path = tmp_path / "logs" / "app.log"
    monkeypatch.setenv("ICLOUD_SORTER_DEBUG_LOGS", "1")
    configure_logging(log_path=log_path)

    logger = logging.getLogger("backend.tests.diagnostic")
    logger.debug("debug should be written")
    for handler in _diagnostic_handlers():
        handler.flush()

    assert "debug should be written" in log_path.read_text(encoding="utf-8")


def test_configure_logging_applies_rotation_limits(tmp_path):
    log_path = tmp_path / "logs" / "app.log"

    configure_logging(log_path=log_path, max_bytes=1024, backup_count=2)
    handler = _diagnostic_handlers()[0]

    assert isinstance(handler, RotatingFileHandler)
    assert handler.maxBytes == 1024
    assert handler.backupCount == 2
