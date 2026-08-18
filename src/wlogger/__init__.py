import logging
from collections.abc import Callable
from contextlib import ExitStack
from typing import Literal, TextIO

from .handler import is_wlogger_handler, make_console_handler, make_file_handler

__all__ = ["LogLevel", "get_logger", "setup"]

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# 로그 레벨 매핑 (문자열 -> 정수)
_LEVELS: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def _to_numeric(lvl: LogLevel | str) -> int:
    try:
        return _LEVELS[lvl.upper()]
    except KeyError:
        raise ValueError(f"유효하지 않은 로그 레벨: {lvl!r}") from None


def setup(
    level: LogLevel = "INFO",
    log_file: str | None = None,
    console_level: LogLevel | None = None,
    file_level: LogLevel | None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    console_stream: TextIO | None = None,
    json_default: Callable[[object], object] | None = str,
) -> None:
    """루트 로거를 설정한다. 프로세스 시작 시 한 번만 호출하면 된다.

    Args:
        level: 전체 기본 로그 레벨. console_level/file_level이 없으면 이 레벨이 적용됨.
        log_file: 파일 출력 경로. None이면 콘솔만 출력.
        console_level: 콘솔 전용 레벨. 생략 시 level 사용.
        file_level: 파일 전용 레벨. 생략 시 level 사용.
        max_bytes: 로그 파일 최대 크기 (bytes). 기본 10MB.
        backup_count: 보관할 로테이션 파일 수. 기본 5개.
        console_stream: 콘솔 출력 대상 스트림. 생략 시 sys.stderr.
        json_default: JSON으로 변환할 수 없는 extra 값의 변환 함수. 기본값은 str.
    """
    if max_bytes <= 0:
        raise ValueError(f"max_bytes must be > 0, got {max_bytes}")
    if backup_count < 0:
        raise ValueError(f"backup_count must be >= 0, got {backup_count}")

    root_lvl = _to_numeric(level)
    c_lvl = _to_numeric(console_level) if console_level is not None else root_lvl
    f_lvl = _to_numeric(file_level) if file_level is not None else root_lvl

    root = logging.getLogger()
    unrelated_levels = [
        handler.level
        for handler in root.handlers
        if not is_wlogger_handler(handler) and handler.level != logging.NOTSET
    ]
    with ExitStack() as stack:
        new_handlers = [
            make_console_handler(c_lvl, stream=console_stream),
        ]
        stack.callback(new_handlers[0].close)
        if log_file is not None:
            file_handler = make_file_handler(
                log_file,
                f_lvl,
                max_bytes,
                backup_count,
                json_default=json_default,
            )
            new_handlers.append(file_handler)
            stack.callback(file_handler.close)

        for handler in list(root.handlers):
            if is_wlogger_handler(handler):
                root.removeHandler(handler)
                handler.close()

        for handler in new_handlers:
            root.addHandler(handler)

        # 기존 외부 핸들러가 놓치지 않도록 필요한 최소 레벨을 유지한다.
        handler_levels = [c_lvl, f_lvl] if log_file else [c_lvl]
        root.setLevel(min([*handler_levels, *unrelated_levels]))
        stack.pop_all()


def get_logger(name: str) -> logging.Logger:
    """이름으로 로거를 반환한다.

    Args:
        name: 로거 이름. 보통 __name__ 을 전달한다.

    Returns:
        logging.Logger 인스턴스
    """
    return logging.getLogger(name)
