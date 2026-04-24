#!/usr/bin/env bash
# ============================================================
# 안전 배포 — Deploy Gate 통과 후에만 sf deploy 실행
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_PATH="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- 색상 ---
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- 인자 파싱 ---
TARGET_ORG="${1:-}"
shift 2>/dev/null || true
DEPLOY_ARGS=("$@")
SF_DEPLOY_ARGS=()

skip_next=false
for arg in "${DEPLOY_ARGS[@]}"; do
    if [[ "$skip_next" == true ]]; then
        skip_next=false
        continue
    fi
    if [[ "$arg" == "--session-dir" ]]; then
        skip_next=true
        continue
    fi
    if [[ "$arg" == --session-dir=* ]]; then
        continue
    fi
    SF_DEPLOY_ARGS+=("$arg")
done

if [[ -z "$TARGET_ORG" ]]; then
    echo -e "${RED}Usage: $0 <ORG_ALIAS> [additional sf deploy args...]${NC}"
    exit 1
fi

# --- 1단계: 정적 Deploy Gate 실행 ---
echo -e "${CYAN}Running Deploy Gate pre-deploy validation...${NC}"
"$SCRIPT_DIR/deploy-gate-check.sh" "$ROOT_PATH"
CHECK_EXIT=$?

if [[ $CHECK_EXIT -ne 0 ]]; then
    echo -e "${RED}Validation failed. Deployment will be stopped.${NC}"
    exit $CHECK_EXIT
fi

# --- 2단계: Org-aware 검사 (Python) ---
echo -e "${GREEN}Validation passed. Running org-aware pre-deploy check...${NC}"
python3 "$SCRIPT_DIR/deploy_org_check.py" "$ROOT_PATH" "$TARGET_ORG" "${DEPLOY_ARGS[@]+"${DEPLOY_ARGS[@]}"}"
ORG_CHECK_EXIT=$?

if [[ $ORG_CHECK_EXIT -ne 0 ]]; then
    echo -e "${RED}Org-aware check failed. Deployment will be stopped.${NC}"
    exit $ORG_CHECK_EXIT
fi

# --- 3단계: Salesforce 배포 ---
echo -e "${GREEN}All checks passed. Starting Salesforce deployment...${NC}"

# NODE_EXTRA_CA_CERTS 설정 (시스템 인증서 사용)
if [[ -f /etc/ssl/certs/ca-certificates.crt ]]; then
    export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
fi

sf project deploy start --target-org "$TARGET_ORG" "${SF_DEPLOY_ARGS[@]+"${SF_DEPLOY_ARGS[@]}"}"
exit $?
