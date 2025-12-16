# GARAM V2 Architecture Strategy

## 1. Structure Principles

*   **01-09 Numbered Stages**: Explicit execution order.
*   **Contracts First**: `core/contracts` defines all I/O schemas (DataClasses/Pydantic).
*   **SSOT Everywhere**: No hardcoded paths. All paths from `core/config`.

## 2. Directory Structure (TO-BE)

```text
/pipeline
  /01_ingest       # Data Collection (Kiwoom, etc.)
  /02_validate     # Data Integrity Check & Repair
  /03_store        # Standardized Data Storage (Parquet/DB)
  /04_feature      # Feature Engineering (Technical Indicators)
  /05_signal       # Strategy Logic (HeroFinder, Probe, Regime)
  /06_monitor      # System Health & Alerting
  /07_execution    # Order Management & Execution
  /08_orchestrator # Trading Loop & Main Controller
  /09_dashboard    # UI Backend & API

/core
  /config          # Configuration Loader (paths.yaml)
  /contracts       # Shared Data Models (Artifacts)
  /utils           # Common Utilities
```

## 3. Migration Strategy (Wrapper & Adapter)

1.  **Do Not Move Files Yet**: Create wrappers in `/pipeline/XX_stage/` first.
2.  **Import Legacy**: Wrappers import logic from `garam_core` or `scripts`.
3.  **Refactor Later**: Once the wrapper is working and tested, move the code into the wrapper.

## 4. Key Contracts (Draft)

*   `Universe`: List of symbols to trade.
*   `MarketData`: OHLCV DataFrame + Metadata.
*   `HeroCandidate`: Symbol + Score + Evidence.
*   `OrderSignal`: Symbol + Side + Price + Qty.
*   `PortfolioState`: Current Holdings + Cash + PnL.
