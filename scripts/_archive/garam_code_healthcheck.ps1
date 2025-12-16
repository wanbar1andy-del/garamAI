<#
.SYNOPSIS
  GARAM 코드 헬스케어 스크립트
  - 파이썬 캐시/찌꺼기 정리
  - 기본 정합성(컴파일) 체크
#>

param(
    [switch]$DeepClean  # 추가 로그/임시파일 정리 옵션
)

$ErrorActionPreference = "Stop"

Write-Host "=== GARAM Code Healthcheck ===" -ForegroundColor Cyan

# 1) 프로젝트 루트 이동 (scripts 폴더 기준 상위)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir   = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $rootDir

Write-Host "Project root: $rootDir" -ForegroundColor DarkCyan
Write-Host ""

# 2) Git 상태 요약 출력 (참고용)
if (Test-Path ".git") {
    Write-Host ">> git status -sb" -ForegroundColor Yellow
    git status -sb
    Write-Host ""
}

# 3) 파이썬 캐시/찌꺼기 정리
Write-Host ">> Cleaning Python caches (__pycache__, *.pyc, .pytest_cache, .mypy_cache)..." -ForegroundColor Yellow

$cleanPatterns = @(
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".mypy_cache"
)

foreach ($pattern in $cleanPatterns) {
    Get-ChildItem -Path $rootDir -Recurse -Force -Include $pattern -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

if ($DeepClean) {
    Write-Host ">> DeepClean enabled: cleaning logs/tmp..." -ForegroundColor Yellow

    if (Test-Path "logs") {
        Get-ChildItem "logs" -Recurse -Include "*.log" -ErrorAction SilentlyContinue |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path "tmp") {
        Get-ChildItem "tmp" -Recurse -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Python cache cleanup done."
Write-Host ""

# 4) 파이썬 코드 컴파일 체크 (Syntax Health Check)
Write-Host ">> Running python -m compileall (syntax check)..." -ForegroundColor Yellow

try {
    python -m compileall -q .
    Write-Host "Syntax check OK." -ForegroundColor Green
} catch {
    Write-Host "Syntax check FAILED. 위 에러를 먼저 해결하세요." -ForegroundColor Red
    exit 1
}

Write-Host ""

# 5) (선택) 핵심 스크립트 스모크 테스트 훅 자리
# 필요해지면 아래 부분에 실제 스모크 명령을 추가하면 됨.
# ex)
# if (Test-Path "scripts\run_champion_rule_v3.py") {
#     Write-Host ">> Smoke test: Champion v3 Regime profile ..." -ForegroundColor Yellow
#     python scripts\run_champion_rule_v3.py --config config\profile_champion_v3_regime.yaml --smoke
# }

Write-Host "=== GARAM Code Healthcheck COMPLETED ===" -ForegroundColor Cyan
