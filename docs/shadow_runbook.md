# Shadow Trading Operations Runbook

## 1. Daily Startup (08:50 ~ 09:00)

### A. Environment Check

1. **Kiwoom Login**: Ensure Kiwoom Open API is logged in (32-bit environment).
2. **Trading Mode**: Verify `config/trading_mode.json` is set to `"SHADOW"`.

### B. Start Processes

1. **32-bit Feeder (Terminal 1)**:

    ```powershell
    # In 32-bit python environment
    python scripts/kr_realtime_feeder.py
    ```

2. **64-bit Shadow Loop (Terminal 2)**:

    ```powershell
    python scripts/run_shadow_loop.py
    ```

3. **Dashboard Server (Terminal 3)**:

    ```powershell
    python api/server.py
    ```

4. **Watchdog (Optional)**:

    ```powershell
    python scripts/watch_shadow_loop.py
    ```

### C. Verify Status

1. Open Dashboard: [http://localhost:5000](http://localhost:5000)
2. Check **System Health** card:
    - Status: **OK** (or WARN if market closed)
    - KR Feed: **Active**
    - Mode: **SHADOW**

---

## 2. Intraday Monitoring (09:00 ~ 15:30)

### Checkpoints

- **Every 1 Hour**: Check Dashboard for "System Health" status.
- **Alerts**: Monitor `GARAM_Data/logs/alerts.log` for ERROR/CRITICAL messages.

### Troubleshooting

- **Feeder Crash**: Restart `scripts/kr_realtime_feeder.py`.
- **Shadow Loop Stalled**:
    1. Check `GARAM_Data/logs/shadow/shadow_loop_YYYYMMDD.log`.
    2. If stuck, kill process and restart `scripts/run_shadow_loop.py`.
- **Data Latency High**: Check internet connection and Kiwoom API status.

---

## 3. End of Day (15:35 ~)

### A. Shutdown

1. Stop `run_shadow_loop.py` (Ctrl+C).
2. Stop `kr_realtime_feeder.py` (Ctrl+C).

### B. Performance Review

1. Run Aggregator (if not auto-run):

    ```powershell
    python monitoring/shadow_performance.py
    ```

2. Check Report: `GARAM_Data/logs/shadow/perf_daily_YYYYMMDD.md`.
3. Fill out Daily Journal (see `docs/shadow_journal/daily_template.md`).

### C. System Health Check

1. Run final health check:

    ```powershell
    python scripts/run_system_health_check.py
    ```
