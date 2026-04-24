# 기술부채 등록부

## 유형 분류

| 유형 | 설명 | 수집 방식 |
|---|---|---|
| `code-debt` | 코드 품질/구조 부채, 하드코딩 의심, 리팩토링 필요 | Review Gate 자동 수집 또는 리뷰 중 수동 추가 |
| `pending-confirm` | 고객사 확인 대기 또는 변경 가능성 높은 요구사항 | 요구사항 분석 단계 선등록 또는 Review Gate 자동 수집 |
| `assumption` | 정보 부족으로 가정 기반 구현한 항목 | 구현 단계 선등록 또는 Review Gate 자동 수집 |
| `external-dep` | 외부 시스템/API 스펙 미확정 | 기술설계 단계 선등록 |

## 상태 값

| 상태 | 의미 |
|---|---|
| `review-needed` | 자동 수집 또는 선등록된 후보. 사람이 확인해야 함 |
| `accepted` | 기술부채로 인정하고 나중에 처리 |
| `resolved` | 처리 완료 |
| `skipped` | 확인 결과 처리 불필요 |

## 등록부

| ID | 상태 | 유형 | 제목 | 영향 | 발견 위치 | 등록일 | 처리 방침 |
|----|------|------|------|------|-----------|--------|-----------|
<!-- review-needed 항목은 자동 스캔으로 누적됩니다. -->

## 운영 규칙

- 요구사항 분석 시 불확실 항목이 발견되면 `review-needed` + `pending-confirm`으로 즉시 등록합니다.
- 배포 전 `npm run debt:scan` 또는 `npm run deploy-gate:check`로 작업 영향 파일을 자동 스캔합니다.
- 자동 수집된 항목은 삭제하지 않고 `accepted`, `resolved`, `skipped` 중 하나로 상태를 변경합니다.
- Review Gate 항목은 배포를 자동 차단하지 않지만, 사용자 승인 전에 반드시 확인합니다.
- 확정 부채에 상세 설명이 필요할 때만 `docs/technical-debt/items/TD-xxx.md`를 추가합니다.
