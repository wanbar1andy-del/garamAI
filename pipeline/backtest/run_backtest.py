# -*- coding: utf-8 -*-
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np

@dataclass
class Bar:
    ts: str            # YYYYMMDDHHMMSS
    close: float

def parse_minute_csv(path: Path) -> pd.DataFrame:
    # Expect: date,open,high,low,close,volume (no header) OR with header
    df = pd.read_csv(path, header=None)
    if df.shape[1] >= 6 and str(df.iloc[0,0]).isdigit() and len(str(df.iloc[0,0])) >= 8:
        df.columns = ["date","open","high","low","close","volume"] + [f"c{i}" for i in range(df.shape[1]-6)]
    else:
        # header exists
        df = pd.read_csv(path)
        # normalize common column names
        rename = {}
        for c in df.columns:
            lc = str(c).lower()
            if lc in ("date","datetime","ts","체결시간"):
                rename[c] = "date"
            elif lc in ("close","현재가","종가"):
                rename[c] = "close"
        if rename:
            df = df.rename(columns=rename)
        if "date" not in df.columns or "close" not in df.columns:
            raise ValueError(f"CSV schema not recognized: {path} cols={list(df.columns)}")
        
        # Ensure volume exists
        if "volume" not in df.columns:
            df["volume"] = 0
            
        # create minimal columns (keep volume)
        df = df[["date","close", "volume"]]
        df["open"] = df["close"]
        df["high"] = df["close"]
        df["low"]  = df["close"]
        # df["volume"] = 0 # Removed overwritten 0

    df["date"] = df["date"].astype(str)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date","close"])
    # Return volume if available, else 0
    if "volume" not in df.columns:
        df["volume"] = 0
    return df[["date","close","volume"]]

def filter_window(df: pd.DataFrame, start_ymd: str, end_ymd: str) -> pd.DataFrame:
    # start/end are YYYYMMDD inclusive
    s = str(start_ymd)
    e = str(end_ymd)
    df = df[df["date"].str[:8].between(s, e)]
    return df

def build_universe(data_dir: Path) -> List[str]:
    # universe = all csv filenames in minute dir
    syms = []
    for p in data_dir.glob("*.csv"):
        name = p.stem.strip()
        if name.isdigit() and len(name) <= 6:
            syms.append(name.zfill(6))
    return sorted(list(set(syms)))

def compute_roc_1m(prices: Dict[str, pd.Series]) -> Dict[str, pd.Series]:
    out = {}
    for sym, s in prices.items():
        out[sym] = s.pct_change().fillna(0.0)
    return out

def align_index(series_map: Dict[str, pd.Series]) -> pd.Index:
    # intersection of indices for stability
    idx = None
    for s in series_map.values():
        idx = s.index if idx is None else idx.intersection(s.index)
    return idx if idx is not None else pd.Index([])

