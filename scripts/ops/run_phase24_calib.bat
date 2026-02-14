@echo off
@REM --- Phase 24 Calibration Snapshot ---
@REM ID: OPT90013_005930_202511_CALIB
@REM Mode: Snapshot style (Single Day call -> Retrieve Block)
@REM Period: 20251107 (Will retrieve ~20 days preceding)

call scripts\ops\run_utf8_env.bat ^
  C:\Python39-32\python.exe scripts\ops\antigravity_watchdog.py ^
  --cmd "C:\Python39-32\python.exe scripts\kiwoom\collect_tr_daily_range.py --trcode OPT90013 --rqname pgrm_daily --start_yyyymmdd 20251107 --end_yyyymmdd 20251107 --out_csv results\phase24\flow\prog\005930\prog_202511_calib.csv --spec_json configs\kiwoom\opt90013_program.json --status_json results\ops\status\kiwoom_flow_job_OPT90013_005930_202511_CALIB.json" ^
  --status_json results\ops\status\kiwoom_flow_job_OPT90013_005930_202511_CALIB.json ^
  --log_dir results\ops\logs\OPT90013_005930_202511_CALIB ^
  --heartbeat_timeout_sec 120 ^
  --max_restart 1
