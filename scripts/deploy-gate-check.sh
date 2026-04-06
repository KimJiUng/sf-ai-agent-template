#!/usr/bin/env bash
# ============================================================
# Deploy Gate — 정적 검사
# 배포 전 규칙 위반을 자동 검사하는 사전 게이트
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_PATH="${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"

# --- 색상 ---
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# --- 위반 수집 ---
declare -a VIOLATIONS=()

add_violation() {
    local rule="$1" path="$2" detail="$3"
    VIOLATIONS+=("[$rule] $path: $detail")
}

# --- 설정 로드 ---
CONFIG_PATH="$ROOT_PATH/config/deploy-gate-rules.json"
if [[ ! -f "$CONFIG_PATH" ]]; then
    add_violation "config" "config/deploy-gate-rules.json" "Deploy Gate rules file is missing."
    echo -e "${RED}Deploy Gate check failed: deployment will be stopped.${NC}"
    printf '%s\n' "${VIOLATIONS[@]}"
    exit 2
fi

# --- Python 헬퍼 호출 ---
# 정적 검사의 핵심 로직은 Python으로 위임
python3 "$SCRIPT_DIR/deploy_gate_check.py" "$ROOT_PATH"
exit $?
