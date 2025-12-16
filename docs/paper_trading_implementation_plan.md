# Paper Trading Implementation Plan

**Objective**: Deploy DGE v0.3 (Refined) to a Paper Trading environment to validate real-time execution, data integrity, and strategy robustness before live deployment.

## 1. System Architecture

The Paper Trading system mimics the Live Trading environment but replaces the Order Execution layer with a Simulator.

### Components

1. **Data Layer**: Real-time Kiwoom OpenAPI+ (Same as Live).
2. **Strategy Layer**: DGE v0.3 Refined (Same as Live).
3. **Execution Layer**: **Paper Execution Simulator** (New).
    - Intercepts `send_order` calls.
    - Simulates fills based on real-time quotes + slippage model.
    - Maintains virtual positions and PnL.
4. **Logging Layer**: Enhanced structured logging for audit and analysis.

## 2. Software Requirements

### A. Mode Flag

Ensure `config.py` and `BaseStrategy` support explicit modes:

- `BACKTEST`: Historical data, fast execution.
- `PAPER`: Real-time data, simulated execution.
- `LIVE`: Real-time data, real execution.

### B. Paper Execution Simulator (`PaperBroker`)

Create `garam/broker/paper_broker.py`:

- **Interface**: Must match `RealBroker` (or `BaseBroker`).
- **Logic**:
  - `send_order(symbol, direction, qty, price, type)`:
    - Log order request.
    - If Market Order: Fill immediately at `current_price` +/- `slippage`.
    - If Limit Order: Add to `pending_orders`. Check against incoming ticks for fill.
  - `get_positions()`: Return virtual positions.
  - `get_balance()`: Return virtual balance.
  - `cancel_order()`: Remove from `pending_orders`.

### C. Logging Structure

- **Trade Log**: `logs/paper/trades_{date}.csv`
  - Time, Symbol, Action, Price, Qty, Slippage, Reason, Regime, fs_orb, fs_fast, fm.
- **Signal Log**: `logs/paper/signals_{date}.csv`
  - Time, Symbol, Signal_Score, Blocked_Reason (if any).
- **Daily Summary**: `logs/paper/summary_{date}.md`
  - PnL, Win Rate, Trade Count, Regime Stats.

### D. Execution Script

Create `scripts/run_paper_trading.py`:

- Initialize `PaperBroker` and `DGEOrbStrategyV3`.
- Connect to Kiwoom (via `RealBroker` data feed or `DataServer`).
- Run the event loop (Real-time).
- Handle graceful shutdown (save state).

## 3. Configuration

### A. Capital & Risk

- **Initial Capital**: 100,000,000 KRW (Virtual).
- **Risk per Trade**: 1.5% (Standard).
- **Slippage Model**:
  - Base: 0.05% (Conservative estimate for liquid mid-caps).
  - Stress: 0.10% (Optional).

### B. Universe

- **Symbols**: Top 10 Liquid Large/Mid Caps (Same as Backtest).
  - 005930, 000660, 005380, 005490, 035420, 000270, 051910, 068270, 105560, 006400.

### C. Schedule

- **Trading Hours**: 09:00 ~ 15:20 (Exit all by 15:20).
- **Days**: Mon-Fri (Market Days).

## 4. Operational Rules

### A. Monitoring

- **Real-time**: Check console logs for "Heartbeat" (Data receiving) and "Order" events.
- **Daily Review**: Check `summary_{date}.md` after market close.

### B. Go/No-Go Criteria (for Live Transition)

- **Duration**: Minimum 2 weeks (10 trading days).
- **Stability**: Zero crashes or data gaps > 10 mins.
- **Performance**:
  - Execution PnL vs Theoretical PnL discrepancy < 1.0% (Slippage check).
  - Strategy behaves as expected in `STRONG_UP` regimes.

## 5. Action Plan

1. [ ] Create `garam/broker/paper_broker.py`.
2. [ ] Update `config.py` with `PAPER` mode settings.
3. [ ] Create `scripts/run_paper_trading.py`.
4. [ ] Dry Run (1 day) to verify logs and simulator logic.
5. [ ] Full Launch.
