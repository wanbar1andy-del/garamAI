@echo off
title Garam System Starter
cls
echo ========================================================
echo   GARAM TRADING SYSTEM - STARTUP
echo ========================================================
echo.
echo [1] Checking Environment...
echo.

:: Optional: Verify 32-bit Python exists
if not exist "C:\Python39-32\python.exe" (
    echo [ERROR] 32-bit Python not found at C:\Python39-32\python.exe
    echo Please install 32-bit Python 3.9.
    pause
    exit
)

echo [2] Starting Data Ingestion (Kiwoom GUI)...
:: Launch Ingestion in a new window/process so this script continues
start "Garam Ingest" scripts\run_ingest_32bit.bat

echo [3] Starting Progress Monitor...
:: Wait a bit for GUI to launch
timeout /t 5 >nul
start "Garam Monitor" python scripts\monitor_ingestion.py

echo.
echo ========================================================
echo   SYSTEM LAUNCHED
echo   - Ingestion GUI should appear.
echo   - Monitor window should track progress.
echo ========================================================
echo.
pause
