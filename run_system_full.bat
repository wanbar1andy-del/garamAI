
@echo off
title GARAM SYSTEM LAUNCHER
echo ===================================================
echo [GARAM] Launching Full Trading System Environment
echo ===================================================

echo 1. Starting GPU Activity Monitor...
start "GARAM_GPU_MONITOR" cmd /k "py -3.9 scripts/monitor_gpu.py"

echo 2. Starting OSS Training Gym (Dual-Core + GPU)...
start "GARAM_OSS_GYM" cmd /k "py -3.9 scripts/train_oss_gym.py"

echo 3. Starting Data Ingestion (Short Selling)...
start "GARAM_DATA_INGEST" cmd /c "scripts\ingest_all_short.bat"

echo 4. Starting Visualizer (Charts)...
start "GARAM_VISUALIZER" cmd /k "py -3.9 scripts/hero_visualizer_gui.py"

echo.
echo [OK] All subsystems launched in separate windows.
echo You can close this window.
pause
