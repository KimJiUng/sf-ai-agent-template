<#
.SYNOPSIS
    Deploy Gate — 정적 검사
.DESCRIPTION
    배포 전 규칙 위반을 자동 검사하는 사전 게이트.
    Python 헬퍼(deploy_gate_check.py)를 호출합니다.
#>
param(
    [string]$RootPath
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not $RootPath) {
    $RootPath = (Resolve-Path (Join-Path $ScriptDir "..")).Path
}

$ConfigPath = Join-Path $RootPath "config\deploy-gate-rules.json"
if (-not (Test-Path $ConfigPath)) {
    Write-Host "[config] config/deploy-gate-rules.json: Deploy Gate rules file is missing." -ForegroundColor Red
    exit 2
}

python "$ScriptDir\deploy_gate_check.py" $RootPath
exit $LASTEXITCODE
