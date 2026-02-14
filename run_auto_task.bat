
@echo off
title GARAM AUTO-PILOT
echo [System] Cleaning up workspace...

:: 1. Start GPU Monitor (Minimized to save space, but visible in taskbar)
start "GARAM_GPU" /MIN cmd /c "py -3.9 scripts/monitor_gpu.py & exit"

:: 2. Start OSS Gym (Main Active Window)
:: Using /WAIT so this script pauses until Gym executes. 
:: Redirect output to log file for monitoring
echo [System] Training AI... (Check logs/training_progress.log for details)
start "GARAM_GYM" /WAIT cmd /c "py -3.9 -u scripts/train_oss_gym.py > logs\training_progress.log 2>&1"

:: 3. Cleanup after Gym finishes
echo [System] Training Complete. Closing monitors...
taskkill /F /FI "WINDOWTITLE eq GARAM_GPU" >nul 2>&1

echo [Done] All tasks finished.
timeout /t 3
exit
