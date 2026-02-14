
@echo off
title GARAM AI CENTER (OFFLINE MODE)
echo ===================================================
echo [GARAM] AI Training & Monitoring (No Kiwoom)
echo ===================================================

echo 1. Starting GPU Monitor...
start "GARAM_GPU" cmd /k "py -3.9 scripts/monitor_gpu.py"

echo 2. Starting OSS Gym (Offline Training)...
start "GARAM_GYM" cmd /k "py -3.9 scripts/train_oss_gym.py"

echo.
echo [NOTE] Data Collection is PAUSED to prevent Kiwoom conflicts.
echo Focus on the AI training output now.
pause
