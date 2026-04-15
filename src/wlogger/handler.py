import logging
import logging.handlers
import sys
from pathlib import Path

from .formatter import ColorFormatter, JsonFormatter


def make_console_handler(level: int = logging.DEBUG) -> logging.StreamHandler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(ColorFormatter())
    return handler


def make_file_handler(
    path: str,
    level: int = logging.DEBUG,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.handlers.RotatingFileHandler:
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        str(log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(JsonFormatter())
    return handler
