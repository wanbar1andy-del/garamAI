# Windows Task Scheduler 등록 스크립트
# PowerShell로 실행하세요

# 작업 1: 오전 10시 실행
$action1 = New-ScheduledTaskAction -Execute "C:\Python39-32\python.exe" -Argument "C:\garam\garam\auto_collect_kiwoom.py" -WorkingDirectory "C:\garam\garam"
$trigger1 = New-ScheduledTaskTrigger -Daily -At 10:00AM
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "Kiwoom_Data_Collection_AM" -Action $action1 -Trigger $trigger1 -Principal $principal -Settings $settings -Description "키움 데이터 자동 수집 (오전)"

# 작업 2: 오후 4시 실행
$action2 = New-ScheduledTaskAction -Execute "C:\Python39-32\python.exe" -Argument "C:\garam\garam\auto_collect_kiwoom.py" -WorkingDirectory "C:\garam\garam"
$trigger2 = New-ScheduledTaskTrigger -Daily -At 4:00PM

Register-ScheduledTask -TaskName "Kiwoom_Data_Collection_PM" -Action $action2 -Trigger $trigger2 -Principal $principal -Settings $settings -Description "키움 데이터 자동 수집 (오후)"

Write-Host "작업 스케줄러 등록 완료!"
Write-Host "- 오전 10시: Kiwoom_Data_Collection_AM"
Write-Host "- 오후 4시: Kiwoom_Data_Collection_PM"
Write-Host ""
Write-Host "확인: taskschd.msc 실행"
