# Garam 프로젝트 전체 검증 스크립트
# 모든 테스트를 순차적으로 실행합니다

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Garam 프로젝트 전체 검증 시작" -ForegroundColor Cyan
Write-Host "시작 시간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$tests = @(
    @{Name="프로젝트 구조 검증"; Script="validate_garam.py"},
    @{Name="컴포넌트 단위 테스트"; Script="test_components.py"},
    @{Name="통합 백테스트 테스트"; Script="test_integration.py"},
    @{Name="파일 시스템 접근성 테스트"; Script="test_filesystem.py"}
)

$results = @()
$startTime = Get-Date

foreach ($test in $tests) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host "실행 중: $($test.Name)" -ForegroundColor Yellow
    Write-Host "스크립트: $($test.Script)" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        $output = python $test.Script 2>&1
        $exitCode = $LASTEXITCODE
        
        Write-Host $output
        
        if ($exitCode -eq 0) {
            Write-Host ""
            Write-Host "[OK] $($test.Name) 성공!" -ForegroundColor Green
            $results += @{Name=$test.Name; Success=$true}
        } else {
            Write-Host ""
            Write-Host "[FAIL] $($test.Name) 실패!" -ForegroundColor Red
            $results += @{Name=$test.Name; Success=$false}
        }
    } catch {
        Write-Host ""
        Write-Host "[ERROR] $($test.Name) 실행 중 오류: $_" -ForegroundColor Red
        $results += @{Name=$test.Name; Success=$false}
    }
}

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

# 결과 요약
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "전체 검증 결과 요약" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$passed = ($results | Where-Object { $_.Success }).Count
$total = $results.Count

foreach ($result in $results) {
    if ($result.Success) {
        Write-Host "$($result.Name.PadRight(40)): [OK] 통과" -ForegroundColor Green
    } else {
        Write-Host "$($result.Name.PadRight(40)): [FAIL] 실패" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "총 $total 개 테스트 중 $passed 개 통과" -ForegroundColor Cyan
Write-Host "소요 시간: $([math]::Round($duration, 1))초" -ForegroundColor Cyan
Write-Host "종료 시간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan

# 최종 판정
if ($passed -eq $total) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "[SUCCESS] 모든 검증 테스트가 성공했습니다!" -ForegroundColor Green
    Write-Host "Garam 프로젝트는 완벽하게 작동합니다!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "[WARNING] $($total - $passed)개 테스트에 문제가 있습니다." -ForegroundColor Yellow
    exit 1
}
