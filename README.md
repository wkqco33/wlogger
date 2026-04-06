# wlogger

Lightweight Python logging library with color console and JSON file output.

외부 의존성 없이 Python 표준 라이브러리만 사용하며, 내부 pypiserver를 통해 배포됩니다.

## Features

- 레벨별 ANSI 컬러 콘솔 출력 (DEBUG ~ CRITICAL)
- JSON Lines 형식 파일 출력 (구조화 로깅)
- 파일 자동 로테이션 (크기 기반)
- `setup()` 한 번으로 전체 설정 완료
- Python 3.12+, 외부 의존성 없음

## Installation

```bash
uv add wlogger --index-url http://<pypiserver-host>
# 또는
pip install wlogger --index-url http://<pypiserver-host>
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
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None
```

루트 로거를 설정한다. 재호출 시 기존 핸들러를 교체한다.

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `level` | `"INFO"` | 로그 레벨 (`"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`) |
| `log_file` | `None` | 파일 출력 경로. `None`이면 콘솔만 출력 |
| `max_bytes` | `10485760` | 로그 파일 최대 크기 (bytes) |
| `backup_count` | `5` | 보관할 로테이션 파일 수 |

### `wlogger.get_logger()`

```python
def get_logger(name: str) -> logging.Logger
```

이름으로 로거를 반환한다. `logging.getLogger(name)` 의 래퍼.

## Build & Deploy

### 1. 빌드

```bash
uv build
```

`dist/` 디렉토리에 두 파일이 생성됩니다:

```
dist/
├── wlogger-0.1.0-py3-none-any.whl
└── wlogger-0.1.0.tar.gz
```

### 2. pypiserver 업로드

```bash
uv publish \
  --publish-url http://<pypiserver-host>/simple/ \
  --username <user> \
  --password <pass> \
  --no-attestations \
  --allow-insecure-host <pypiserver-host>
```

| 옵션 | 이유 |
|------|------|
| `--publish-url` | pypiserver의 업로드 엔드포인트 (보통 `/simple/`) |
| `--no-attestations` | pypiserver는 attestation을 지원하지 않아 기본값이면 오류 발생 |
| `--allow-insecure-host` | HTTP(비HTTPS) 호스트에 연결할 때 필요 |

인증 정보는 환경변수로 관리하는 것을 권장합니다:

```bash
export UV_PUBLISH_USERNAME=<user>
export UV_PUBLISH_PASSWORD=<pass>

uv publish \
  --publish-url http://<pypiserver-host>/simple/ \
  --no-attestations \
  --allow-insecure-host <pypiserver-host>
```

### 3. 사용 측 프로젝트에서 설치

```bash
uv add wlogger \
  --index-url http://<pypiserver-host>/simple/ \
  --allow-insecure-host <pypiserver-host>
```

또는 `pyproject.toml`에 인덱스를 등록해두면 매번 플래그 없이 사용할 수 있습니다:

```toml
[[tool.uv.index]]
name = "internal"
url = "http://<pypiserver-host>/simple/"
```
