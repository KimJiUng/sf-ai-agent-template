# BOOTSTRAP — Claude용 프로젝트 적용 지침

> 이 문서는 Claude(AI)가 읽고 실행하는 지침서입니다.
> 사용자가 이 저장소 URL을 제공하며 "내 프로젝트에 적용해줘"라고 요청하면, 이 문서의 절차를 따릅니다.

## 0. 사전 확인 — 사용자에게 질문

적용을 시작하기 전에 사용자에게 아래 항목을 확인합니다:

1. **프로젝트명** — `sfdx-project.json`, `package.json` 등에 사용할 이름 (예: "MyCompany CRM")
2. **대상 프로젝트 경로** — 적용할 프로젝트의 루트 경로 (현재 열린 프로젝트라면 생략 가능)
3. **기존 Salesforce 프로젝트 여부** — 이미 `sfdx-project.json`이 있는 프로젝트인지 확인

## 1. 적용 순서

아래 순서대로 파일과 폴더를 생성합니다. 이미 존재하는 파일은 **병합 규칙**을 따릅니다.

### 1-1. 설정 파일 (플레이스홀더 치환 필요)

아래 파일에서 `{{PROJECT_NAME}}`을 사용자가 알려준 프로젝트명으로 치환합니다:

| 파일 | 치환 대상 |
|---|---|
| `sfdx-project.json` | `"name"` 값 |
| `package.json` | `"description"` 값 |
| `config/project-scratch-def.json` | `"orgName"` 값 |

### 1-2. 설정 파일 (그대로 복사)

이 저장소의 내용을 그대로 대상 프로젝트에 생성합니다:

- `.gitignore`
- `.gitattributes`
- `.forceignore`
- `.prettierrc`
- `.prettierignore`
- `eslint.config.js`
- `jest.config.js`
- `.vscode/settings.json`
- `config/deploy-gate-rules.json`
- `manifest/package.xml`

### 1-3. CLAUDE.md (핵심 — 그대로 복사)

프로젝트 루트에 `CLAUDE.md`를 생성합니다. 이 파일이 이후 모든 Claude 세션의 작업 규칙이 됩니다.

### 1-4. 영속 컨텍스트 (`context/`)

아래 파일을 모두 생성합니다. 내용은 이 저장소의 템플릿을 그대로 사용합니다:

- `context/README.md`
- `context/project_state.md`
- `context/session_summary.md`
- `context/decisions.md`
- `context/open_tasks.md`
- `context/failure_playbook.md`

### 1-5. 문서 (`docs/`)

- `docs/architecture.md`
- `docs/deploy-gate-가이드.md`
- `docs/orchestration-가이드.md`
- `docs/design/README.md`
- `docs/design/design-artifacts.md`
- `docs/design/specs/.gitkeep`
- `docs/requirements/README.md`
- `docs/requirements/features/.gitkeep`
- `docs/technical-debt/register.md`
- `docs/technical-debt/items/.gitkeep`

### 1-6. 배포 스크립트 (`scripts/`)

- `scripts/deploy-gate-check.ps1`
- `scripts/deploy-with-gate.ps1`
- `scripts/deploy-gate-check.sh`
- `scripts/deploy-with-gate.sh`
- `scripts/deploy_gate_check.py`
- `scripts/deploy_org_check.py`

### 1-7. Salesforce 소스 디렉토리 (`force-app/`)

빈 디렉토리 구조를 `.gitkeep`과 함께 생성합니다:

```
force-app/main/default/
  classes/
  triggers/
  lwc/
  aura/
  objects/
  layouts/
  permissionsets/
  tabs/
  staticresources/
  customMetadata/
  labels/
  flexipages/
  flows/
```

### 1-8. 로그 디렉토리

- `logs/failures/.gitkeep`

## 2. 기존 프로젝트 병합 규칙

이미 Salesforce 프로젝트가 있는 경우:

| 파일 | 병합 방법 |
|---|---|
| `sfdx-project.json` | 기존 `packageDirectories`, `sourceApiVersion` 유지. 없는 필드만 추가 |
| `package.json` | 기존 `dependencies` 유지. `devDependencies`는 병합 (버전 충돌 시 높은 버전). `scripts`는 기존 것을 유지하고 `deploy-gate:check`, `deploy:safe`, `precommit` 추가 |
| `.gitignore` | 기존 내용 유지 + 템플릿 항목 중 누락된 것 추가 |
| `.forceignore` | 기존 내용 유지 + 템플릿 항목 중 누락된 것 추가 |
| `force-app/` | 기존 소스 절대 건드리지 않음. 없는 하위 폴더만 추가 |
| `CLAUDE.md` | 기존 것이 있으면 사용자에게 덮어쓸지 확인 |

**절대 하지 말 것:**
- 기존 소스 코드 수정/삭제
- 기존 `package.json`의 `dependencies` 덮어쓰기
- 기존 `.gitignore` 규칙 제거

## 3. 적용 후 검증

1. `npm install` 실행 (package.json이 새로 생성되었거나 devDependencies가 변경된 경우)
2. Deploy Gate 검사 실행:
   ```powershell
   python scripts/deploy_gate_check.py .
   ```
3. 통과하면 적용 완료. 실패하면 위반 항목을 수정합니다.

## 4. 적용 완료 후 안내

사용자에게 아래 내용을 안내합니다:

1. `CLAUDE.md`가 모든 Claude 세션의 작업 규칙으로 동작합니다
2. `context/` 폴더가 세션 간 영속 컨텍스트로 사용됩니다
3. 배포 전 `npm run deploy-gate:check`로 규칙 검증이 필요합니다
4. `context/project_state.md`에 현재 프로젝트 상태를 기록해두면 다음 세션에서 이어서 작업할 수 있습니다
