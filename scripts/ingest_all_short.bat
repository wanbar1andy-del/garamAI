
@echo off
echo [GARAM] Starting Full Short Selling Ingestion (Resume-Mode)
echo -----------------------------------------------------------

echo [Step 1] Verifying/Collecting 2025 Data...
C:\Python39-32\python.exe scripts/ingest_short_selling_2025.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 2025 Failed. Continue anyway...
)

echo.
echo [Step 2] Verifying/Collecting 2026 Data...
C:\Python39-32\python.exe scripts/ingest_short_selling_2026.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 2026 Failed. Continue anyway...
)

echo.
echo [Step 3] Collecting 2024 Data...
C:\Python39-32\python.exe scripts/ingest_short_selling_2024.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 2024 Failed.
)

echo.
echo [FINISH] All Data Collection Complete.
pause
