# Risk & Ops Layer Roadmap (GARAM)

## 1. Overview

Based on your blueprint, we will implement the Risk & Ops layer in **3 Phases**, prioritizing immediate safety for the Live Engine.

| Phase | Focus | Key Components | Timeline |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **Immediate Safeguards ("Airbag")** | Account Limits, Pre-Trade Checks, Slippage Model | **Immediate (Before Real Money)** |
| **Phase 2** | **Operational Stability ("Black Box")** | Health Checks, Logging, Version Control | Next Week |
| **Phase 3** | **Advanced Research ("Lab")** | Purged CV, Stress Tests, Off-Sample Validation | Future |

---

## 2. Phase 1: Immediate Safeguards (The "Airbag")

**Goal**: Prevent catastrophic loss due to engine bugs or fat-finger errors during Live/Paper trading.

### 2.1. Account Risk Engine (`risk/account_limits.yaml`)

Define hard limits that, if breached, trigger an immediate **STOP**.

```yaml
# risk/account_limits.yaml
daily_loss_limit_pct: -3.0      # Stop if daily loss > 3%
max_gross_exposure_pct: 100.0   # No leverage for now
max_single_symbol_pct: 30.0     # Max 30% in one stock
min_cash_balance: 1_000_000     # Always keep 1M KRW cash
```

### 2.2. Pre-Trade Checks (`risk/pretrade_checks.py`)

A module called by `run_live_trading.py` *before* sending any order.

- **Check 1**: Order Value < Account Limit (e.g., max 30% equity).
- **Check 2**: Order Qty < Market Volume (e.g., max 1% of 5-day avg volume).
- **Check 3**: Price Deviation (Limit Price vs. Last Close < 15%).

### 2.3. Slippage & Cost Model (`risk/slippage_model.py`)

- Apply conservative slippage (e.g., 20bps) to all backtests and paper trades to ensure realistic PnL.

**Action Item**:

- Create `risk/` directory structure.
- Implement `pretrade_checks.py`.
- Integrate into `run_live_trading.py` (Wrap `orders.append` with `if check_order(order):`).

---

## 3. Phase 2: Operational Stability (The "Black Box")

**Goal**: Ensure the system runs reliably and recovers from failures.

### 3.1. Enhanced Health Check (`scripts/check_system_health.py`)

Upgrade the existing script to check:

- **Data Freshness**: Is today's data actually downloaded?
- **Broker Connectivity**: Is Kiwoom API responding? (Ping test)
- **Risk Daemon**: Is the risk process running?

### 3.2. Version Control & Rollback

- **Tagging**: Add `strategy_version` to `alpha_catalog.yaml` and logs.
- **Backup**: `daily_routine.py` should zip `config/` and `scripts/` to `backup/` before running.

---

## 4. Phase 3: Advanced Research (The "Lab")

**Goal**: Prevent overfitting in future strategies.

### 4.1. Purged Combinatorial CV (`scripts/run_ts_cv.py`)

- Implement the "Train/Val/Test" split logic.
- Automated "Fail" if Val performance deviates too much from Train.

---

## 5. Recommendation

**Approve Phase 1 implementation immediately.**
The Multi-Alpha Engine is powerful but complex. Without the "Airbag" (Phase 1), a logic error in `AlphaAggregator` could theoretically allocate 100% to a single stock or trade illiquid assets.

**Shall I proceed with Phase 1?**

1. Create `risk/account_limits.yaml`
2. Create `risk/pretrade_checks.py`
3. Integrate into `run_live_trading.py`
