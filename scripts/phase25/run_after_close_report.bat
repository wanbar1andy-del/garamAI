@echo off
setlocal

set PY=C:\Python39-32\python.exe
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set DT=%%i

set RUNA=results\phase25\paper_ops\%DT%\A_oper_w-1
set RUNB=results\phase25\paper_ops\%DT%\B_ctrl_w0
set OUTMD=results\phase25\paper_ops\%DT%\report.md

if not exist "%RUNA%\switch_log_ts.csv" (
  echo [FAIL] missing A switch_log_ts.csv: %RUNA%
  exit /b 2
)
if not exist "%RUNB%\switch_log_ts.csv" (
  echo [FAIL] missing B switch_log_ts.csv: %RUNB%
  exit /b 3
)

%PY% scripts\phase25\paper_ops_after_close_report.py ^
  --run_dirs "%RUNA%,%RUNB%" ^
  --tape_csv "results\phase25\paper_ops\live_tape\decision_tape_%DT%.csv" ^
  --out_md "%OUTMD%"

if errorlevel 1 (
  echo [FAIL] after-close report failed
  exit /b 10
)

echo [OK] After-close report saved: %OUTMD%
exit /b 0
