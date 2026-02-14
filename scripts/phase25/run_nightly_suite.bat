@echo off
chcp 65001
set PY=C:\Python39-32\python.exe

REM UTF-8 콘솔 강제
call scripts\ops\run_utf8_env.bat %PY% scripts\phase25\nightly_suite.py ^
  --raw_opt10059_csv results\phase25\flow\investor\005930\opt10059_005930_2025.csv ^
  --tape_csv results\phase24\tape\decision_tape.csv ^
  --out_dir results\phase25\nightly\%DATE:~0,4%%DATE:~5,2%%DATE:~8,2% ^
  --signal 외국인투자자_ratio_z20 ^
  --gap_list 1.5,2.0,2.5 ^
  --weight_list 0,0.5,1,2,3 ^
  --min_hold_list 0,10,60 ^
  --cap_list 6,12,999 ^
  --top_n 3 ^
  --regime_thr 1.0
