@echo off
cd /d C:\garam\garam
echo [AUTO-EVOLVE] Starting Daily Cycle %DATE% %TIME% >> logs\scheduler.log
python scripts\daily_optimizer.py >> logs\scheduler.log 2>&1
echo [AUTO-EVOLVE] Cycle End >> logs\scheduler.log
