import json
import logging
import traceback

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
        level = f"{record.levelname:<8}"
        msg = record.getMessage()

        line = f"[{timestamp}] {color}[{level}]{_RESET} [{record.name}] {msg}"

        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)

        return line


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(data, ensure_ascii=False)
