import sys
import argparse
import traceback
import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta, time
import shutil

# Setup Paths
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from garam_core.fastlane.feature_store import FeatureStore
from garam_core.data.loader import load_ohlcv
import shutil # Re-adding explicitly if missing or robust import

# --- Phase 22 Constants ---
COST_RATE_BPS = 15 # 0.15%
TAX_RATE_BPS = 21.5 # 0.215% (Assuming roughly KOSPI/KOSDAQ avg or user spec)
# User said COST_RATE=0.0015 (0.15%) and TAX approx 0.215%?
# Code had COST_RATE = 0.0015 and used 0.00015 in loop (0.015%?).
# User said: "Code has COST_RATE=0.0015 declared, but uses 0.00015. Fix to SSOT. Let's assume 30bps roundtrip."
# 30bps roundtrip = 0.30%.
# Let's align exactly: Entry Fee 0.015%, Exit Fee 0.015% + Tax 0.20%? => ~0.23%?
# User said "Real assumption 30bps".
# Let's set: ENTRY_FEE = 0.00015 (0.015%), EXIT_FEE = 0.00015, TAX = 0.0020 (0.2%). Total ~0.23%.
# Wait, user said "Code used 0.00015". 0.00015 is 1.5bps. That seems low for retail. Kiwoom is 0.015% (1.5bps).
# Ah, 0.00015 IS 0.015%. 
# 0.01 = 1%. 0.0015 = 0.15%. NO.
# 1.0 = 100%. 0.01 = 1%. 0.00015 = 0.015%. Correct.
# So Kiwoom Fee is 0.015%.
# Tax is 0.20% (KOSPI) or 0.20% (KOSDAQ)? currently 0.18% or 0.20%.
# Let's use standard: Fee 0.00015, Tax 0.0020.
# User said: "Make sure entry/exit use same FEE, TAX, SLIPPAGE. Total 30bps."
# 30bps = 0.0030.
# If I set Fee=0.00015, Tax=0.0020, total is 0.0023 (23bps). Slippage 7bps?
# I will define:
ENTRY_COST = 0.00015
EXIT_COST = 0.00015
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

# --- Phase 22 Constants (SSOT) ---
ENTRY_FEE = 0.00015
EXIT_FEE  = 0.00015
EXIT_TAX  = 0.0020
SLIPPAGE  = 0.00035   # 3.5 bps
DEFAULT_MA60_CHECK = True






def calc_trade_pnl(qty: int, entry_px: float, exit_px: float) -> tuple[float, float, float]:
    """
    Calculates PnL with Price Slippage and standard Fees/Tax.
    Returns: (net_pnl, cost_basis, proceeds)
    """
    # Apply slippage to price
    fill_entry = entry_px * (1 + SLIPPAGE)
    fill_exit  = exit_px  * (1 - SLIPPAGE)

    cost_basis = qty * fill_entry * (1 + ENTRY_FEE)
    proceeds   = qty * fill_exit  * (1 - EXIT_FEE - EXIT_TAX)
    pnl = proceeds - cost_basis
    
    return pnl, cost_basis, proceeds

def pre_load_data(universe: list):
    """
    Loads all data into RAM (Raw OHLCV) and pre-calculates Daily MA60.
    """
    print(f"[Init] Pre-loading data for {len(universe)} symbols...")
    
    data_map = {}
    ma60_map = {}
    
    cnt = 0
    data_root = project_root / "GARAM_Data" 
    
    for sym in universe:
        cnt += 1
        if cnt % 50 == 0: print(f"  Loaded {cnt}/{len(universe)}")
        
        try:
            df = load_ohlcv(data_root, sym, "minute")
            if df is None or df.empty: continue
            
            # Normalize
            df = df.reset_index()
            if "index" in df.columns and "date" not in df.columns:
                 df.rename(columns={"index": "date"}, inplace=True)
            elif "date" not in df.columns:
                 # Check if the first column is date-like? Or assume index was reset?
                 pass

            df.columns = [c.lower() for c in df.columns]
            
            if "date" in df.columns:
                if not pd.api.types.is_datetime64_any_dtype(df["date"]):
                    df["date"] = pd.to_datetime(df["date"])
                if df["date"].dt.tz is not None:
                     df["date"] = df["date"].dt.tz_localize(None)
                
                df = df.sort_values("date").reset_index(drop=True)
                data_map[sym] = df
                
                # Pre-calc Daily MA60
                df_curr = df.copy()
                df_curr.set_index("date", inplace=True)
                daily_closes = df_curr["close"].resample("D").last().dropna()
                
                if not daily_closes.empty:
                    ma60_map[sym] = daily_closes.rolling(window=60).mean()
            
        except Exception as e:
            continue
            
    print(f"[Init] Finished loading {len(data_map)} valid symbols.")
    return data_map, ma60_map

