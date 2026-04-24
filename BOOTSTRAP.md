# BOOTSTRAP — AI 에이전트용 프로젝트 적용 지침

> 이 문서는 Claude/Codex 같은 AI 에이전트가 읽고 실행하는 지침서입니다.
> 사용자가 이 저장소 URL을 제공하며 "내 프로젝트에 적용해줘"라고 요청하면, 이 문서의 절차를 따릅니다.

## 0. 사전 요구사항 체크

프로젝트 적용 전에 아래 도구들이 설치되어 있는지 **반드시 확인**합니다.
각 도구의 명령어를 실행하여 버전을 확인하고, 설치되지 않은 항목이 있으면 사용자에게 알리고 설치 여부를 묻습니다.

### 체크 명령어

```
sf --version          # Salesforce CLI
node --version        # Node.js
npm --version         # npm (Node.js와 함께 설치됨)
python --version      # Python 3
```

### 체크 절차

1. 위 4개 명령어를 모두 실행합니다.
2. 결과를 아래 형식으로 정리하여 사용자에게 보여줍니다:

| 도구 | 상태 | 버전 |
|---|---|---|
| Salesforce CLI (sf) | 설치됨 / **미설치** | v2.x.x |
| Node.js | 설치됨 / **미설치** | v20.x.x |
| Python 3 | 설치됨 / **미설치** | 3.x.x |

3. **미설치 항목이 있는 경우**, 사용자에게 설치할지 물어봅니다.
4. 사용자가 동의하면 아래 설치 명령어를 안내하거나 실행합니다.

### 설치 방법 (Windows)

```powershell
# Salesforce CLI
npm install -g @salesforce/cli

# Node.js (winget 사용)
winget install OpenJS.NodeJS.LTS

# Python 3 (winget 사용)
winget install Python.Python.3.12

```

### 설치 방법 (macOS)

```bash
# Homebrew가 없다면 먼저 설치
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Salesforce CLI
npm install -g @salesforce/cli

# Node.js
brew install node

# Python 3
brew install python

```

### 체크 완료 조건

- 모든 도구가 설치 확인된 후에만 다음 단계로 진행합니다.
- 설치 후에는 체크 명령어를 다시 실행하여 정상 설치를 확인합니다.
- `sf`만 미설치이고 `npm`이 있으면 `npm install -g @salesforce/cli`로 바로 설치할 수 있습니다.

## 1. 사전 확인 — 사용자에게 질문

사전 요구사항이 모두 충족된 후, 아래 항목을 사용자에게 확인합니다:

1. **프로젝트명** — `sfdx-project.json`, `package.json` 등에 사용할 이름 (예: "MyCompany CRM")
2. **작성자 이름** — 코드 주석의 Author에 사용할 이름 (예: "홍길동")
3. **작성자 이메일** — 코드 주석의 Last Modified By에 사용할 이메일 (예: "hong@example.com")
4. **대상 프로젝트 경로** — 적용할 프로젝트의 루트 경로 (현재 열린 프로젝트라면 생략 가능)
5. **기존 Salesforce 프로젝트 여부** — 이미 `sfdx-project.json`이 있는 프로젝트인지 확인
6. **사용할 AI 에이전트** — Claude, Codex, 또는 둘 다 사용할지 확인 (특별한 지시가 없으면 둘 다 적용)

## 2. 적용 순서

아래 순서대로 파일과 폴더를 생성합니다. 이미 존재하는 파일은 **병합 규칙**을 따릅니다.

### 2-1. 설정 파일 (플레이스홀더 치환 필요)

아래 파일의 플레이스홀더를 사용자 입력값으로 치환합니다:

**`{{PROJECT_NAME}}` 치환:**

| 파일 | 치환 대상 |
|---|---|
| `sfdx-project.json` | `"name"` 값 |
| `package.json` | `"description"` 값 |
| `config/project-scratch-def.json` | `"orgName"` 값 |

**`{{AUTHOR_NAME}}`, `{{AUTHOR_EMAIL}}` 치환:**

| 파일 | 치환 대상 |
|---|---|
| `docs/coding-standards.md` | 주석 템플릿의 Author, Last Modified By 등 모든 `{{AUTHOR_NAME}}`, `{{AUTHOR_EMAIL}}` |

### 2-2. 설정 파일 (그대로 복사)

이 저장소의 내용을 그대로 대상 프로젝트에 생성합니다:

- `.forceignore`
- `.prettierrc`
- `.prettierignore`
- `eslint.config.js`
- `jest.config.js`
- `.vscode/settings.json`
- `config/deploy-gate-rules.json`
- `manifest/package.xml`

