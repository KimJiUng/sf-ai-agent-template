<#
.SYNOPSIS
    안전 배포 — Deploy Gate 통과 후에만 sf deploy 실행
.DESCRIPTION
    1단계: 정적 Deploy Gate
    2단계: Org-aware 검사
    3단계: Salesforce 배포
.PARAMETER TargetOrg
    배포 대상 org alias (필수)
.EXAMPLE
    .\deploy-with-gate.ps1 -TargetOrg myOrg
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$TargetOrg,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$DeployArgs
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootPath  = (Resolve-Path (Join-Path $ScriptDir "..")).Path

$SfDeployArgs = @()
for ($i = 0; $i -lt $DeployArgs.Count; $i++) {
    $arg = $DeployArgs[$i]
    if ($arg -eq "--session-dir") {
        $i++
        continue
    }
    if ($arg -like "--session-dir=*") {
        continue
    }
    if ($arg) {
        $SfDeployArgs += $arg
    }
}

# --- 1단계: 정적 Deploy Gate ---
Write-Host "Running Deploy Gate pre-deploy validation..." -ForegroundColor Cyan
& powershell -ExecutionPolicy Bypass -File "$ScriptDir\deploy-gate-check.ps1" -RootPath $RootPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "Validation failed. Deployment will be stopped." -ForegroundColor Red
    exit $LASTEXITCODE
}

# --- 2단계: Org-aware 검사 ---
Write-Host "Validation passed. Running org-aware pre-deploy check..." -ForegroundColor Green
$orgCheckArgs = @($RootPath, $TargetOrg) + ($DeployArgs | Where-Object { $_ })
python "$ScriptDir\deploy_org_check.py" @orgCheckArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "Org-aware check failed. Deployment will be stopped." -ForegroundColor Red
    exit $LASTEXITCODE
}

# --- 3단계: Salesforce 배포 ---
Write-Host "All checks passed. Starting Salesforce deployment..." -ForegroundColor Green
$sfArgs = @("project", "deploy", "start", "--target-org", $TargetOrg) + $SfDeployArgs
& sf @sfArgs
exit $LASTEXITCODE
