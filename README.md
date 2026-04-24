# Salesforce + AI Agent 프로젝트 템플릿

Claude와 Codex 같은 AI 에이전트와 함께 Salesforce 프로젝트를 체계적으로 개발하기 위한 프로젝트 템플릿입니다.

## 사용법

### 1. 템플릿 적용

Claude 또는 Codex에서 아래와 같이 요청합니다:

```
이 저장소를 참고해서 내 프로젝트에 적용해줘 → https://github.com/KimJiUng/sf-claude-template
```

AI 에이전트가 `BOOTSTRAP.md`를 읽고 현재 프로젝트에 구조, 설정, 규칙을 자동 적용합니다.
Claude는 `CLAUDE.md`, Codex는 `AGENTS.md`를 작업 규칙 진입점으로 사용합니다.

### 2. 평소 작업 요청

템플릿 적용 후에는 평소처럼 AI에게 작업을 요청하면 됩니다.

```
AccountService에 고객 등급 계산 로직 추가해줘.
대상 Org는 devOrg야.
```

AI는 바로 배포하지 않고 아래 순서로 진행합니다.

```text
요구사항 확인
→ 영향 파일 정리
→ 작업 전 local-backup + org-start snapshot 생성
→ 구현
→ 자체리뷰
→ 기술부채 후보 자동 수집
→ 생성/수정/삭제 목록과 작업 요약 보고
→ 사용자 승인 대기
→ 승인 후 Org 충돌 검사 및 배포
```

### 3. 사람이 확인할 것

AI가 구현을 마치면 배포 전에 다음 내용을 보고합니다.

| 확인 항목 | 의미 |
|---|---|
| 생성/수정/삭제 파일 | 이번 작업으로 바뀐 파일 목록 |
| 작업 요약 | 어떤 요구사항을 어떻게 반영했는지 |
| 검증 결과 | Deploy Gate, 테스트, 스크립트 검사 결과 |
| 자동 병합 여부 | Org 최신본과 로컬 변경을 비교해 병합한 파일 |
| 기술부채 후보 | `review-needed` 상태로 쌓인 확인 필요 항목 |

보고 내용을 확인한 뒤에만 배포를 승인합니다.

```
승인. devOrg에 배포해.
```

수정이 더 필요하면 배포 대신 지시합니다.

```
기술부채 후보 TD-003은 지금 수정하고, 배포는 아직 하지 마.
```

명시적으로 승인하지 않으면 AI는 Org에 배포하지 않습니다.

## 포함 기능

| 기능 | 설명 |
|---|---|
| **영속 컨텍스트** | `context/` 폴더로 세션 간 작업 상태를 유지합니다. 채팅이 끊겨도 이전 작업을 이어갈 수 있습니다. |
| **오케스트레이션** | 요구사항 → 기술설계 → 작업 snapshot → 구현 → 자체리뷰 → 사용자 승인 → 배포의 단계별 절차를 따릅니다. |
| **작업 Snapshot** | 작업 전 로컬 백업과 Org 시작본을 `backups/`에 생성하여 복구와 3-way 비교 기준으로 사용합니다. |
| **Deploy Gate** | 배포 전 규칙 위반과 Org 충돌을 검사하고, 안전한 비충돌 변경은 자동 병합합니다. |
| **Review Gate** | 수정한 파일에서 기술부채 후보를 자동 수집하여 `review-needed` 상태로 누적합니다. |
| **하네스 질문** | 요구사항이 불명확하면 구현 전에 AI 에이전트가 먼저 질문하여 방향을 확인합니다. |
| **실패 플레이북** | 반복되는 실패 패턴을 기록하고 재발을 방지합니다. |

## 디렉토리 구조

