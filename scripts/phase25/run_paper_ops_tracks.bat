@echo off
setlocal enabledelayedexpansion

REM ====== Python path
set PY=C:\Python39-32\python.exe

REM ====== Date tag
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set DT=%%i

REM ====== Inputs
set TAPE=results\phase25\paper_ops\live_tape\decision_tape_%DT%.csv
set RAW_FLOW=results\phase25\analysis\005930_investor_flow_metrics.csv
set NORM_FLOW=results\phase25\paper_ops\live_tape\flow_zscore_%DT%.csv

REM ====== Outputs
set OUTA=results\phase25\paper_ops\%DT%\A_oper_w-1
set OUTB=results\phase25\paper_ops\%DT%\B_ctrl_w0

if not exist "%TAPE%" (
  echo [FAIL] tape not found: %TAPE%
  exit /b 2
)

if not exist "results\phase25\nightly\%DT%\flow_zscore.csv" (
  echo [FAIL] nightly flow_zscore.csv not found. Run nightly suite first.
  exit /b 3
)

echo [INFO] Copying verified flow_zscore from Nightly Suite...
copy /Y "results\phase25\nightly\%DT%\flow_zscore.csv" "%NORM_FLOW%" >nul

echo [INFO] TAPE=%TAPE%
echo [INFO] FLOW=%NORM_FLOW%

REM ====== Track A (Operational): Aggressive/Chase-Lock (w=-1, gap=2.0)
echo.
echo [Track A] Operational: Weight -1.0
%PY% scripts\phase24\switching_from_tape_ts.py ^
  --tape_csv "%TAPE%" ^
  --flow_metrics_csv "%NORM_FLOW%" ^
  --out_dir "%OUTA%" ^
  --gap 2.0 --weight -1.0 --min_hold_min 60 --max_switches_per_day 999 ^
  --status_json results\ops\status\switching_ts_job.json --status_every 1

if errorlevel 1 (
  echo [FAIL] Track A failed
  exit /b 10
)

REM ====== Track B (Control): Baseline (w=0, gap=2.0)
echo.
echo [Track B] Control: Weight 0.0
%PY% scripts\phase24\switching_from_tape_ts.py ^
  --tape_csv "%TAPE%" ^
  --flow_metrics_csv "%NORM_FLOW%" ^
  --out_dir "%OUTB%" ^
  --gap 2.0 --weight 0.0 --min_hold_min 60 --max_switches_per_day 999

if errorlevel 1 (
  echo [FAIL] Track B failed
  exit /b 11
)

echo [OK] Paper Ops done. Outputs:
echo  - %OUTA%
echo  - %OUTB%
exit /b 0
