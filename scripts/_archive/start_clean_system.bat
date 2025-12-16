@echo off
chcp 65001
title GARAM Clean Starter

echo ========================================================
echo       GARAM SYSTEM CLEAN START
echo ========================================================

echo [1/4] Killing old processes...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM "Kiwoom Login.exe" 2>nul
timeout /t 2 /nobreak >nul

echo [2/4] Cleaning temporary files...
del "c:\garam\garam\debug_*.txt" 2>nul
del "C:\garam\garam\GARAM_Data\kiwoom_ready.flag" 2>nul

echo [3/4] Starting API Server (Port 5000)...
start "GARAM API Server" /min cmd /k "cd /d c:\garam\garam && python api/server_fixed.py"

echo [4/4] Starting Kiwoom Watchdog...
start "Kiwoom Watchdog" /min cmd /k "cd /d c:\garam\garam && python scripts/kiwoom_maintenance.py"

echo.
echo ========================================================
echo       SYSTEM STARTED SUCCESSFULLY
echo ========================================================
echo.
echo API Server: http://localhost:5000
echo Watchdog: Running (Monitoring Kiwoom)
echo.
echo Please open the Dashboard now.
pause
