# GARAM System Connection Map

This diagram illustrates the intended connection flow and the fix applied to the "Kiwoom Connection" gap.

```mermaid
graph TD
    subgraph Startup
        A[start_garam.bat] -->|Launches| B[Kiwoom Login UI]
        A -->|Launches| C[Flask API Server]
        A -->|Opens| D[Browser Dashboard]
    end

    subgraph Kiwoom Connection
        B -->|Connects| E[Kiwoom OpenAPI]
        B -->|Creates (FIXED)| F[kiwoom_ready.flag]
        E -->|Real-time Data| B
    end

    subgraph Server Logic
        C -->|Checks| F
        C -->|Reads| G[Daily Plan JSON]
        C -->|Reads| H[Signal Logs]
    end

    subgraph Dashboard UI
        D -->|Fetches /api/system/kiwoom_status| C
        D -->|Fetches /api/strategy/daily-plan| C
        D -->|Fetches /api/ai/summary| C
    end

    style F fill:#f9f,stroke:#333,stroke-width:4px
```

## Connection Status Analysis

1. **Kiwoom Login UI -> Server**:
    * **Status**: BROKEN -> **FIXED**
    * **Issue**: The UI logged in successfully but didn't tell the server.
    * **Fix**: Added `_create_connection_flag()` to `kiwoom_login_ui.py`.

2. **Server -> Dashboard (Strategy)**:
    * **Status**: OK
    * **Path**: `ui/static/dashboard.js` calls `/api/strategy/daily-plan/today`.
    * **Backend**: `ui/api/strategy_api.py` serves `GARAM_Data/plans/daily_plan_YYYYMMDD.json`.

3. **Server -> Dashboard (AI Core)**:
    * **Status**: OK
    * **Path**: `ui/static/dashboard.js` calls `/api/ai/health`.
    * **Backend**: `ui/api/ai_core_api.py` is active.
