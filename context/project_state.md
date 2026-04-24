# 프로젝트 상태

최종 업데이트: 2026-04-24

## 현재 목표

오픈소스 배포 가능한 Salesforce + AI Agent 프로젝트 템플릿 완성

## 구현 상태

- 프로젝트 템플릿 골격 완료 (디렉토리 구조, 설정 파일, 운영 문서)
- Claude/Codex 동시 사용을 위한 에이전트 규칙 진입점 구성 완료
- 저장소 이력 전제 제거 및 작업 snapshot 기반 변경 추적 흐름 반영
- Org snapshot 기반 3-way 비교/자동 병합 흐름 반영
- 기술부채 Review Gate 자동 누적 흐름 반영
- 오픈소스 배포 준비 완료 (회사 참조 제거, 플레이스홀더 적용, LICENSE/README/BOOTSTRAP 추가)
- Deploy Gate 정적 검사 통과 확인됨

## 변경 파일

- `AGENTS.md` — Codex용 작업 규칙 진입점
- `CLAUDE.md` — Claude용 작업 규칙 진입점
- `BOOTSTRAP.md` — AI 에이전트용 프로젝트 적용 지침서
- `README.md` — 사람용 소개 및 사용법
- `LICENSE` — MIT License (신규)
- `sfdx-project.json`, `package.json`, `config/project-scratch-def.json` — `{{PROJECT_NAME}}` 플레이스홀더 적용
- `scripts/run_deploy_gate.js` — OS 공통 Deploy Gate 실행 래퍼
- `scripts/work_snapshot.py` — 작업 전 로컬 백업 및 Org snapshot 생성
- `scripts/deploy_org_check.py` — Org snapshot 기반 3-way 비교/자동 병합
- `scripts/debt_scan.py` — 기술부채 후보 자동 수집
- `docs/technical-debt/register.md` — `review-needed` 중심 등록부로 개편

## 테스트

- Deploy Gate 정적 검사: 통과
- 스크립트 단위 테스트: 통과
- 회사 참조(KOLON) 잔존 검사: 0건

## 남은 작업

- 팀원 대상 사용 테스트 (Claude/Codex에게 URL 주고 적용 확인)
- 실제 Salesforce org 대상 snapshot/배포 리허설

## 리스크

- `CLAUDE.md`와 `AGENTS.md` 규칙이 장기적으로 어긋나지 않도록 변경 시 함께 갱신 필요
- 자동 병합은 텍스트 범위 기준이므로 의도 충돌 의심 시 사용자 확인 필요
