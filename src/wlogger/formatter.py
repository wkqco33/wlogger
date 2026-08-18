import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import ClassVar, cast, override

_RESET = "\033[0m"
_BOLD = "\033[1m"

_LEVEL_COLORS = {
    logging.DEBUG: "\033[90m",  # 회색
    logging.INFO: "\033[32m",  # 초록
    logging.WARNING: "\033[33m",  # 노랑
    logging.ERROR: "\033[31m",  # 빨강
    logging.CRITICAL: "\033[1;31m",  # 굵은 빨강
}

# 콘솔 출력 정렬을 위한 최대 레벨 이름 길이
_LEVEL_WIDTH = max(len(name) for name in logging.getLevelNamesMapping())


class ColorFormatter(logging.Formatter):
    def __init__(self, *, use_color: bool = True) -> None:
        super().__init__()
        self.use_color: bool = use_color

    @override
    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(_LEVEL_WIDTH)
        msg = record.getMessage()

        if self.use_color:
            color = _LEVEL_COLORS.get(record.levelno, "")
            level_field = f"{color}[{level}]{_RESET}"
        else:
            level_field = f"[{level}]"

        line = f"[{timestamp}] {level_field} [{record.name}] {msg}"

        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        if record.stack_info:
            line += "\n" + record.stack_info

        return line


class JsonFormatter(logging.Formatter):
    _STANDARD_ATTRS: ClassVar[frozenset[str]] = frozenset(
        vars(logging.LogRecord("", logging.NOTSET, "", 0, "", (), None))
    ) | {"message"}

    def __init__(
        self, *, json_default: Callable[[object], object] | None = str
    ) -> None:
        super().__init__()
        self.json_default = json_default

    @override
    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "process": record.process,
            "thread": record.threadName,
            "file": f"{record.filename}:{record.lineno}",
        }

        record_data = cast(dict[str, object], record.__dict__)
        extra: dict[str, object] = {}
        for key, value in record_data.items():
            if key not in self._STANDARD_ATTRS:
                if key in data or key == "extra":
                    extra[key] = value
                else:
                    data[key] = value

        if extra:
            data["extra"] = extra

        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            data["stack_info"] = record.stack_info

        return json.dumps(
            data,
            ensure_ascii=False,
            allow_nan=False,
            default=self.json_default,
        )
