import json
import logging
from datetime import datetime, timezone
from typing import Callable, ClassVar, cast, override

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
    # 표준 속성 셋을 클래스 상수로 정의하여 매번 생성하지 않도록 최적화
    _STANDARD_ATTRS: ClassVar[frozenset[str]] = frozenset(
        {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
            "taskName",
        }
    )

    def __init__(
        self, *, json_default: Callable[[object], object] | None = str
    ) -> None:
        super().__init__()
        self.json_default = json_default

    @override
    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "process": record.process,
            "thread": record.threadName,
            "file": f"{record.filename}:{record.lineno}",
        }

        # record.__dict__에서 표준 속성이 아닌 것들(extra)을 추출하여 포함
        record_data = cast(dict[str, object], record.__dict__)
        for key, value in record_data.items():
            if key not in self._STANDARD_ATTRS:
                data[key] = value

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
