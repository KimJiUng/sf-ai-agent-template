# 아키텍처 기준

최종 업데이트: (프로젝트 시작 시 갱신)

## 목적

프로젝트 전반의 구현 계층과 책임 경계를 명확히 하여 품질/보안/유지보수 기준을 통일합니다.

## 계층 원칙

1. UI(LWC)는 입력/표시/상태 관리만 담당합니다.
2. 비즈니스 규칙과 검증은 Apex Service Layer에서 처리합니다.
3. 데이터 접근은 SOQL/Apex 계층에서 통제하며, UI에서 raw SOQL을 직접 생성하지 않습니다.
4. 공통 기능은 재사용 가능한 모듈(LWC 유틸/Apex 유틸)로 분리합니다.

## 품질 원칙

- Salesforce 보안 규칙(CRUD/FLS) 준수
- Bulkify 기준 준수 (Trigger/Service)
- 테스트 전략: LWC 단위 테스트 + Apex 테스트
- 배포 전 Deploy Gate 필수 통과

## 기술부채 관리 원칙

- 표준 기능 우선 원칙을 적용한다. built-in platform service를 먼저 검토하고, 필요 시 패키지 또는 low-code를 거친 뒤 마지막에 custom code를 선택한다.
- 설계 단계에서 단기 구현 편의뿐 아니라 장기 유지비, 중복 여부, 의존성, 롤백 경로를 함께 검토한다.
- UI(LWC/Aura/VF)가 비즈니스 규칙을 직접 품거나 플랫폼 order of execution을 우회하는 구현을 지양한다.
- 수용한 기술부채는 `docs/technical-debt/register.md`와 `docs/technical-debt/items/TD-xxx.md`에 기록하고, 비즈니스 영향과 상환 계획을 남긴다.

## 실패 관리 연계

- 반복 가능한 실패는 `context/failure_playbook.md`에 규칙으로 관리합니다.
- 개별 실패 상세 기록은 `logs/failures/YYYY-MM/failure_YYYY-MM-DD.md`에 남깁니다.
- 현재 살아 있는 구조적 부채와 상환 계획은 `docs/technical-debt/**`에서 관리합니다.