def simulate_day_intraday(sym, df_day, ma60_val,
                          entry_roc: float,
                          entry_vol: float,
                          exit_sl: float,
                          exit_tp: float,
                          time_stop_mins: int, # NEW
                          reversal_type: int): # 0=None (but we calc score), >0=Filter(Legacy)
    """
    Simulates Intraday Trading for a single symbol.
    Returns CANIDATE object with Score.
    """
    if df_day.empty: return []
    df_day = df_day.set_index("date").sort_index()
    
    day_date = df_day.index[0].date()
    market_start = datetime.combine(day_date, time(9, 0))
    market_end = datetime.combine(day_date, time(15, 30))
    full_idx = pd.date_range(market_start, market_end, freq="1min")
    
    df_res = df_day.reindex(full_idx)
    df_res["close"] = df_res["close"].ffill() 
    df_res["volume"] = df_res["volume"].fillna(0) 
    
    # 2. Vectorized Features
    # ROC 5m
    roc_5m = (df_res["close"] / df_res["close"].shift(5)) - 1.0
    
    # Vol Accel
    vol_roll = df_res["volume"].rolling(10).sum()
    vol_ma = vol_roll / 10.0
    vol_accel = np.divide(df_res["volume"], vol_ma, out=np.zeros_like(vol_ma), where=vol_ma > 1e-9)
    
    # Reversal Signals (For Scoring)
    # 2-Candle
    rev_2candle = (df_res["close"] > df_res["close"].shift(1)) & \
                  (df_res["close"].shift(1) > df_res["close"].shift(2))
    # Breakout (Max 3)
    recent_max = df_res["close"].shift(1).rolling(3).max()
    rev_breakout = df_res["close"] > recent_max
    
    # 3. Scanning
    # MA60 Check
    if DEFAULT_MA60_CHECK:
        if pd.isna(ma60_val) or ma60_val == 0: return []
        trend_mask = df_res["close"] > ma60_val
    else:
        trend_mask = True
        
    start_time = datetime.combine(day_date, time(9, 5))
    end_time = datetime.combine(day_date, time(15, 19))
    time_mask = (df_res.index >= start_time) & (df_res.index <= end_time)
    
    # Base Entry Mask (Relaxed)
    base_mask = time_mask & trend_mask & (roc_5m <= entry_roc) & (vol_accel >= entry_vol)
    
    # Legacy Reversal Filter (for A/B compat, though Phase 22 uses 0)
    if reversal_type == 1: base_mask &= (df_res["close"] > df_res["close"].shift(1))
    elif reversal_type == 2: base_mask &= rev_2candle
    elif reversal_type == 3: base_mask &= rev_breakout
    
    entries = df_res[base_mask]
    if entries.empty: return []
    
    # IMPORTANT: In Phase 22, we generate ALL candidates, not just the first one.
    # But for "Trade Management Simplicity", we assume 1 trade per symbol per day for now.
    # We pick the FIRST qualified signal time as the candidate.
    # (Refinement: Could check subsequent signals if first one wasn't picked? Complex. Stick to First valid).
    
    entry_ts = entries.index[0]
    entry_row = entries.iloc[0]
    entry_price = entry_row["close"]
    
    if pd.isna(entry_price): return []
    
    # SCORING (Phase 22 P1)
    # dip_strength = clamp((-roc_5m)/abs(entry_roc), 0, 2)
    current_roc = roc_5m.loc[entry_ts]
    dip_strength = min(max((-current_roc) / abs(entry_roc), 0.0), 2.0)
    
    # vol_score = log1p(vol_accel)
    current_vol = vol_accel.loc[entry_ts]
    vol_score = np.log1p(current_vol)
    
    # Rev Bonus
    rev_bonus = 0.0
    if rev_2candle.loc[entry_ts]: rev_bonus += 0.2
    if rev_breakout.loc[entry_ts]: rev_bonus += 0.25
    
    total_score = dip_strength + vol_score + rev_bonus
    
    # Exit Logic (Fast Forward)
    exit_ts = None
    exit_price = 0.0
    exit_reason = ""
    
    holding_data = df_res.loc[entry_ts + timedelta(minutes=1) : ]
    
    for ts, row in holding_data.iterrows():
        # EOD
        if ts.time() >= time(15, 20):
            exit_ts = ts
            exit_price = row["close"]
            exit_reason = "EOD"
            break
            
        curr_price = row["close"]
        if pd.isna(curr_price): continue
        
        # Check SL/TP
        pnl_pct = (curr_price / entry_price) - 1.0
        
        if pnl_pct <= exit_sl:
            exit_ts = ts
            exit_price = curr_price
            exit_reason = "SL"
            break
            
        if pnl_pct >= exit_tp:
            exit_ts = ts
            exit_price = curr_price
            exit_reason = "TP"
            break
            
        # Time Stop (Phase 22 P3 - Conditional)
        if time_stop_mins > 0:
            elapsed = (ts - entry_ts).total_seconds() / 60.0
            if elapsed >= time_stop_mins:
                # Conditional: Only exit if PnL is non-positive (Cutting losers/stagnant)
                # Winners are allowed to run until TP or End of Day.
                if pnl_pct <= 0.001: # Use small threshold (0.1%) to cut breakeven stagnation too
                     exit_ts = ts
                     exit_price = curr_price
                     exit_reason = "TimeStop"
                     break
            
    if exit_ts is None:
        exit_ts = df_res.index[-1]
        exit_price = df_res["close"].iloc[-1]
        exit_reason = "ForceEnd"
        
    return [{
        "ts": entry_ts, 
        "type": "CANDIDATE", 
        "symbol": sym, 
        "price": entry_price,
        "score": total_score,
        "exit_info": {
            "ts": exit_ts,
            "price": exit_price,
            "reason": exit_reason
        },
        "log_extras": {
            "roc_5m": current_roc,
            "vol_accel": current_vol,
            "rev_hit": (1 if rev_2candle.loc[entry_ts] else 0) + (2 if rev_breakout.loc[entry_ts] else 0),
            "ma60": ma60_val
        }
    }]

