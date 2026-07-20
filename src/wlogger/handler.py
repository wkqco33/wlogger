import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import TextIO

from .formatter import ColorFormatter, JsonFormatter


def _supports_color(stream: TextIO) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    isatty = getattr(stream, "isatty", None)
    return bool(callable(isatty) and isatty())


def make_console_handler(
    level: int = logging.DEBUG, *, stream: TextIO | None = None
) -> logging.StreamHandler:
    # Logs are diagnostic output, not program output: default to stderr so
    # stdout stays clean for whatever the application actually produces
    # (piping, scripting, JSON output, ...).
    target = stream if stream is not None else sys.stderr
    handler = logging.StreamHandler(target)
    handler.setLevel(level)
    handler.setFormatter(ColorFormatter(use_color=_supports_color(target)))
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
