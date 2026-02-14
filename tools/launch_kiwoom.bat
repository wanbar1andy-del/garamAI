@echo off
chcp 65001
set PYTHONPATH=%~dp0..
echo [INFO] Launching Garam Kiwoom Ingest GUI (32-bit)...
echo [INFO] Python: C:\Python39-32\python.exe
"C:\Python39-32\python.exe" "%~dp0..\pipeline\ingest\run_ingest_kiwoom.py"
pause
