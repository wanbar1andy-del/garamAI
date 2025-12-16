# System Path & Data Policy

This document defines the standard directory structure and file safety policies for the Garam Trading System. All components must adhere to these rules to ensure data integrity and operational stability.

## 1. Directory Structure

The system uses `GARAM_Data` as the root for all dynamic data.

```
GARAM_Data/
├── config/              # Operational configurations (Critical)
│   ├── trading_mode.json
│   ├── kr_shadow_universe.yaml
│   └── cost_config.yaml
├── raw/                 # Immutable raw data (Append-only)
│   ├── kr/
│   │   └── realtime/    # 1-minute bars from Feeder
│   └── us/
├── runtime/             # Volatile runtime state (Recoverable)
│   ├── positions.json
│   ├── kiwoom_session.json
│   └── realtime_feed_buffer/
└── logs/                # Rotatable logs
    ├── shadow/          # Shadow loop logs & reports
    ├── health/          # System health reports
    ├── alerts/          # Critical alerts
    └── signals/         # Strategy signal logs
```

## 2. File Safety Policies

### A. Atomic Writes (Feeder -> Loader)

When writing data that is consumed by another process (e.g., Feeder writing 1-minute bars for Loader):

1. Write data to a temporary file first: `filename.tmp`
2. Flush buffer and close file handle.
3. Rename `filename.tmp` to `filename.csv` (Atomic operation).

**Rule**: Consumers (Loaders) must **IGNORE** `.tmp` files and only read `.csv` files.

### B. Configuration Safety

- `config/` files are critical.
- Changes to `trading_mode.json` should be done via `scripts/set_trading_mode.py` or verified UI actions, not manual edits during runtime.

### C. Log Rotation

- Logs in `logs/` can be deleted or archived without affecting system logic.
- Filename pattern: `service_YYYYMMDD.log` (Daily rotation).

### D. Disk Usage

- System Health Check must warn if the drive containing `GARAM_Data` exceeds **90%** usage.
