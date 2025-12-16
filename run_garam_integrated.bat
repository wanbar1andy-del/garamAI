@echo off
title GARAM Integrated Operation
echo ========================================================
echo   GARAM INTEGRATED PIPELINE - STARTUP
echo ========================================================
echo.
echo [1] Checking Environment...
echo.
if exist "config\telegram_secrets.json" (
    echo [OK] Telegram Secrets Found.
) else (
    echo [WARN] Telegram Secrets Missing. Alerts may fail.
)

echo [2] Starting Full Pipeline...
python scripts/run_full_pipeline.py
pause
