@echo off
set PROJECT_ROOT=C:\garam\garam
cd /d %PROJECT_ROOT%

echo [START] Running Daily Routine... >> paper_trading.log
date /t >> paper_trading.log
time /t >> paper_trading.log

:: Use the python executable from the environment (assuming it's in path or specify absolute path)
:: Here we assume 'python' is the correct command as used in previous steps
python scripts/daily_routine.py >> paper_trading.log 2>&1

echo [END] Daily Routine Finished. >> paper_trading.log
