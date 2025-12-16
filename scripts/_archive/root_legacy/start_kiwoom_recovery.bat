@echo off
echo ========================================================
echo Garam System Recovery (After Reboot)
echo ========================================================

:: 1. Clean Stale Locks
if exist "GARAM_Data\kiwoom_ready.flag" (
    echo [Cleaning] Removing stale lock file...
    del "GARAM_Data\kiwoom_ready.flag"
)

:: 2. Verify 32-bit Python
if not exist "C:\Python39-32\python.exe" (
    echo [ERROR] 32-bit Python not found at C:\Python39-32\python.exe
    echo Please install or fix path.
    pause
    exit
)

:: 3. Launch Ingest System
echo [Launch] Starting Kiwoom Ingest System (32-bit)...
echo [Info] Targeted Re-collection mode will be active if 'recollect_targets.txt' exists.
"C:\Python39-32\python.exe" "pipeline/ingest/run_ingest_kiwoom.py"

echo ========================================================
echo Program Terminated.
pause
