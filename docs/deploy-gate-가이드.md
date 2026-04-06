# Deploy Gate 가이드

## 목적

Deploy Gate는 배포 전 규칙 위반을 자동 검사하는 사전 게이트입니다.
위반이 발견되면 항목을 출력하고 즉시 종료(비정상 종료 코드)하여 배포를 중단합니다.

## 실행 방법

```powershell
# 규칙 검증만 실행
powershell -ExecutionPolicy Bypass -File scripts/deploy-gate-check.ps1

# 검증 통과 시에만 배포
powershell -ExecutionPolicy Bypass -File scripts/deploy-with-gate.ps1 -TargetOrg YOUR_ORG_ALIAS
```

NPM 스크립트:

```bash
npm run deploy-gate:check
npm run deploy:safe -- -TargetOrg YOUR_ORG_ALIAS
```

## 검사 규칙 소스

- 규칙 파일: `config/deploy-gate-rules.json`
- 검증 스크립트: `scripts/deploy_gate_check.py`
- 배포 래퍼: `scripts/deploy-with-gate.ps1`

## 현재 검사 항목

정적 Deploy Gate (`deploy-gate-check.sh`)

1. 필수 문서/스크립트 파일 존재 여부
2. 금지 패턴(예: 외부 디자인 툴 참조) 검사
3. Markdown 로컬 링크 무결성
4. Markdown 파일 인코딩(UTF-8) 형식 검사
5. 텍스트 계약 문구 존재 여부
6. 디자인 인덱스 문서 내 경로 실존 여부

배포 직전 org-aware 검사 (`deploy-with-gate.sh`)

1. 배포 대상 텍스트 소스가 UTF-8로 읽히는지 확인
2. 배포 대상 한글 텍스트 안에 깨짐 흔적이 끼어 있지 않은지 확인
3. 대상 org 현재본을 retrieve 해서 git base ref와 3-way 비교
4. 로컬에서 안 바꾼 파일인데 org만 바뀐 경우 org 현재본을 payload에 반영
5. Apex Class에서 같은 메소드를 로컬과 org가 함께 바꾼 경우 배포 중단
6. 서로 다른 메소드/라인을 바꾼 경우 임시 payload에서 자동 병합 후 배포

## 실패 시 동작

- Deploy Gate가 위반 항목을 규칙 단위로 출력
- 종료 코드 `2`로 즉시 종료
- 배포 명령을 실행하지 않음
- 사용자에게 위반 내용을 즉시 보고하고 수정 방향을 제안

## 규칙 확장 방법

1. `config/deploy-gate-rules.json`에 검사 규칙 추가
2. 필요한 경우 `scripts/deploy_gate_check.py`에 검사 로직 추가
3. `./scripts/deploy-gate-check.sh`로 로컬 검증 후 배포 파이프라인 반영
