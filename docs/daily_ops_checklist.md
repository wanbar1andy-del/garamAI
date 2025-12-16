- [ ] Verify the new window is running and logging "Waiting for Market Open" or processing ticks.

## Intraday Monitoring (09:00 - 15:30)

### 1. Dashboard Check

- [ ] Open `GaramUI/v4/index.html` in a browser.
- [ ] Verify **System Health** card is Green/Yellow.
- [ ] Verify **KR Feed** status is "OK" and Latency is low (< 2s).
- [ ] Monitor **Shadow Performance** panel for new trades.

### 2. Alert Monitoring

- [ ] Check `GARAM_Data/logs/alerts.log` periodically for ERRORs.

## Evening Routine (15:40 - 16:00)

### 1. Verify Shutdown

- [ ] Ensure `run_shadow_loop.py` has stopped (it should auto-stop after 15:35).
- [ ] If not, press `Ctrl+C` in the terminal window.

### 2. Review Reports

- [ ] Check `GARAM_Data/logs/shadow/` for the daily shadow report (`shadow_report_YYYYMMDD.md`).
- [ ] Check `GARAM_Data/logs/shadow/perf_daily_YYYYMMDD.md` for performance stats.
- [ ] (Optional) Commit logs/reports to git for backup.

## Troubleshooting

- **Kiwoom Disconnected**: Restart the workstation and log in to Kiwoom manually.
- **High Latency**: Check internet connection and CPU usage. Restart `run_shadow_loop.py`.
- **Disk Full**: Run `python scripts/run_system_health_check.py` to see usage. Clear old logs in `GARAM_Data/logs/`.