```
├── AGENTS.md               ← Codex의 작업 규칙 (핵심)
├── CLAUDE.md               ← Claude의 작업 규칙 (핵심)
├── BOOTSTRAP.md            ← AI 에이전트가 프로젝트에 적용할 때 읽는 지침
├── context/                ← 영속 컨텍스트 (세션 간 작업 메모리)
├── docs/                   ← 아키텍처, 디자인, 요구사항 문서
├── scripts/                ← Deploy Gate 검사/배포 스크립트
├── config/                 ← 검사 규칙, Scratch Org 설정
├── force-app/              ← Salesforce 소스 코드
├── manifest/               ← 배포 매니페스트
├── backups/                ← 작업 전 로컬 백업 및 Org snapshot
└── logs/                   ← 실패 기록 보관소
```

## 사전 요구사항

- [Salesforce CLI (sf)](https://developer.salesforce.com/tools/salesforcecli)
- [Node.js](https://nodejs.org/) (LWC 테스트/Lint용)
- [Python 3](https://www.python.org/) (Deploy Gate 검사용)

## 주요 명령

```bash
npm run work:snapshot -- --target-org <ORG_ALIAS> --label <작업명> --files <파일...>
npm run debt:scan
npm run deploy-gate:check
npm run deploy:safe -- --target-org <ORG_ALIAS>
```

`deploy:safe`는 사용자가 생성/수정/삭제 목록과 Review Gate 결과를 확인하고 명시적으로 승인한 뒤에만 실행합니다.

## 작업 Snapshot

작업 전 snapshot은 AI가 소스 수정 전에 생성합니다.

```bash
npm run work:snapshot -- --target-org devOrg --label account-grade --files force-app/main/default/classes/AccountService.cls
```

생성되는 구조:

```text
backups/
└── YYYYMMDD-HHMMSS-account-grade/
    ├── local-backup/   # 작업 전 로컬 파일 복구/참고용
    ├── org-start/      # 작업 시작 시점의 Org 최신본
    └── manifest.json   # 작업 기준 파일과 대상 Org 기록
```

`local-backup`은 복구용이고, `org-start`는 배포 전 3-way 비교 기준입니다.
AI는 `backups/` 아래 파일을 생성하고 참고할 수 있지만 수정하거나 삭제하지 않습니다.

## 배포 안전 흐름

배포 승인 후 `deploy:safe`는 다음 순서로 동작합니다.

1. 정적 Deploy Gate 검사
2. 배포 직전 Org 최신본 조회
3. `org-start`, 현재 로컬, 배포 직전 Org 최신본 3-way 비교
4. 서로 다른 영역 변경은 자동 병합
5. 같은 메소드/라인 충돌 또는 삭제/의도 불명 변경은 배포 중단
6. 충돌이 없으면 Salesforce 배포 실행

예를 들어 Org에서는 `methodB`를 새로 추가했고 로컬에서는 `methodA`만 수정했다면 자동 병합할 수 있습니다.
반대로 Org와 로컬이 같은 메소드를 서로 다르게 수정했다면 배포를 멈추고 사람에게 보고합니다.

## 기술부채 Review Gate

기술부채는 배포를 무조건 막는 항목이 아니라, 사람이 확인해야 할 후보로 누적합니다.

```bash
npm run debt:scan
```

Review Gate는 작업 영향 파일에서 다음 패턴을 찾습니다.

- `TODO`, `FIXME`, `pending-confirm`
- 임시/우회/가정/확인 필요 문구
- 하드코딩된 Salesforce ID 의심

발견한 후보는 `docs/technical-debt/register.md`에 `review-needed` 상태로 쌓입니다.
사람은 나중에 확인하면서 `accepted`, `resolved`, `skipped` 중 하나로 정리하면 됩니다.

## 직접 실행용 래퍼

PowerShell/Bash 래퍼도 함께 제공됩니다.

- Windows: `npm run deploy-gate:check:ps`, `npm run deploy:safe:ps -- -TargetOrg <ORG_ALIAS>`
- macOS/Linux: `npm run deploy-gate:check:sh`, `npm run deploy:safe:sh -- <ORG_ALIAS>`

## 라이선스

MIT License — [LICENSE](LICENSE) 참고
