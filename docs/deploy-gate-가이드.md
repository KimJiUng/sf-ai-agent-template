# Deploy Gate 가이드

## 목적

Deploy Gate는 배포 전 규칙 위반과 Org 충돌을 자동 검사하는 사전 게이트입니다.
Review Gate는 수정한 파일에서 기술부채 후보를 자동 수집하여 사용자가 배포 승인 전에 확인할 수 있게 합니다.
Hard Gate 위반이 발견되면 즉시 종료하여 배포를 중단하고, Review Gate 항목은 `review-needed` 상태로 누적합니다.

## 실행 방법

```bash
# 작업 시작 전 로컬 백업 + Org 시작 snapshot
npm run work:snapshot -- --target-org YOUR_ORG_ALIAS --label 작업명 --files force-app/main/default/classes/Sample.cls

# 기술부채 후보 수집
npm run debt:scan

# OS 공통 규칙 검증
npm run deploy-gate:check

# 사용자 승인 후 OS 공통 안전 배포
npm run deploy:safe -- --target-org YOUR_ORG_ALIAS
```

Windows 전용 래퍼:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy-gate-check.ps1
powershell -ExecutionPolicy Bypass -File scripts/deploy-with-gate.ps1 -TargetOrg YOUR_ORG_ALIAS
```

macOS/Linux 전용 래퍼:

```bash
bash scripts/deploy-gate-check.sh
bash scripts/deploy-with-gate.sh YOUR_ORG_ALIAS
```

## 검사 규칙 소스

- 규칙 파일: `config/deploy-gate-rules.json`
- OS 공통 실행 래퍼: `scripts/run_deploy_gate.js`
- 검증 스크립트: `scripts/deploy_gate_check.py`
- 작업 snapshot 생성: `scripts/work_snapshot.py`
- 기술부채 후보 수집: `scripts/debt_scan.py`
- 배포 래퍼: `scripts/deploy-with-gate.ps1`, `scripts/deploy-with-gate.sh`

## 현재 검사 항목

정적 Deploy Gate (`npm run deploy-gate:check`)

1. 필수 문서/스크립트 파일 존재 여부
2. 금지 패턴(예: 외부 디자인 툴 참조) 검사
3. Markdown 로컬 링크 무결성
4. Markdown 파일 인코딩(UTF-8) 형식 검사
5. 텍스트 계약 문구 존재 여부
6. 디자인 인덱스 문서 내 경로 실존 여부

배포 직전 org-aware 검사 (`npm run deploy:safe`)

1. 배포 대상 텍스트 소스가 UTF-8로 읽히는지 확인
2. 배포 대상 한글 텍스트 안에 깨짐 흔적이 끼어 있지 않은지 확인
3. 작업 시작 Org snapshot, 현재 로컬, 배포 직전 Org 최신본을 3-way 비교
4. 로컬에서 안 바꾼 파일인데 Org만 바뀐 경우 Org 최신본을 로컬에 반영
5. 서로 다른 메소드/라인을 바꾼 경우 자동 병합
6. 같은 메소드/라인 또는 삭제/의도 불명 변경은 배포 중단

Review Gate (`npm run debt:scan`)

1. 작업 snapshot에 포함된 영향 파일만 스캔
2. `TODO`, `FIXME`, `pending-confirm`, 임시/우회/가정, 하드코딩된 Salesforce ID 의심을 후보로 수집
3. `docs/technical-debt/register.md`에 `review-needed` 상태로 누적
4. 배포를 자동 차단하지는 않지만, 사용자 승인 전에 반드시 보고

## 실패 시 동작

- Deploy Gate가 위반 항목을 규칙 단위로 출력
- 종료 코드 `2`로 즉시 종료
- 배포 명령을 실행하지 않음
- 사용자에게 위반 내용을 즉시 보고하고 수정 방향을 제안

## 규칙 확장 방법

1. `config/deploy-gate-rules.json`에 검사 규칙 추가
2. 필요한 경우 `scripts/deploy_gate_check.py`에 검사 로직 추가
3. `npm run deploy-gate:check`로 로컬 검증 후 배포 파이프라인 반영
