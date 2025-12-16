# GARAM Dashboard 바로가기 생성 스크립트
# 브라우저 하이재킹 우회용

Write-Host "Creating GARAM Dashboard shortcut..." -ForegroundColor Cyan

# 바탕화면 경로
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "GARAM Dashboard.lnk"

# 바로가기 생성
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

# Edge 브라우저 경로
$EdgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# Edge가 없으면 기본 경로 시도
if (-not (Test-Path $EdgePath)) {
    $EdgePath = "msedge.exe"
}

$Shortcut.TargetPath = $EdgePath
$Shortcut.Arguments = "http://localhost:5000 --new-window"
$Shortcut.Description = "GARAM Trading Dashboard"
$Shortcut.WorkingDirectory = "C:\garam\garam"
$Shortcut.Save()

Write-Host "✅ Shortcut created: $ShortcutPath" -ForegroundColor Green
Write-Host ""
Write-Host "Usage:" -ForegroundColor Yellow
Write-Host "  Double-click 'GARAM Dashboard' on Desktop" -ForegroundColor White
Write-Host "  This will open http://localhost:5000 directly" -ForegroundColor White
