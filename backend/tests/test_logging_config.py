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
    for handler in _diagnostic_handlers():
        root_logger.removeHandler(handler)
        handler.close()
    yield
    for handler in _diagnostic_handlers():
        root_logger.removeHandler(handler)
        handler.close()


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
