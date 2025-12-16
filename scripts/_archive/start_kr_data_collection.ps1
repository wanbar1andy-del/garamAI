# Kiwoom 데이터 수집 시작 스크립트
# 사용법: .\start_kr_data_collection.ps1 [-TestMode]

param(
    [switch]$TestMode = $false,
    [int]$MaxIterations = 0,
    [double]$MaxHours = 24.0
)

$ErrorActionPreference = "Stop"

# 경로 설정
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$pythonScript = Join-Path $scriptDir "schedule_kr_data_collection.py"
$logPath = "g:\내 드라이브\garamdata\logs\scheduler.log"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "     GARAM Kiwoom 데이터 수집 스케줄러" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Python 스크립트 존재 확인
if (-not (Test-Path $pythonScript)) {
    Write-Host "❌ 오류: Python 스크립트를 찾을 수 없습니다: $pythonScript" -ForegroundColor Red
    exit 1
}

# 로그 디렉토리 생성
$logDir = Split-Path -Parent $logPath
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    Write-Host "✓ 로그 디렉토리 생성: $logDir" -ForegroundColor Green
}

# 명령행 인자 구성
$pythonArgs = @()

if ($TestMode) {
    Write-Host "🧪 테스트 모드로 실행 중..." -ForegroundColor Yellow
    Write-Host "   - 최대 반복: 10회" -ForegroundColor Gray
    $pythonArgs += "--max-iterations", "10"
} else {
    Write-Host "🚀 프로덕션 모드로 실행 중..." -ForegroundColor Green
    
    if ($MaxIterations -gt 0) {
        Write-Host "   - 최대 반복: $MaxIterations 회" -ForegroundColor Gray
        $pythonArgs += "--max-iterations", "$MaxIterations"
    }
    
    if ($MaxHours -gt 0) {
        Write-Host "   - 최대 실행 시간: $MaxHours 시간" -ForegroundColor Gray
        $pythonArgs += "--max-runtime-hours", "$MaxHours"
    }
}

Write-Host ""
Write-Host "📋 설정:" -ForegroundColor Cyan
Write-Host "   - 스케줄: 매일 15:35 KST" -ForegroundColor Gray
Write-Host "   - 로그: $logPath" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 Ctrl+C를 눌러 안전하게 종료할 수 있습니다" -ForegroundColor Yellow
Write-Host ""

# Python 스크립트 실행
try {
    Write-Host "▶ 스케줄러 시작..." -ForegroundColor Green
    & python $pythonScript @pythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ 스케줄러가 정상적으로 종료되었습니다" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ 스케줄러가 오류와 함께 종료되었습니다 (코드: $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host ""
    Write-Host "❌ 오류 발생: $_" -ForegroundColor Red
    exit 1
}
