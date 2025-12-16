:: c:\garam\garam\start_garam.bat
:: WHY: GARAM 전체 시스템을 "한 번만" 깨끗하게 올리기 위한 단일 스타트 스크립트

@echo off
setlocal

:: ==============================
:: CONFIG
:: ==============================
set SERVER_PORT=5003

:: 32-bit Python for Kiwoom (MUST be real 32-bit)
if "%GARAM_PYTHON_32%"=="" set GARAM_PYTHON_32=C:\Python39-32\python.exe

:: Verify Architecture
"%GARAM_PYTHON_32%" -c "import struct,sys; print('GARAM_PYTHON_32 =', sys.executable); print('ARCH =', struct.calcsize('P')*8, 'bit')"

:: Main Python (Unified to 32-bit for now)
set PYTHON_MAIN=%GARAM_PYTHON_32%

echo [GARAM] Startup script initialized.
echo   - Kiwoom Python : %GARAM_PYTHON_32%
echo   - Main Python   : %PYTHON_MAIN%
echo   - Server Port   : %SERVER_PORT%
echo.

:: ==============================
:: UAC: Request admin once
:: ==============================
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo [GARAM] Requesting administrative privileges...
    goto UACPrompt
) else (
    goto gotAdmin
)

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" del "%temp%\getadmin.vbs"
    pushd "%CD%"
    cd /D "%~dp0"

echo [GARAM] Running with administrative privileges.
echo.

:: ==============================
:: 0. AI Core (Ollama)
:: ==============================
echo [0/3] Launching AI Core (Ollama)...
start "Ollama AI" ollama serve

:: ==============================
:: 1. Kiwoom Login (32-bit)
:: ==============================
echo [1/3] Launching Kiwoom Login UI...
echo        Using Python: %GARAM_PYTHON_32%
start "Garam Gateway (Ingest)" "%GARAM_PYTHON_32%" pipeline\ingest\run_ingest_kiwoom.py

:: ==============================
:: 2. API / Dashboard Server
:: ==============================
echo [2/3] Launching Dashboard Server...
echo        Using Python: %PYTHON_MAIN%
start "Garam Server" "%PYTHON_MAIN%" api\server_fixed.py

:: ==============================
:: 3. Live Strategy Runner
:: ==============================
echo [3/4] Launching Trading Engine (Orchestrator)...
echo        Using Python: %PYTHON_MAIN%
start "Garam Brain" "%PYTHON_MAIN%" run_trading_engine.py

:: ==============================
:: 4. Open Browser (Correct Port)
:: ==============================
echo [4/4] Opening Dashboard in browser...
echo        URL: http://localhost:%SERVER_PORT%
timeout /t 5 /nobreak >nul
start http://localhost:%SERVER_PORT%

echo.
echo [GARAM] Startup Initiated. Please complete Kiwoom login in the popup window.
echo [GARAM] If the page is blank, CHECK the URL is EXACTLY:
echo         http://localhost:%SERVER_PORT%
echo.
pause
endlocal
