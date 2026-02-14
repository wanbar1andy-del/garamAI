@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
REM 필요시 Windows Terminal에서 실행 권장
cmd /c %*
