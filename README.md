# wlogger

Lightweight Python logging library with color console and JSON file output.

외부 의존성 없이 Python 표준 라이브러리만 사용합니다.

## Features

- 레벨별 ANSI 컬러 콘솔 출력 (DEBUG ~ CRITICAL)
- JSON Lines 형식 파일 출력 (구조화 로깅)
- 파일 자동 로테이션 (크기 기반)
- `setup()` 한 번으로 전체 설정 완료
- Python 3.12+, 외부 의존성 없음

## Installation

```bash
uv add wlogger
# or
pip install wlogger
```

## Usage

```python
import wlogger

# 프로세스 시작 시 한 번만 호출
wlogger.setup(
    level="INFO",
    log_file="app.log",   # 생략 시 콘솔만 출력
    max_bytes=10 * 1024 * 1024,  # 기본 10MB
    backup_count=5,              # 기본 5개
)

# 각 모듈에서 로거 획득
logger = wlogger.get_logger(__name__)

logger.debug("디버그 메시지")
logger.info("서버 시작")
logger.warning("디스크 용량 부족")
logger.error("요청 처리 실패")

# 예외 정보 포함
try:
    1 / 0
except ZeroDivisionError:
    logger.critical("치명적 오류", exc_info=True)
```

### 콘솔 출력 형식

```
[2026-04-07 12:00:00] [DEBUG   ] [myapp] 디버그 메시지
[2026-04-07 12:00:00] [INFO    ] [myapp] 서버 시작
[2026-04-07 12:00:00] [WARNING ] [myapp] 디스크 용량 부족
[2026-04-07 12:00:00] [ERROR   ] [myapp] 요청 처리 실패
```

### 파일 출력 형식 (JSON Lines)

```json
{"timestamp": "2026-04-07T12:00:00", "level": "INFO", "logger": "myapp", "message": "서버 시작"}
{"timestamp": "2026-04-07T12:00:00", "level": "ERROR", "logger": "myapp", "message": "요청 처리 실패"}
{"timestamp": "2026-04-07T12:00:00", "level": "CRITICAL", "logger": "myapp", "message": "치명적 오류", "exc_info": "Traceback ..."}
```

## API

### `wlogger.setup()`

```python
def setup(
    level: str = "INFO",
    log_file: str | None = None,
    console_level: str | None = None,
    file_level: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    console_stream: TextIO | None = None,
) -> None
```

루트 로거를 설정한다. 재호출 시 기존 핸들러를 닫고 교체한다.

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `level` | `"INFO"` | 로그 레벨 (`"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`) |
| `log_file` | `None` | 파일 출력 경로. `None`이면 콘솔만 출력 |
| `console_level` | `None` | 콘솔 전용 레벨. 생략 시 `level` 사용 |
| `file_level` | `None` | 파일 전용 레벨. 생략 시 `level` 사용 |
| `max_bytes` | `10485760` | 로그 파일 최대 크기 (bytes) |
| `backup_count` | `5` | 보관할 로테이션 파일 수 |
| `console_stream` | `None` | 콘솔 출력 대상. 생략 시 `sys.stderr` |

콘솔 핸들러는 항상 **stderr**로 출력한다 — 로그는 진단용 출력이므로, 애플리케이션이 stdout으로 내보내는 실제 결과물(파이프, 스크립팅, JSON 출력 등)과 섞이지 않는다.

색상 코드는 출력 대상이 실제 터미널일 때(`isatty()`)만 붙는다. 파일로 리다이렉트되거나 파이프로 연결된 경우, 또는 `NO_COLOR` 환경변수가 설정된 경우 색상 없이 출력된다.

### `wlogger.get_logger()`

```python
def get_logger(name: str) -> logging.Logger
```

이름으로 로거를 반환한다. `logging.getLogger(name)` 의 래퍼.

## 개발 및 테스트

```bash
# 의존성 동기화 (pytest 포함, dev 그룹)
uv sync

# 테스트 실행
uv run pytest
```

`pytest`는 `dev` 의존성 그룹으로만 선언되어 있다. `uv run pytest`는 프로젝트 전용 `.venv`(현재 패키지가 editable로 설치된 환경)에서 실행되므로, 시스템에 별도로 설치된 `pytest`와 섞이지 않는다.

## Build & Publish (PyPI)

### 1. 빌드

```bash
uv build
```

`dist/` 디렉토리에 wheel/sdist 파일이 생성됩니다:

```
dist/
├── wlogger-<version>-py3-none-any.whl
└── wlogger-<version>.tar.gz
```

### 2. TestPyPI 업로드 (권장)

```bash
uv publish \
  --publish-url https://test.pypi.org/legacy/ \
  --token <testpypi-token>
```

업로드 후 설치 확인:

```bash
pip install -i https://test.pypi.org/simple/ wlogger
```

### 3. PyPI 업로드

```bash
uv publish --token <pypi-token>
```

토큰은 환경변수로 관리하는 것을 권장합니다:

```bash
export UV_PUBLISH_TOKEN=<pypi-token>

uv publish
```

### 4. 설치

```bash
uv add wlogger
# or
pip install wlogger
```
