# AGENTS.md

이 문서는 `wlogger` 프로젝트에 기여하거나 작업을 수행하는 개발자 및 AI 에이전트를 위한 개발 가이드라인입니다.

## TDD 개발 가이드

### 1) 기본 원칙

- 기능 변경은 **테스트 먼저(실패 확인) -> 구현 -> 리팩터링** 순서로 진행합니다.
- 버그 수정은 반드시 **재현 테스트**를 먼저 작성합니다.
- 공개 API 변경 시 테스트와 README 예시를 함께 갱신합니다.

### 2) 테스트 작성 규칙

- 표준 라이브러리 기반 동작은 mocking보다 실제 객체(`LogRecord`, `TemporaryDirectory`)를 우선 사용합니다.
- 테스트 이름은 `test_<condition>_<expected>` 형태로 작성합니다.
- 한 테스트는 하나의 행위만 검증합니다 (Assertion 과다 결합 지양).
- 환경변수(`NO_COLOR` 등)를 다룰 때는 `patch.dict`로 격리합니다.

### 3) 권장 테스트 범위

- `setup()`
  - 잘못된 로그 레벨 입력 예외
  - 파라미터 경계값 검증 (`max_bytes > 0`, `backup_count >= 0`)
  - console/file 레벨 우선순위
  - 재호출 시 기존 핸들러 close/clear
- `ColorFormatter`
  - TTY/비TTY/NO_COLOR 분기
  - 레벨 패딩 정렬
  - 예외(`exc_info`) 출력 포함 여부
- `JsonFormatter`
  - 필수 필드 존재 및 타입
  - `extra` 필드 보존
  - 표준 속성 누수 방지
  - 예외(`exc_info`) 포함 시 traceback 필드 검증
- 파일 핸들러
  - 로그 파일 생성
  - 로테이션 파일 생성(`backup_count`) 동작

### 4) 작업 절차 (TDD 루프)

1. 요구사항을 테스트 케이스로 먼저 분해
2. 가장 작은 실패 테스트 1개 작성
3. `uv run pytest -q tests/test_wlogger.py -k <case>` 로 해당 케이스만 실행하여 실패 확인
4. 테스트를 통과시키는 최소 구현 적용
5. 리팩터링 후 전체 테스트(`uv run pytest -q`) 실행

### 5) PR / 리뷰 체크리스트

- [ ] 새 기능/버그에 대응하는 실패 테스트가 먼저 추가되었는가
- [ ] 테스트가 구현 세부보다 외부 동작을 검증하는가
- [ ] 테스트가 환경/시간/순서 의존 없이 재현 가능한가
- [ ] README API/예제가 코드와 일치하는가
- [ ] 전체 테스트가 로컬에서 통과하는가
- [ ] 패키지 빌드(`uv build`)가 정상 수행되는가
