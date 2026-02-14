# Phase 6: Paper Trading Operations Plan (2-Week)

**Objective**: Verify the operational stability of the entire pipeline (Ingest -> Signal -> Order -> Fill -> Reconcile) without risking capital.
**Engine**: `HOLD_1D` (SSOT Default)
**Status**: **Ready to Start**

## 1. Operational Gates (Go/No-Go)

Every daily operation MUST pass these gates before generating any orders.

| Gate | Check | Action on Fail |
|---|---|---|
| **1. SSOT Audit** | `python -m scripts.audit_ssot` returns PASS | **KILL SWITCH** (Stop immediately) |
| **2. Data Freshness** | `run_ingest_kiwoom` collected today's data for 400 symbols | **SKIP** (No new signal) |
| **3. Execution** | `orders/inbox` is empty (Previous orders processed) | **WARN** (Potential backlog) |

## 2. Weekly Schedule

### Week 1: Dry Run (File Generation Only)

**Goal**: Verify the "Signal -> Order File" pipeline and Audit integration.
**Capital**: Virtual 100M KRW (Simulation)
**Command**:

```powershell
python -m scripts.run_daily_ops --audit --dry_run --allocate --build_orders
```

**Verification**:

- [ ] Ops script checks `audit_ssot`.
- [ ] Scanning runs successfully.
- [ ] Allocation logic runs.
- [ ] Order Builder runs in `--dry_run` mode (Prints JSONs to console, writes nothing OR writes to `orders/dry_run`?).
  - *Decision*: We will let it print to console to confirm logic. Or strictly use `--dry_run` flag of builder.

### Week 2: Mock Trading (Live Kiwoom)

**Goal**: Verify "Order File -> Kiwoom Execution -> Fill Report".
**Environment**: Kiwoom Mock Investment Server (모의투자).
**Command**:

```powershell
python -m scripts.run_daily_ops --audit --allocate --build_orders
```

**Verification**:

- [ ] Files created in `GARAM_Data/orders/inbox`.
- [ ] `run_ingest_kiwoom.py` (Watcher) picks them up.
- [ ] Orders sent to Kiwoom.
- [ ] ACKs received in `orders/ack`.
- [ ] Fills (Chegyeol) received and saved.
- [ ] End-of-Day Position Reconciliation matches.

## 3. Daily Routine (User)

1. **15:30**: Market Close.
2. **15:35**: Run `launch_kiwoom.bat` (Ensure Mock Server selected).
3. **15:40**: Run Daily Ops:

    ```powershell
    python -m scripts.run_daily_ops --audit --allocate --build_orders [--dry_run if Week 1]
    ```

4. **15:50**: Confirm `[AUDIT] PASS` logs and Order generation.
5. **09:00 (Next Day)**: Monitor Execution (if Week 2).

## 4. Success Criteria (Exit to Phase 7)

- [ ] **10 consecutive days** of Audit PASS.
- [ ] **Zero** missing orders (Allocated = Ordered).
- [ ] **Zero** unhandled ACKs or Rejections.
- [ ] **PnL Sync**: Internal Equity Curve tracks Mock Account Equity within 0.1% error.
