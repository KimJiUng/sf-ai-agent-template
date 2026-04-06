# 컨텍스트 운영 규칙

이 폴더는 구현 사이클의 영속 컨텍스트(작업 메모리)입니다.
채팅 기록은 휘발성이므로 영속 컨텍스트로 사용하지 않습니다.

## 디렉토리 원칙

- `context/` = 현재 상태(항상 읽음)
- `logs/` = 기록 보관소(기본 작업에서 읽지 않음)

## 작성 언어 원칙

- `context/*.md`, `logs/failures/*.md`, 관련 운영 README의 제목과 서술형 본문은 기본적으로 한글로 작성합니다.
- 코드 식별자, 파일 경로, 명령어, API/컴포넌트 이름처럼 원문 유지가 필요한 기술 식별자는 그대로 둘 수 있습니다.
- 한글 문서를 수정할 때는 UTF-8 인코딩을 유지하고, 저장 직후 문자가 깨지지 않았는지 확인합니다.

## 필수 컨텍스트 파일

- `context/project_state.md`
- `context/session_summary.md`
- `context/decisions.md`
- `context/open_tasks.md`
- `context/failure_playbook.md`

## 사이클 시작 시 (필수 읽기)

1. `docs/architecture.md`
2. `context/project_state.md`
3. `context/failure_playbook.md`
4. `context/open_tasks.md`
5. `context/decisions.md`
6. `context/session_summary.md`

작업 시작 전에 현재 작업이 과거 실패 패턴(`failure_playbook`)과 충돌하는지 확인합니다.

## 사이클 종료 시 (필수 갱신)

의미 있는 작업 단계(분석/구현/테스트) 종료 시 아래 파일을 갱신합니다.

1. `context/project_state.md`
2. `context/session_summary.md`
3. `context/decisions.md` (의미 있는 설계 의사결정이 있을 때만)
4. `context/open_tasks.md` (신규 작업 추가, 완료 작업 제거)
5. `context/failure_playbook.md` (반복 가능한 실패 패턴이 확인된 경우만)

## 압축 규칙

- 요약은 짧고 중복 없이 작성합니다.
- 오래된 진술은 제거하고 모순은 해소합니다.
- `context` 파일은 수백 줄 이하로 유지합니다.
- 기록 항목: 현재 목표, 구현 상태, 변경 파일, 테스트, 남은 작업, 리스크
- 큰 로그나 전체 diff는 저장하지 않습니다.

## 실패 패턴 플레이북 규칙

- `context/failure_playbook.md`는 반복되는 실패 패턴의 오답노트입니다.
- 최대 80개 항목(`## FP-XX ...`)만 유지합니다.
- 단순 오타/포맷 문제는 기록하지 않습니다.
- 항목은 `문제 패턴`, `금지 사항`, `올바른 방식`으로 짧고 명확하게 작성합니다.

## 실패 로그 규칙

기록 대상:

- 잘못된 구현 방향
- 아키텍처 규칙 위반
- 반복될 가능성이 있는 구현 실수

기록 위치: `logs/failures/YYYY-MM/failure_YYYY-MM-DD.md`

로그 형식: 날짜, 실패 내용, 원인, 올바른 접근 방식, 감지 방법, 관련 파일

로그 작성 후 반복 패턴이면 `context/failure_playbook.md`를 추가/업데이트합니다.
