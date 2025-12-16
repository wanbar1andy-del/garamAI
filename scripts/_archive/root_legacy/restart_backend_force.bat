@echo off
echo [Restarting Backend] Killing old processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq api/server_fixed.py"
taskkill /F /IM python.exe /FI "WINDOWTITLE eq scripts/run_live_dge_final.py"

echo [Restarting Backend] Starting API Server...
start "api/server_fixed.py" /min cmd /c "set SERVER_PORT=5003 && python api/server_fixed.py"

echo [Restarting Backend] Starting Live Runner...
start "scripts/run_live_dge_final.py" /min cmd /c "python scripts/run_live_dge_final.py"

echo [Done] Backend restarted.
timeout /t 5
