import logging
from typing import Literal

from .handler import make_console_handler, make_file_handler

__all__ = ["setup", "get_logger"]

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup(
    level: LogLevel = "INFO",
    log_file: str | None = None,
    console_level: LogLevel | None = None,
    file_level: LogLevel | None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """루트 로거를 설정한다. 프로세스 시작 시 한 번만 호출하면 된다.

    Args:
        level: 전체 기본 로그 레벨. console_level/file_level이 없으면 이 레벨이 적용됨.
        log_file: 파일 출력 경로. None이면 콘솔만 출력.
        console_level: 콘솔 전용 레벨. 생략 시 level 사용.
        file_level: 파일 전용 레벨. 생략 시 level 사용.
        max_bytes: 로그 파일 최대 크기 (bytes). 기본 10MB.
        backup_count: 보관할 로테이션 파일 수. 기본 5개.
    """
    def _to_numeric(lvl: LogLevel | str) -> int:
        num = logging.getLevelName(lvl.upper())
        if not isinstance(num, int):
            raise ValueError(f"유효하지 않은 로그 레벨: {lvl!r}")
        return num

    root_lvl = _to_numeric(level)
    c_lvl = _to_numeric(console_level) if console_level else root_lvl
    f_lvl = _to_numeric(file_level) if file_level else root_lvl

    root = logging.getLogger()
    if root.handlers:
        root.handlers.clear()

    # 루트 레벨은 가장 낮은 것으로 설정 (핸들러에서 각각 필터링)
    root.setLevel(min(root_lvl, c_lvl, f_lvl) if log_file else c_lvl)

    # 콘솔 핸들러 추가
    root.addHandler(make_console_handler(c_lvl))

    # 파일 핸들러 추가 (설정된 경우)
    if log_file is not None:
        root.addHandler(
            make_file_handler(log_file, f_lvl, max_bytes, backup_count)
        )


def get_logger(name: str) -> logging.Logger:
    """이름으로 로거를 반환한다.

    Args:
        name: 로거 이름. 보통 __name__ 을 전달한다.

    Returns:
        logging.Logger 인스턴스
    """
    return logging.getLogger(name)
