@echo off
title Garam OSS Brain Mock Trading
cls
echo ========================================================
echo   GARAM OSS BRAIN MOCK TRADING
echo ========================================================
echo.
echo [1] Starting Kiwoom Data Ingestion (Background)...
start "Garam Ingest" scripts\run_ingest_32bit.bat

echo.
echo [2] Launching OSS Brain (Neuro Link Activated)...
echo     - Model: core/active_config/neuro_brain_state.pth
echo     - Mode: Mock Trading (Real-time Feed)
echo.
timeout /t 5 >nul

py -3.9 scripts/run_live_oss_brain.py

pause
