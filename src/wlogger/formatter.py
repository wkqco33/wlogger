import json
import logging

_RESET = "\033[0m"
_BOLD = "\033[1m"

_LEVEL_COLORS = {
    logging.DEBUG: "\033[90m",     # 회색
    logging.INFO: "\033[32m",      # 초록
    logging.WARNING: "\033[33m",   # 노랑
    logging.ERROR: "\033[31m",     # 빨강
    logging.CRITICAL: "\033[1;31m", # 굵은 빨강
}


class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelno, "")
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        level = record.levelname
        msg = record.getMessage()

        line = f"[{timestamp}] {color}[{level}]{_RESET} [{record.name}] {msg}"

        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)

        return line


class JsonFormatter(logging.Formatter):
    # 표준 속성 셋을 클래스 상수로 정의하여 매번 생성하지 않도록 최적화
    _STANDARD_ATTRS = {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message"
    }

    def format(self, record: logging.LogRecord) -> str:
        data: dict = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "process": record.process,
            "thread": record.threadName,
            "file": f"{record.filename}:{record.lineno}",
        }

        # record.__dict__에서 표준 속성이 아닌 것들(extra)을 추출하여 포함
        for key, value in record.__dict__.items():
            if key not in self._STANDARD_ATTRS:
                data[key] = value

        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(data, ensure_ascii=False)
