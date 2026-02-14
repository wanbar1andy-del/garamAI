@echo off
set PY=C:\Python39-32\python.exe

REM 날짜 폴더 (YYYYMMDD)
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set DT=%%i

set OUT=results\phase25\nightly\%DT%
set TAPE=results\phase24\tape\decision_tape.csv
set BUILT=results\phase25\nightly\%DT%\flow_metrics_built.csv

REM NOTE: BUILT가 다른 위치라면 여기만 바꾸면 됩니다.

%PY% scripts\phase25\nightly_suite_v2.py ^
  --python_exe %PY% ^
  --switching_py scripts\phase24\switching_from_tape_ts.py ^
  --tape_csv %TAPE% ^
  --flow_metrics_built_csv %BUILT% ^
  --out_dir %OUT% ^
  --gaps "1.5,2.0,2.5" ^
  --weights="-2,-1,-0.5,0,0.5,1,2" ^
  --min_holds "60" ^
  --caps "999" ^
  --top_k 20

echo.
echo DONE. Open:
echo  - %OUT%\report_v2.md
echo  - %OUT%\grid_v2.csv
echo  - %OUT%\paper_ops_candidates.json
