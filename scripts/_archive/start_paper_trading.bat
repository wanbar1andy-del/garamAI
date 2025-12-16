@echo off
REM GARAM Paper Trading Startup Script
REM This script checks if market is open and starts paper trading

echo ========================================
echo GARAM Paper Trading Startup
echo ========================================
echo.

REM Get current time
for /f "tokens=1-3 delims=:" %%a in ('echo %time%') do (
    set hour=%%a
    set minute=%%b
)

REM Remove leading space from hour
set hour=%hour: =%

echo Current time: %hour%:%minute%
echo.

REM Check if it's after 08:50
if %hour% LSS 8 (
    echo Market not open yet. Will wait.
    timeout /t 60
    goto :EOF
)

if %hour% EQU 8 (
    if %minute% LSS 50 (
        echo Market not open yet. Will wait.
        timeout /t 60
        goto :EOF
    )
)

REM Check if it's before 16:00
if %hour% GEQ 16 (
    echo Market closed. Exiting.
    goto :EOF
)

echo Starting Paper Trading...
echo.

cd /d C:\garam\garam
python scripts\run_live_trading.py --mode paper

echo.
echo Paper Trading stopped.
pause
