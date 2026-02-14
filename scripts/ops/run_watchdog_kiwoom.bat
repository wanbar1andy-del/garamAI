@echo off
setlocal enabledelayedexpansion

REM ====== Config (Operational Hardening)
cd /d C:\garam\garam

set "WATCHDOG=scripts\ops\antigravity_watchdog.py"
set "PY32=C:\Python39-32\python.exe"
set "TARGET_SCRIPT=C:\garam\garam\pipeline\ingest\run_ingest_kiwoom.py"
set "STATUS_JSON=results\ops\status\kiwoom_ingest.json"
set "LOG_DIR=results\ops\logs\kiwoom_watchdog"

REM ====== Run Watchdog
echo [INFO] Starting Watchdog for Kiwoom Ingest...
set "CMDLINE=\"%PY32%\" \"%TARGET_SCRIPT%\""
echo CMDLINE=%CMDLINE%

"%PY32%" "%WATCHDOG%" ^
  --cmd "%CMDLINE%" ^
  --status_json "%STATUS_JSON%" ^
  --log_dir "%LOG_DIR%" ^
  --heartbeat_timeout_sec 120 ^
  --max_restart 9999

if errorlevel 1 (
  echo [FAIL] Watchdog exited with error
  pause
  exit /b 1
)