def run_replay_batch(days2run: int,
                     entry_roc: float,
                     entry_vol: float,
                     ma60_check: bool,
                     exit_sl: float,
                     exit_tp: float,
                     time_stop: int, # NEW
                     max_slots: int,
                     reversal_type: int,
                     tag: str,
                     start_date: str | None = None,
                     end_date: str | None = None,
                     init_capital: float = 10_000_000.0,
                     out_root: str | None = None,
                     reset_out: bool = True):


    if days2run < 2:
        print("[ERR] days must be >= 2")
        sys.exit(1)

    print(f"=== Phase 22 Batch Replay: days={days2run} tag={tag} ===")
    print(f"Params: ROC={entry_roc}, Vol={entry_vol}, SL={exit_sl}, TP={exit_tp}, TimeStop={time_stop}, Rev={reversal_type}")
    print(f"CostModel: Entry/Exit Fee={ENTRY_FEE:.5f}, Tax={EXIT_TAX:.5f}, Slippage={SLIPPAGE:.5f}")
    # print(f"Logic: 2/5/0 Allocation (Top-2 Dominant or Top-5 Balanced)")

    # ... (Date Range & Universe Loading Code same as before) ...
    # Optimized: Removed Universe Print spam
    
    fs = FeatureStore()
    df_sample = fs.get_features("005930")
    dates = pd.to_datetime(df_sample["date"]).dt.tz_localize(None).dt.normalize().unique()
    dates = sorted(pd.to_datetime(dates))

    if start_date and end_date:
        s = pd.to_datetime(start_date).normalize()
        e = pd.to_datetime(end_date).normalize()
        target_dates = [d for d in dates if (d >= s and d <= e)]
    else:
        target_dates = dates[-days2run:]

    if len(target_dates) < 2:
        print(f"[WARN] Not enough trading days in range. days={len(target_dates)}")
        return {
            "tag": tag, "days": len(target_dates), "final_equity": init_capital,
            "return_pct": 0.0, "trades": 0, "win_rate": 0.0, "mdd_pct": 0.0, "pnl_sum": 0.0
        }
    
    universe_path = project_root / "GARAM_Data" / "real_universe_400.csv"
    df_univ = pd.read_csv(universe_path)
    # Filter 6-digit only
    raw_codes = df_univ["Code"].astype(str).tolist()
    valid_universe = [c.zfill(6) for c in raw_codes if c.zfill(6).isdigit() and len(c.zfill(6))==6]
    if "475960" in valid_universe: valid_universe.remove("475960")

    data_map, ma60_map = pre_load_data(valid_universe)
    loaded_syms = list(data_map.keys())
    
    if out_root is None:
        base_res_dir = project_root / "results" / "replay" / tag
    else:
        base_res_dir = Path(out_root)

    if reset_out and base_res_dir.exists():
        shutil.rmtree(base_res_dir)
    base_res_dir.mkdir(parents=True, exist_ok=True)
    
    capital = float(init_capital)
    initial_cap = float(init_capital)
    equity_curve = []
    all_trades = []

    # 4. Simulation Loop (Rank-Based)
    for idx, current_date in enumerate(target_dates):
        date_str = current_date.strftime("%Y-%m-%d")
        daily_dir = base_res_dir / date_str
        (daily_dir / "results" / "logs").mkdir(parents=True, exist_ok=True)
        print(f"[{idx+1}/{days2run}] Simulating {date_str} (Cap: {capital:,.0f})...")
        
        # 4.1 Collect All Candidates for the Day
        all_candidates = []
        for sym in loaded_syms:
            df_all = data_map[sym]
            start_ts = current_date
            end_ts = current_date + timedelta(days=1)
            i_start = df_all["date"].searchsorted(start_ts)
            i_end = df_all["date"].searchsorted(end_ts)
            if i_start == i_end: continue 
            
            df_day = df_all.iloc[i_start:i_end].copy()
            
            # MA60 Logic (Same as before)
            ma60 = ma60_map.get(sym, 0)
            ma60_val = 0
            if ma60 is not None and isinstance(ma60, pd.Series): # Correct MA60 lookup logic or reuse prev
                 if current_date in ma60.index: ma60_val = ma60.loc[current_date]
                 elif not ma60.empty:
                      asof_idx = ma60.index.searchsorted(current_date)
                      if asof_idx>0: ma60_val = ma60.iloc[asof_idx-1]
                      else: ma60_val = ma60.iloc[0]
                 else: ma60_val=0
            else: ma60_val=0

            cands = simulate_day_intraday(
                sym, df_day, ma60_val,
                entry_roc, entry_vol, exit_sl, exit_tp, time_stop, reversal_type
            )
            all_candidates.extend(cands)
            
        # 4.2 Group by Time and Rank
        all_candidates.sort(key=lambda x: x["ts"])
        
        # Grouping
        from itertools import groupby
        grouped_candidates = []
        for key, group in groupby(all_candidates, key=lambda x: x["ts"]):
            g_list = list(group)
            # Sort by Score Descending
            g_list.sort(key=lambda x: x["score"], reverse=True)
            grouped_candidates.append((key, g_list))
            
        # 4.3 Execute Time Steps
        active_positions = {} # sym -> {shares, exit_info, k_mode, norm, w}
        day_trade_logs = []
        
        # Timeline processing
        timeline = []
        for ts, cands in grouped_candidates:
            timeline.append({"ts": ts, "type": "ENTRY_CYCLE", "candidates": cands})
            
        for step in timeline:
            curr_ts = step["ts"]
            
            # 1. Process Exits (Clean up finished trades)
            to_remove = []
            for sym, pos in active_positions.items():
                exit_ts = pos["exit_info"]["ts"]
                if exit_ts <= curr_ts:
                    # Trade completed
                    p_entry = pos["price"]
                    p_exit = pos["exit_info"]["price"]
                    qty = pos["shares"]
                    
                    # P0: SSOT Cost Model (calc_trade_pnl)
                    pnl, cost_basis, proceeds = calc_trade_pnl(qty, p_entry, p_exit)
                    
                    capital += proceeds
                    
                    day_trade_logs.append({
                        "ts": exit_ts, "symbol": sym, "decision": "EXIT",
                        "price": p_exit, "qty": qty, "pnl": pnl, 
                        "reason": pos["exit_info"]["reason"],
                        "score": 0, "rank": 0, "k_mode": pos.get("k_mode", 0), "norm_score": pos.get("norm",0), "weight": pos.get("w",0)
                    })
                    to_remove.append(sym)
                    
            for sym in to_remove:
                del active_positions[sym]
                
            # 2. Process Entries (Ranked)
            cands = step["candidates"]
            rank=0
            for cand in cands:
                rank += 1
                sym = cand["symbol"]
                if sym in active_positions: continue # Already holding (re-entry block?)
                if len(active_positions) >= max_slots: break # Slots Full
                
                # Enter
                price = cand["price"]
                slot_cash = initial_cap / max_slots
                if capital > slot_cash * 0.5:
                     shares = int(slot_cash / price)
                     
                     # Est Cost for Entry (including fees/slippage estimate? Or just Fee)
                     # For simplicity, we deduct basic cost to check cash.
                     # But for PnL consistency with `calc_trade_pnl`, entry cost is Basis.
                     # Basis = qty * price * (1+S) * (1+F).
                     
                     est_basis = shares * price * (1+SLIPPAGE) * (1+ENTRY_FEE)
                     
                     if capital >= est_basis:
                         capital -= est_basis
                         active_positions[sym] = {
                             "shares": shares, 
                             "price": price, 
                             "exit_info": cand["exit_info"]
                         }
                         # Log with Extras (P2)
                         row = {
                             "ts": curr_ts, "symbol": sym, "decision": "ENTRY",
                             "price": price, "qty": shares, "pnl": 0, "reason": "Signal",
                             "score": cand["score"], "rank": rank
                         }
                         # Add extras
                         row.update(cand["log_extras"])
                         day_trade_logs.append(row)
        
        # End of Day Cleanup
        to_remove = []
        for sym, pos in active_positions.items():
            exit_ts = pos["exit_info"]["ts"]
            p_entry = pos["price"]
            p_exit = pos["exit_info"]["price"]
            qty = pos["shares"]
            
            pnl, cost_basis, proceeds = calc_trade_pnl(qty, p_entry, p_exit)
            
            capital += proceeds
            
            day_trade_logs.append({
                "ts": exit_ts, "symbol": sym, "decision": "EXIT",
                "price": p_exit, "qty": qty, "pnl": pnl, 
                "reason": pos["exit_info"]["reason"],
                "score": 0, "rank": 0
            })
            to_remove.append(sym)
        active_positions = {}
        
        # Save Logs
        all_trades.extend(day_trade_logs)
        df_log = pd.DataFrame(day_trade_logs)
        if not df_log.empty:
            df_log = df_log.sort_values("ts")
            df_log.to_csv(daily_dir / "results" / "logs" / f"trade_log_{date_str}.csv", index=False)
            
        equity_curve.append({"date": date_str, "equity": capital})

    # 5. Report (SSOT Quality)
    df_eq = pd.DataFrame(equity_curve)
    
    # --- Save equity curve CSV options (WFA contract: save to base_res_dir) ---
    # WFA needs consistent location: base_res_dir / f"EquityCurve_{tag}.csv"
    eq_csv_path = base_res_dir / f"EquityCurve_{tag}.csv"
    if not df_eq.empty: df_eq.to_csv(eq_csv_path, index=False, encoding="utf-8")
    
    tr_csv_path = base_res_dir / f"Trades_{tag}.csv"
    if all_trades: pd.DataFrame(all_trades).to_csv(tr_csv_path, index=False, encoding="utf-8")

    df_trades = pd.DataFrame(all_trades)
    
    total_trades = len(df_trades[df_trades["decision"]=="EXIT"]) if not df_trades.empty else 0
    pnl_sum = 0.0
    win_rate = 0.0
    if total_trades > 0:
        exits = df_trades[df_trades["decision"]=="EXIT"]
        pnl_sum = exits["pnl"].sum()
        wins = exits[exits["pnl"] > 0]
        win_rate = (len(wins) / total_trades) * 100

    final_eq = df_eq.iloc[-1]["equity"] if not df_eq.empty else initial_cap
    ret_pct = ((final_eq / initial_cap) - 1) * 100
    mdd = 0.0
    if not df_eq.empty:
        peak = df_eq["equity"].cummax()
        dd = (df_eq["equity"] / peak) - 1.0
        mdd = dd.min() * 100
        
    # Validation P0: BPS Calculation
    # Approx total impact: S(in)+F(in) + S(out)+F(out)+Tax(out)
    # Entry: (1+S)(1+F) ~= 1 + S + F
    # Exit: (1-S)(1-F-T) ~= 1 - S - F - T
    # Total Drop ~= 2S + 2F + T
    # 2*3.5 + 2*1.5 + 20 = 7 + 3 + 20 = 30 bps?
    # Actually calc:
    # Cost = EntryBasis - EntryRaw + ExitRaw - ExitProceeds ?
    # Let's just sum constants.
    total_cost_bps = (SLIPPAGE*2 + ENTRY_FEE + EXIT_FEE + EXIT_TAX) * 10000
    
    # Monthly Breakdown
    monthly_stats = ""
    if not df_eq.empty:
        df_eq["date_dt"] = pd.to_datetime(df_eq["date"])
        df_eq["month"] = df_eq["date_dt"].dt.strftime("%Y-%m")
        # monthly = df_eq.groupby("month")["equity"].last() # This line was commented out in the original, keeping it that way.
        # monthly_pct = monthly.pct_change() * 100 # This line was commented out in the original, keeping it that way.
        
        months = df_eq["month"].unique()
        prev_eq = initial_cap
        monthly_lines = []
        for m in months:
             last_eq = df_eq[df_eq["month"]==m]["equity"].iloc[-1]
             m_ret = ((last_eq / prev_eq) - 1) * 100
             monthly_lines.append(f"- **{m}**: {m_ret:+.2f}% (Eq: {last_eq:,.0f})")
             prev_eq = last_eq
        monthly_stats = "\n".join(monthly_lines)

    summary_md = f"""# Profitability Validation Gate (Phase 22 Champion SEALED)

## Configuration
- Strategy: Phase 22 (Tag: {tag})
- Range: {target_dates[0].date()} ~ {target_dates[-1].date()} ({len(target_dates)} days)
- Init Capital: {initial_cap:,.0f} KRW
- Params: ROC={entry_roc}, Vol={entry_vol}, SL={exit_sl}, TP={exit_tp}, TS={time_stop} (Conditional)
- **Allocation Rule**: Uniform Top-K (Ranked)
- **Cost Model (Sealed)**: {total_cost_bps:.1f} bps
- Data Coverage: {len(loaded_syms)}/{len(valid_universe)}

## KPI Summary
1. **Total Return**: {ret_pct:.2f}%
2. **Total Trades (Exit)**: {total_trades}
3. **Win Rate**: {win_rate:.1f}%
4. **PnL Sum**: {pnl_sum:,.0f} KRW
5. **MDD**: {mdd:.2f}%
6. **Final Equity**: {final_eq:,.0f} KRW

## Monthly Breakdown
{monthly_stats}

## Status
- **Profitability**: {'PASS' if ret_pct > 0 else 'FAIL'}
- **Sample Size**: {'PASS' if total_trades >= 40 else 'FAIL (<40)'}
- **Stability (MDD)**: {'PASS' if mdd > -10 else 'WARN'}

## Evidence
- Logs: `results/replay/*/results/logs/trade_log_*.csv`
"""
    rep_path = project_root / "results" / "reports" / f"Backtest_Summary_{tag}.md"
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    rep_path.write_text(summary_md, encoding="utf-8")
    
    # Plotting code ... (same)
    import matplotlib.pyplot as plt
    plots_dir = project_root / "results" / "reports" / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    if not df_eq.empty:
        plt.figure()
        plt.plot(pd.to_datetime(df_eq["date"]), df_eq["equity"])
        plt.title(f"Phase 22 Equity ({tag})")
        plt.savefig(plots_dir / f"Batch_Equity_{tag}.png")
        plt.close()
        
        plt.figure()
        peak = df_eq["equity"].cummax()
        dd = (df_eq["equity"] / peak) - 1.0
        plt.plot(pd.to_datetime(df_eq["date"]), dd)
        plt.title(f"Phase 22 Drawdown ({tag})")
        plt.savefig(plots_dir / f"Batch_Drawdown_{tag}.png")
        plt.close()
        
        if not df_trades.empty:
            exits = df_trades[df_trades["decision"]=="EXIT"].copy()
            if "pnl" in exits.columns and len(exits) > 0:
                plt.figure()
                plt.hist(exits["pnl"].values, bins=30)
                plt.title(f"Trade PnL ({tag})")
                plt.savefig(plots_dir / f"Batch_TradePnL_{tag}.png")
                plt.close()

    summary = {
        "tag": tag,
        "start_date": str(target_dates[0].date()) if target_dates else None,
        "end_date": str(target_dates[-1].date()) if target_dates else None,
        "days": len(target_dates),
        "init_capital": initial_cap,
        "final_equity": float(final_eq),
        "return_pct": float(ret_pct),
        "trades": int(total_trades),
        "win_rate": float(win_rate),
        "mdd_pct": float(mdd),
        "pnl_sum": float(pnl_sum),
    }
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--entry_roc", type=float, default=-0.02)
    parser.add_argument("--entry_vol", type=float, default=1.2)
    parser.add_argument("--exit_sl", type=float, default=-0.02)
    parser.add_argument("--exit_tp", type=float, default=0.03)
    parser.add_argument("--time_stop", type=int, default=0) # New: 0=Disabled
    parser.add_argument("--max_slots", type=int, default=3)
    parser.add_argument("--reversal", type=int, default=0) # 0=Scoring Only, >0=Filter
    parser.add_argument("--tag", type=str, default="exp22_test")
    # WFA Extension
    parser.add_argument("--start_date", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--end_date", type=str, default=None, help="YYYY-MM-DD (inclusive)")
    parser.add_argument("--init_capital", type=float, default=10_000_000.0)
    parser.add_argument("--out_root", type=str, default=None, help="e.g., results/walkforward/2025-09")
    parser.add_argument("--reset_out", action="store_true", help="delete out_root if exists")
    
    args = parser.parse_args()

    run_replay_batch(
        days2run=args.days,
        entry_roc=args.entry_roc,
        entry_vol=args.entry_vol,
        ma60_check=True,
        exit_sl=args.exit_sl,
        exit_tp=args.exit_tp,
        time_stop=args.time_stop,
        max_slots=args.max_slots,
        reversal_type=args.reversal,
        tag=args.tag,
        start_date=args.start_date,
        end_date=args.end_date,
        init_capital=args.init_capital,
        out_root=args.out_root,
        reset_out=args.reset_out,
    )
