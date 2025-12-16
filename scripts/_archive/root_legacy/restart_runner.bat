@echo off
setlocal
echo [GARAM] Restarting Live Strategy Runner ONLY...
echo.

:: 1. Kill existing runner (Find by window title if possible, or python script)
:: Note: taskkill by window title is safer than killing all python
taskkill /FI "WINDOWTITLE eq Garam Live Runner" /F >nul 2>&1

echo [GARAM] Waiting for cleanup...
timeout /t 2 /nobreak >nul

:: 2. Restart Runner
set PYTHON_MAIN=C:\Python39-32\python.exe
if not "%GARAM_PYTHON_32%"=="" set PYTHON_MAIN=%GARAM_PYTHON_32%

echo [GARAM] Starting Runner...
start "Garam Live Runner" "%PYTHON_MAIN%" scripts\run_live_dge_final.py

echo.
echo [SUCCESS] Runner restarted. Kiwoom connection should remain active.
pause