### 2-3. AI 에이전트 규칙 파일 (핵심 — 그대로 복사)

프로젝트 루트에 사용할 에이전트별 규칙 파일을 생성합니다.

- Claude 사용 시: `CLAUDE.md`
- Codex 사용 시: `AGENTS.md`
- 둘 다 사용하는 경우: 두 파일 모두 생성

운영 규칙을 수정할 때는 두 파일이 서로 어긋나지 않도록 함께 갱신합니다.

### 2-4. 영속 컨텍스트 (`context/`)

아래 파일을 모두 생성합니다. 내용은 이 저장소의 템플릿을 그대로 사용합니다:

- `context/README.md`
- `context/project_state.md`
- `context/session_summary.md`
- `context/decisions.md`
- `context/open_tasks.md`
- `context/failure_playbook.md`

### 2-5. 문서 (`docs/`)

- `docs/architecture.md`
- `docs/coding-standards.md` — Salesforce 코딩 표준 및 주석 규칙 (플레이스홀더 치환 후 복사)
- `docs/deploy-gate-가이드.md`
- `docs/orchestration-가이드.md`
- `docs/design/README.md`
- `docs/design/design-artifacts.md`
- `docs/requirements/README.md`
- `docs/technical-debt/register.md`

### 2-6. 배포 스크립트 (`scripts/`)

- `scripts/deploy-gate-check.ps1`
- `scripts/deploy-with-gate.ps1`
- `scripts/deploy-gate-check.sh`
- `scripts/deploy-with-gate.sh`
- `scripts/deploy_gate_check.py`
- `scripts/deploy_org_check.py`
- `scripts/debt_scan.py`
- `scripts/work_snapshot.py`
- `scripts/run_deploy_gate.js`

### 2-7. Salesforce 소스 디렉토리 (`force-app/`)

빈 디렉토리 구조를 생성합니다:

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

### 2-8. 로그/백업 디렉토리

- `logs/failures/`
- `backups/`

## 3. 기존 프로젝트 병합 규칙

이미 Salesforce 프로젝트가 있는 경우:

| 파일 | 병합 방법 |
|---|---|
| `sfdx-project.json` | 기존 `packageDirectories`, `sourceApiVersion` 유지. 없는 필드만 추가 |
| `package.json` | 기존 `dependencies` 유지. `devDependencies`는 병합 (버전 충돌 시 높은 버전). `scripts`는 기존 것을 유지하고 `work:snapshot`, `debt:scan`, `deploy-gate:check`, `deploy:safe` 추가 |
| `.forceignore` | 기존 내용 유지 + 템플릿 항목 중 누락된 것 추가 |
| `force-app/` | 기존 소스 절대 건드리지 않음. 없는 하위 폴더만 추가 |
| `CLAUDE.md` | 기존 것이 있으면 사용자에게 덮어쓸지 확인 |
| `AGENTS.md` | 기존 것이 있으면 사용자에게 덮어쓸지 확인. 기존 Codex 지침이 있으면 충돌 없이 병합 |

**절대 하지 말 것:**
- 기존 소스 코드 수정/삭제
- 기존 `package.json`의 `dependencies` 덮어쓰기
- 백업 폴더(`backups/`)의 파일 수정/삭제

## 4. 적용 후 검증

1. `npm install` 실행 (package.json이 새로 생성되었거나 devDependencies가 변경된 경우)
2. Deploy Gate 및 Review Gate 검사 실행:
   ```bash
   npm run deploy-gate:check
   ```
3. 통과하면 적용 완료. 실패하면 위반 항목을 수정합니다.

## 5. 적용 완료 후 안내

사용자에게 아래 내용을 안내합니다:

1. `CLAUDE.md`는 Claude 세션의 작업 규칙으로 동작합니다
2. `AGENTS.md`는 Codex 세션의 작업 규칙으로 동작합니다
3. `context/` 폴더가 세션 간 영속 컨텍스트로 사용됩니다
4. Salesforce 소스 작업 전 `npm run work:snapshot -- --target-org <ORG_ALIAS> --label <작업명> --files <파일...>`로 로컬 백업과 Org snapshot을 생성합니다
5. 배포 전 `npm run deploy-gate:check`로 규칙 검증과 기술부채 후보 수집이 필요합니다
6. Org 배포는 사용자가 생성/수정/삭제 목록과 기술부채 후보를 확인하고 승인한 뒤에만 진행합니다
7. `context/project_state.md`에 현재 프로젝트 상태를 기록해두면 다음 세션에서 이어서 작업할 수 있습니다