def run_backtest(
    data_dir: Path,
    start: str,
    end: str,
    capital: float,
    fee_bps: float,
    max_symbols: int,
    hold_symbol: Optional[str],
    out_dir: Path,
    rebalance_period: int = 1,
    threshold: float = 0.0,
    cooldown: int = 0,
    universe_file: Optional[Path] = None,
    slippage_bps: float = 0.0,
    liq_lookback: int = 60,
    liq_min_notional: float = 0.0,
    trend_lookback: int = 15,
    trend_min: float = 0.0,
    score_w5: float = 0.7,
    score_w1: float = 0.3,
    index_symbol: str = "",
    regime_ma: bool = False,
    regime_roc: bool = False,
    use_kill_switch: bool = False
):
    out_dir.mkdir(parents=True, exist_ok=True)

    if universe_file and universe_file.exists():
        # Load from file (expecting 'symbol' column or just list)
        try:
            # Try reading as csv with header
            udf = pd.read_csv(universe_file, dtype=str)
            if "symbol" in udf.columns:
                universe = udf["symbol"].tolist()
            elif "code" in udf.columns:
                universe = udf["code"].tolist()
            else:
                # assume no header, first column
                universe = udf.iloc[:,0].tolist()
        except:
             # plain text
             universe = universe_file.read_text().splitlines()
        universe = [str(x).strip().zfill(6) for x in universe if str(x).strip().isdigit()]
        # Filter by max_symbols
        universe = universe[:max_symbols]
    else:
        universe = build_universe(data_dir)
        if hold_symbol:
            universe = [hold_symbol.zfill(6)]
        else:
            # limit for speed if needed
            universe = universe[:max_symbols]

    if not universe:
        raise ValueError("Universe is empty. Check data_dir.")

    # Load close series per symbol
    closes: Dict[str, pd.Series] = {}
    volumes: Dict[str, pd.Series] = {}
    for sym in universe:
        p = data_dir / f"{sym}.csv"
        if not p.exists():
            continue
        df = parse_minute_csv(p)
        df = filter_window(df, start, end)
        if df.empty:
            continue
        # date is YYYYMMDDHHMMSS
        df = df.set_index("date")
        s = df["close"].astype(float)
        v = df["volume"].astype(float)
        closes[sym] = s.sort_index()
        volumes[sym] = v.sort_index()

    if not closes:
        raise ValueError("No data loaded for the requested window.")


    # Align timestamps (common timeline)
    idx = align_index(closes)
    if len(idx) < 10:
        raise ValueError(f"Not enough aligned minutes. aligned_len={len(idx)}. Consider reducing universe or checking data window.")

    closes = {sym: s.reindex(idx).ffill().bfill() for sym, s in closes.items()}
    volumes = {sym: s.reindex(idx).fillna(0.0) for sym, s in volumes.items()}
    # [FIX] Look-ahead Bias Removal: Calculate ROC at t, but available for decision at t+1
    # We shift signal forward by 1 step so that rocs[t] contains the ROC calculated from t-1 to t.
    # Actually, user request: "Signal calculated at t, execute at t+1".
    # If we simply use closes[t-1] and closes[t-2] to decide for t, that works.
    # The existing code uses current 'roc_now' at 'ts'.
    # So we calculate ROC normally, but in the loop, we access 'roc[t-1]' to decide for 't'?
    # Simpler: Shift the entire ROC DataFrame by 1.
    roc = compute_roc_1m(closes)
    for sym in roc:
        roc[sym] = roc[sym].shift(1).fillna(0.0) # Signal for t is based on t-1 data

    # [Gate 1] Liquidity Pre-computation
    liquidity = {}
    if liq_min_notional > 0:
        for sym in closes:
            notional = closes[sym] * volumes[sym]
            liquidity[sym] = notional.rolling(window=liq_lookback).mean().fillna(0.0).shift(1) 
            # Shift 1 to match decision timing (using past 60m avg to decide for T)
    
    # [Gate 2 & Scoring] Trend and Multi-period ROC
    # Trend: 15m ROC
    trend = {}
    if trend_lookback > 0:
        for sym in closes:
             # pct_change(15) -> shifted 1
             trend[sym] = closes[sym].pct_change(trend_lookback).fillna(0.0).shift(1)
    
    # Roc5: 5m ROC
    roc5 = {}
    # Always compute roc5 if we are mixing score? Or only if score_w5 > 0?
    # Better to always compute for simplicity or valid mixing.
    for sym in closes:
         roc5[sym] = closes[sym].pct_change(5).fillna(0.0).shift(1)

    fee = fee_bps / 10000.0

    # [Regime] Index Data Loading & Processing
    regime_mask = pd.Series(True, index=idx)
    if index_symbol:
        ipath = data_dir / f"{index_symbol}.csv"
        if ipath.exists():
            idf = parse_minute_csv(ipath)
            idf = filter_window(idf, start, end)
            if not idf.empty:
                # Resample to Daily for Regime Calculation
                idf["dt"] = pd.to_datetime(idf["date"], format="%Y%m%d%H%M%S")
                idf = idf.set_index("dt").sort_index()
                
                # Daily Resample (Last Close)
                daily = idf["close"].resample("D").last().dropna()
                
                # Calculate Indicators
                ma20 = daily.rolling(20).mean()
                roc10 = daily.pct_change(10)
                
                # Align Daily Signals to Minute Index (Shift 1 day to remove look-ahead)
                daily_ma20 = ma20.shift(1).fillna(0)
                daily_roc10 = roc10.shift(1).fillna(0)
                daily_close = daily.shift(1).fillna(0) 
                
                # Gates
                gate_a = (daily_close > daily_ma20)
                gate_b = (daily_roc10 > 0)
                
                # Reindex to minute
                idx_dt = pd.to_datetime(pd.Series(idx), format="%Y%m%d%H%M%S")
                minute_gate_a = gate_a.reindex(idx_dt, method='ffill').fillna(False).values
                minute_gate_b = gate_b.reindex(idx_dt, method='ffill').fillna(False).values
                
                # Combine Filters
                final_mask = np.ones(len(idx), dtype=bool)
                if regime_ma:
                    final_mask = final_mask & minute_gate_a
                if regime_roc:
                    final_mask = final_mask & minute_gate_b
                
                regime_mask = pd.Series(final_mask, index=idx)
        else:
            print(f"[WARN] Index symbol {index_symbol} not found. Regime Gates disabled.")

    # State
    cash = float(capital)
    pos_sym = None
    pos_qty = 0.0
    entry_px = 0.0
    
    last_entry_idx = -9999
    
    # Kill Switch State
    current_date = ""
    daily_start_equity = capital
    kill_switch_active = False

    equity_rows = []
    trade_rows = []
    
    # [FIX] Rebalancing Parameters
    # rebalance_period_min: e.g. 5 means rebalance only if minute % 5 == 0 (or index step % 5 == 0)
    # logic: if i % rebalance_period_min == 0: check logic
    # threshold: if new_best_roc > current_roc + threshold: switch

    # Helper
    def mark_to_market(ts: str) -> float:
        nonlocal cash, pos_sym, pos_qty
        if pos_sym is None:
            return cash
        # Use current close for MTM
        px = float(closes[pos_sym].loc[ts])
        return cash + pos_qty * px

    def close_position(ts: str, reason: str):
        nonlocal cash, pos_sym, pos_qty, entry_px
        if pos_sym is None:
            return
        px = float(closes[pos_sym].loc[ts])
        
        # Apply Slippage (Exit = Sell -> Price drops)
        slip = px * (slippage_bps / 10000.0)
        exec_px = px - slip
        
        notional = pos_qty * exec_px
        cost = notional * fee
        cash += notional - cost
        pnl = (exec_px - entry_px) * pos_qty - cost
        
        # Return pct based on entry_px (which already included slippage)
        return_pct = (exec_px / entry_px - 1.0) if entry_px > 0 else 0.0
        
        trade_rows.append({
            "exit_ts": ts,
            "symbol": pos_sym,
            "entry_px": entry_px,
            "exit_px": exec_px,
            "qty": pos_qty,
            "pnl": pnl,
            "return_pct": return_pct,
            "reason": reason
        })
        pos_sym = None
        pos_qty = 0.0
        entry_px = 0.0

    def open_position(ts: str, sym: str, reason: str):
        nonlocal cash, pos_sym, pos_qty, entry_px
        px = float(closes[sym].loc[ts])
        if px <= 0:
            return
        
        # Apply Slippage (Entry = Buy -> Price increases)
        slip = px * (slippage_bps / 10000.0)
        exec_px = px + slip
        
        notional = cash
        cost = notional * fee
        invest = max(0.0, notional - cost)
        qty = invest / exec_px
        cash -= invest + cost
        pos_sym = sym
        pos_qty = qty
        entry_px = exec_px
        trade_rows.append({
            "entry_ts": ts,
            "symbol": sym,
            "entry_px": exec_px,
            "qty": qty,
            "entry_reason": reason
        })

    # Backtest Loop
    for i, ts in enumerate(idx):
        # Daily reset logic for Kill Switch
        ts_date = ts[:8]
        if ts_date != current_date:
            # New Day
            if kill_switch_active:
                kill_switch_active = False 
            
            # Update Daily Start Equity
            daily_start_equity = mark_to_market(ts)
            current_date = ts_date
        
        eq = mark_to_market(ts)
        
        # Check Kill Switch
        if use_kill_switch and not kill_switch_active:
             dd_day = (eq / daily_start_equity) - 1.0
             if dd_day < -0.02: # -2% limit
                 kill_switch_active = True
                 if pos_sym:
                     close_position(ts, reason="KILL_SWITCH_DAILY")
        
        # If Kill Switch Active, Skip Logic (Hold Cash)
        if kill_switch_active:
            equity_rows.append({"ts": ts, "equity": eq})
            continue

        # Check Regime Gate
        is_bullish = regime_mask[ts] 
        if not is_bullish:
            if pos_sym:
                close_position(ts, reason="REGIME_OFF")
            equity_rows.append({"ts": ts, "equity": eq})
            continue

        # MTM first (using close at t)
        
        # Check rebalancing schedule (modulo index)
        # 1-minute data, so step 1 = 1 minute.
        if i % rebalance_period == 0:
            # Decide Top-1 based on shifted ROC (which is ROC(t-1))
            # [Gate 1 & 2] Filter Candidates
            candidates = []
            for sym in closes.keys():
                # Gate 1: Liquidity
                if liq_min_notional > 0:
                     val = float(liquidity[sym].loc[ts])
                     if val < liq_min_notional:
                         continue
                
                # Gate 2: Trend
                if trend_min > -999: # Enable if trend_min is set (default -999 to disable?) User said trend_min 0.0 default. 
                # Let's assume if trend_lookback > 0, we check trend.
                     t_val = float(trend[sym].loc[ts])
                     if t_val <= trend_min: # Only allow if trend > min
                         continue
                         
                candidates.append(sym)
            
            if not candidates:
                best_sym = None
                best_val = -999.0 # Score
                best_roc_1m = -999.0
            else:
                # [Scoring] Calculate Mixed Score
                # score = w5 * roc5 + w1 * roc1
                scores = {}
                for sym in candidates:
                    r1 = float(roc[sym].loc[ts])
                    r5 = float(roc5[sym].loc[ts])
                    scores[sym] = (score_w5 * r5) + (score_w1 * r1)
                
                best_sym = max(scores, key=scores.get)
                best_val = scores[best_sym] # This is the SCORE
                best_roc_1m = float(roc[best_sym].loc[ts]) # Original 1m ROC for reporting/logging check

            # Logic
            if pos_sym is None:
                 if best_sym and best_val > 0: # Entry condition on SCORE? Or 1m ROC? Usually Score > 0.
                    open_position(ts, best_sym, reason=f"OPEN_SCORE_{best_val:.4f}")
                    last_entry_idx = i
            elif best_sym != pos_sym:
                 # Check Cooldown
                 if cooldown > 0 and (i - last_entry_idx) < cooldown:
                     pass # Hold position
                 else:
                     # Switching logic with Threshold
                     # Need current symbol score to compare
                     if pos_sym in scores:
                         current_score = scores[pos_sym]
                     else:
                         # Calculate current symbol score on the fly if not in candidates (e.g. illiquid now)
                         # Or just assume very low if filtered out.
                         # If filtered out, should we sell? User didn't specify forced exit on filtering.
                         # Assume we compare best vs current.
                         # If current filtered out, current_score should be low?
                         # Let's compute it if possible, else -999.
                         if pos_sym in roc and pos_sym in roc5:
                             c_r1 = float(roc[pos_sym].loc[ts])
                             c_r5 = float(roc5[pos_sym].loc[ts])
                             current_score = (score_w5 * c_r5) + (score_w1 * c_r1)
                         else:
                             current_score = -999.0

                     if best_val > current_score + threshold:
                        close_position(ts, reason=f"RX_TO_{best_sym}")
                        open_position(ts, best_sym, reason=f"OPEN_SCORE_{best_val:.4f}")
                        last_entry_idx = i
        
        eq = mark_to_market(ts)
        equity_rows.append({"ts": ts, "equity": eq, "pos": pos_sym if pos_sym else ""})

    # Close at end
    close_position(idx[-1], reason="EOD_CLOSE")

    equity = pd.DataFrame(equity_rows)
    trades = pd.DataFrame(trade_rows)

    equity.to_csv(out_dir / "equity_curve.csv", index=False, encoding="utf-8-sig")
    trades.to_csv(out_dir / "trades.csv", index=False, encoding="utf-8-sig")

    print("[OK] backtest done")
    print(f" - out_dir: {out_dir}")
    print(f" - equity rows: {len(equity)}")
    print(f" - trades rows: {len(trades)}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--capital", type=float, required=True)
    ap.add_argument("--fee_bps", type=float, default=3.0)
    ap.add_argument("--max_symbols", type=int, default=120)
    ap.add_argument("--hold_symbol", default="")
    ap.add_argument("--out_dir", required=True)
    # New Arguments for Phase 26b
    ap.add_argument("--rebalance_period", type=int, default=1, help="Rebalance every N minutes")
    ap.add_argument("--threshold", type=float, default=0.0, help="Switch only if diff > threshold")
    ap.add_argument("--cooldown", type=int, default=0, help="Cooldown bars after entry")
    ap.add_argument("--universe_file", default="", help="Path to universe csv")
    ap.add_argument("--slippage_bps", type=float, default=0.0, help="Slippage bps per side")
    ap.add_argument("--liq_lookback", type=int, default=60, help="Liquidity lookback window")
    ap.add_argument("--liq_min_notional", type=float, default=0.0, help="Min average notional to trade")
    ap.add_argument("--trend_lookback", type=int, default=15, help="Trend lookback (15m)")
    ap.add_argument("--trend_min", type=float, default=0.0, help="Min trend ROC to allow entry")
    ap.add_argument("--score_w5", type=float, default=0.7, help="Weight for 5m ROC")
    ap.add_argument("--score_w1", type=float, default=0.3, help="Weight for 1m ROC")
    ap.add_argument("--index_symbol", default="", help="Index symbol for regime filter (e.g. 005930)")
    ap.add_argument("--regime_ma", action="store_true", help="Enable MA20 Regime Gate")
    ap.add_argument("--regime_roc", action="store_true", help="Enable ROC10 Regime Gate")
    ap.add_argument("--use_kill_switch", action="store_true", help="Enable Daily -2% Kill Switch")
    
    args = ap.parse_args()

    run_backtest(
        data_dir=Path(args.data_dir),
        start=str(args.start),
        end=str(args.end),
        capital=float(args.capital),
        fee_bps=float(args.fee_bps),
        max_symbols=int(args.max_symbols),
        hold_symbol=args.hold_symbol.strip() if args.hold_symbol.strip() else None,
        out_dir=Path(args.out_dir),
        rebalance_period=int(args.rebalance_period),
        threshold=float(args.threshold),
        cooldown=int(args.cooldown),
        universe_file=Path(args.universe_file) if args.universe_file else None,
        slippage_bps=float(args.slippage_bps),
        liq_lookback=int(args.liq_lookback),
        liq_min_notional=float(args.liq_min_notional),
        trend_lookback=int(args.trend_lookback),
        trend_min=float(args.trend_min),
        score_w5=float(args.score_w5),
        score_w1=float(args.score_w1),
        index_symbol=args.index_symbol.strip(),
        regime_ma=args.regime_ma,
        regime_roc=args.regime_roc,
        use_kill_switch=args.use_kill_switch
    )

if __name__ == "__main__":
    main()
