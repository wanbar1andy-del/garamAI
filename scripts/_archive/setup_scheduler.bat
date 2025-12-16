@echo off
REM GARAM Task Scheduler Setup
REM Windows 작업 스케줄러 자동 설정

echo ====================================
echo GARAM Task Scheduler Setup
echo ====================================
echo.

REM Check admin権한
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Administrator 권한 필요!
    echo 관리자 권한으로 다시 실행하세요.
    pause
    exit /b 1
)

echo [1/4] 기존 작업 제거 중...
schtasks /delete /tn "GARAM_AutoStart" /f >nul 2>&1
schtasks /delete /tn "GARAM_Watchdog" /f >nul 2>&1
schtasks /delete /tn "GARAM_Telegram" /f >nul 2>&1

echo [2/4] Python 경로 확인...
set PYTHON_PATH=python
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Python not found in PATH
    echo Python 경로를 수동으로 설정하세요.
    pause
)

echo [3/4] 작업 생성 중...

REM Task 1: Auto-Start (매일 08:30)
schtasks /create /tn "GARAM_AutoStart" /tr "%PYTHON_PATH% c:\garam\garam\scripts\auto_start.py" /sc daily /st 08:30 /ru SYSTEM /f
if %errorLevel% neq 0 (
    echo ERROR: Auto-Start 작업 생성 실패
) else (
    echo   [OK] Auto-Start 작업 생성 완료
)

REM Task 2: Watchdog (시스템 시작 시)
schtasks /create /tn "GARAM_Watchdog" /tr "%PYTHON_PATH% c:\garam\garam\scripts\simple_watchdog.py" /sc onstart /ru SYSTEM /f
if %errorLevel% neq 0 (
    echo ERROR: Watchdog 작업 생성 실패
) else (
    echo   [OK] Watchdog 작업 생성 완료
)

REM Task 3: Telegram Listener (시스템 시작 시)
schtasks /create /tn "GARAM_Telegram" /tr "%PYTHON_PATH% c:\garam\garam\scripts\telegram_minimal.py" /sc onstart /ru SYSTEM /f
if %errorLevel% neq 0 (
    echo ERROR: Telegram 작업 생성 실패
) else (
    echo   [OK] Telegram 작업 생성 완료
)

echo [4/4] 작업 확인...
echo.
schtasks /query /tn "GARAM_AutoStart" /fo list
echo.
schtasks /query /tn "GARAM_Watchdog" /fo list
echo.
schtasks /query /tn "GARAM_Telegram" /fo list
echo.

echo ====================================
echo 설정 완료!
echo ====================================
echo.
echo 생성된 작업:
echo   1. GARAM_AutoStart  - 매일 08:30 자동 시작
echo   2. GARAM_Watchdog   - 시스템 부팅 시 감시 시작
echo   3. GARAM_Telegram   - 시스템 부팅 시 Telegram Bot 시작
echo.
echo 수동 실행 테스트:
echo   schtasks /run /tn "GARAM_AutoStart"
echo   schtasks /run /tn "GARAM_Watchdog"
echo   schtasks /run /tn "GARAM_Telegram"
echo.
pause
