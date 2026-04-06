import logging

from .handler import make_console_handler, make_file_handler

__all__ = ["setup", "get_logger"]

_setup_done = False


def setup(
    level: str = "INFO",
    log_file: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """루트 로거를 설정한다. 프로세스 시작 시 한 번만 호출하면 된다.

    Args:
        level: 로그 레벨 문자열 ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        log_file: 파일 출력 경로. None이면 콘솔만 출력.
        max_bytes: 로그 파일 최대 크기 (bytes). 기본 10MB.
        backup_count: 보관할 로테이션 파일 수. 기본 5개.
    """
    global _setup_done

    numeric_level = logging.getLevelName(level.upper())
    if not isinstance(numeric_level, int):
        raise ValueError(f"유효하지 않은 로그 레벨: {level!r}")

    root = logging.getLogger()

    if _setup_done:
        root.handlers.clear()

    root.setLevel(numeric_level)
    root.addHandler(make_console_handler(numeric_level))

    if log_file is not None:
        root.addHandler(
            make_file_handler(log_file, numeric_level, max_bytes, backup_count)
        )

    _setup_done = True


def get_logger(name: str) -> logging.Logger:
    """이름으로 로거를 반환한다.

    Args:
        name: 로거 이름. 보통 __name__ 을 전달한다.

    Returns:
        logging.Logger 인스턴스
    """
    return logging.getLogger(name)
