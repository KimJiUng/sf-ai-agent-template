# Salesforce + Claude 프로젝트 템플릿

Claude(AI)와 함께 Salesforce 프로젝트를 체계적으로 개발하기 위한 프로젝트 템플릿입니다.

## 사용법

Claude(Cursor, Claude Code 등)에서 아래와 같이 요청하면 됩니다:

```
이 저장소를 참고해서 내 프로젝트에 적용해줘 → https://github.com/YOUR_ORG/sf-claude-template
```

Claude가 `BOOTSTRAP.md`를 읽고 현재 프로젝트에 구조, 설정, 규칙을 자동 적용합니다.

## 포함 기능

| 기능 | 설명 |
|---|---|
| **영속 컨텍스트** | `context/` 폴더로 세션 간 작업 상태를 유지합니다. 채팅이 끊겨도 이전 작업을 이어갈 수 있습니다. |
| **오케스트레이션** | 요구사항 → 기술설계 → 디자인 → 구현 → 자체리뷰 → 배포의 단계별 절차를 자동으로 따릅니다. |
| **Deploy Gate** | 배포 전 규칙 위반(인코딩, 링크 무결성, 금지 패턴 등)을 자동 검사하여 안전한 배포를 보장합니다. |
| **하네스 질문** | 요구사항이 불명확하면 구현 전에 Claude가 먼저 질문하여 방향을 확인합니다. |
| **실패 플레이북** | 반복되는 실패 패턴을 기록하고 재발을 방지합니다. |

## 디렉토리 구조

```
├── CLAUDE.md               ← Claude의 작업 규칙 (핵심)
├── BOOTSTRAP.md            ← Claude가 프로젝트에 적용할 때 읽는 지침
├── context/                ← 영속 컨텍스트 (세션 간 작업 메모리)
├── docs/                   ← 아키텍처, 디자인, 요구사항 문서
├── scripts/                ← Deploy Gate 검사/배포 스크립트
├── config/                 ← 검사 규칙, Scratch Org 설정
├── force-app/              ← Salesforce 소스 코드
├── manifest/               ← 배포 매니페스트
└── logs/                   ← 실패 기록 보관소
```

## 사전 요구사항

- [Salesforce CLI (sf)](https://developer.salesforce.com/tools/salesforcecli)
- [Node.js](https://nodejs.org/) (LWC 테스트/Lint용)
- [Python 3](https://www.python.org/) (Deploy Gate 검사용)

## 라이선스

MIT License — [LICENSE](LICENSE) 참고
