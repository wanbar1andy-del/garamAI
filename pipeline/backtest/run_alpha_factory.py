# -*- coding: utf-8 -*-
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import glob
from concurrent.futures import ThreadPoolExecutor

# --- Configuration & Constants ---
FEE_BPS = 5.0 # Conservative
SLIPPAGE_BPS = 5.0 # Total 10bps friction
CAPITAL = 10_000_000

class AlphaBase:
    def __init__(self):
        self.name = "Base"
    
    def calculate_signals(self, closes: pd.DataFrame, volumes: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

class AlphaA1(AlphaBase):
    def __init__(self):
        super().__init__()
        self.name = "A1_FlowZ"

    def calculate_signals(self, closes: pd.DataFrame, volumes: pd.DataFrame) -> pd.DataFrame:
        print("[Alpha A1] Calculating Factors...")
        flow = closes * volumes
        rolling = flow.rolling(window=60)
        z_score = (flow - rolling.mean()) / (rolling.std() + 1e-9)
        ma60 = closes.rolling(window=60).mean()
        trend_up = (closes > ma60)
        signals = z_score.where(trend_up & (z_score > 2.0), -999.0)
        return signals.shift(1).fillna(-999.0)

class AlphaA6(AlphaBase):
    def __init__(self):
        super().__init__()
        self.name = "A6_Reversion"

    def calculate_signals(self, closes: pd.DataFrame, volumes: pd.DataFrame) -> pd.DataFrame:
        print("[Alpha A6] Calculating Factors (RSI Reversion)...")
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        score = (30.0 - rsi)
        signals = score.where(score > 0, -999.0)
        return signals.shift(1).fillna(-999.0)

class AlphaA2(AlphaBase):
    """
    A2: Volatility Breakout (5m)
    - Factors:
      1. Compression (BB Width Z-Score < 0)
      2. Breakout (Close > 20 High)
      3. Volume (Vol > MA20 Vol)
    - Gates: Comp > 0, Brk > 0.2%, VolRatio > 1.5
    """
    def __init__(self):
        super().__init__()
        self.name = "A2_VolBreakout"

    def calculate_signals(self, closes: pd.DataFrame, volumes: pd.DataFrame) -> pd.DataFrame:
        print("[Alpha A2] Calculating Factors (5m Vol Breakout)...")
        # 1. Resample to 5m
        # Note: We need 'High' for breakout. But we only have closes/volumes here.
        # Approximation: High ~ Max within 5m? 
        # Since we load closes/volumes only, we'll approximate 5m High as max(close) in that bucket? 
        # Or better: We assume closes are 1m.
        # correct way: resample('5min').max() for High, .last() for Close.
        
        # But `closes` passed here is 1m minute close.
        c_5m = closes.resample('5min', label='right').last()
        h_5m = closes.resample('5min', label='right').max() # Approx High
        v_5m = volumes.resample('5min', label='right').sum()
        
        # 2. Factors (on 5m)
        lookback = 100
        
        # A) Compression (BB Width)
        rolling = c_5m.rolling(window=20)
        mid = rolling.mean()
        std = rolling.std()
        upper = mid + 2*std
        lower = mid - 2*std
        bb_width = (upper - lower) / (mid + 1e-9)
        bb_width = bb_width.fillna(method='bfill').fillna(0.0)
        
        # Z-Score of Width 
        w_mean = bb_width.rolling(window=lookback, min_periods=20).mean()
        w_std = bb_width.rolling(window=lookback, min_periods=20).std()
        w_z = (bb_width - w_mean) / (w_std + 1e-9)
        score_comp = -w_z.fillna(0.0)
        
        # B) Breakout (Close vs 20-period High)
        h_20 = h_5m.rolling(window=20, min_periods=5).max().shift(1)
        brk_str = (c_5m / (h_20 + 1e-9) - 1.0).fillna(0.0)
        
        # Z-Score of Break Strength
        b_mean = brk_str.rolling(window=lookback, min_periods=20).mean()
        b_std = brk_str.rolling(window=lookback, min_periods=20).std()
        score_brk = ((brk_str - b_mean) / (b_std + 1e-9)).fillna(0.0)
        
        # C) Volume
        v_ma20 = v_5m.rolling(window=20, min_periods=5).mean()
        vol_ratio = (v_5m / (v_ma20 + 1e-9)).fillna(0.0)
        score_vol = vol_ratio.clip(upper=5.0)
        
        # 3. Composite Score
        # Weights: 0.45, 0.35, 0.20
        final_score = (0.45 * score_comp) + (0.35 * score_brk) + (0.20 * score_vol)
        
        # DEBUG STATS (Commented out for Prod)
        # print(f"[A2 Debug] Width Mean: {bb_width.mean().mean():.4f}")
        # print(f"[A2 Debug] Comp Mean: {score_comp.mean().mean():.4f}, Max: {score_comp.max().max():.4f}")
        # print(f"[A2 Debug] Brk Mean: {brk_str.mean().mean():.4f}, Max: {brk_str.max().max():.4f}")
        # print(f"[A2 Debug] Vol Mean: {vol_ratio.mean().mean():.4f}, Max: {vol_ratio.max().max():.4f}")
        
        # 4. Gates (Production Tuned)
        # - Comp > -0.2 (Allow slightly wider than avg)
        # - Brk > 0.0015 (0.15%)
        # - VolRatio > 1.3
        
        mask = (score_comp > -0.2) & (brk_str > 0.0015) & (vol_ratio > 1.3)
        
        # Check pass rate
        # pass_count = mask.sum().sum()
        # total_count = mask.count().sum()
        # print(f"[A2 Debug] Signals Passing Gates: {pass_count} / {total_count} ({pass_count/total_count*100:.4f}%)")
        
        filtered_score = final_score.where(mask, -999.0)
        
        # 5. Up-sample back to 1m
        # ffill() to propagate the signal for the next 5 mins
        signals_1m = filtered_score.reindex(closes.index).ffill()
        
        # Shift 1m to allow execution at Next Minute
        return signals_1m.shift(1).fillna(-999.0)

def parse_minute_csv(filepath):
    try:
        df = pd.read_csv(filepath)
        cols = [c.lower() for c in df.columns]
        df.columns = cols
        if "datetime" in df.columns:
             df = df.rename(columns={"datetime": "date"})
        
        if "volume" not in df.columns: df["volume"] = 0.0
        
        # Fast Date Parse
        df["dt"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d%H%M%S", errors='coerce')
        if df["dt"].isnull().all():
             df["dt"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d%H%M", errors='coerce')
             
        df = df.dropna(subset=["dt"]).set_index("dt").sort_index()
        return df[["close", "volume"]]
    except:
        return pd.DataFrame()

def load_data(data_dir, universe_file, start_date, end_date):
    print(f"[Loader] Loading data from {start_date} to {end_date}...")
    u_df = pd.read_csv(universe_file)
    u_df.columns = [c.lower() for c in u_df.columns]
    sym_col = "symbol" if "symbol" in u_df.columns else "code"
    if "shcode" in u_df.columns: sym_col = "shcode"
    
    symbols = u_df[sym_col].astype(str).str.zfill(6).tolist()
    closes, volumes = {}, {}
    s_dt, e_dt = pd.to_datetime(start_date), pd.to_datetime(end_date)
    
    def _load(sym):
        f = data_dir / f"{sym}.csv"
        if not f.exists(): return None, None, None
        df = parse_minute_csv(f)
        if df.empty: return None, None, None
        mask = (df.index >= s_dt) & (df.index <= e_dt)
        df = df.loc[mask]
        if df.empty: return None, None, None
        return sym, df["close"], df["volume"]

    with ThreadPoolExecutor(max_workers=8) as executor:
        for sym, c, v in executor.map(_load, symbols):
            if sym:
                closes[sym] = c
                volumes[sym] = v
            
    print(f"[Loader] Loaded {len(closes)} symbols.")
    print(f"[Loader] Loaded {len(closes)} symbols.")
    return pd.DataFrame(closes), pd.DataFrame(volumes)

def calculate_daily_heroes(closes: pd.DataFrame) -> pd.Series:
    print("[Regime] Calculating Daily Hero Counts (>15%)...")
    # Resample to Daily
    daily_closes = closes.resample('D').last().ffill()
    daily_ret = daily_closes.pct_change()
    
    # Hero Definition: Gain > 15%
    hero_mask = (daily_ret > 0.15)
    hero_counts = hero_mask.sum(axis=1)
    
    # Rolling Average of Heroes (last 3 days)
    # Using shift(1) to ensure we use YESTERDAY's data for TODAY's decision
    rolling_heroes = hero_counts.rolling(window=3).mean().shift(1).fillna(0)
    
    print("[Regime] Recent Hero Counts (Last 5 days):")
    print(rolling_heroes.tail(5))
    return rolling_heroes

def run_strategy(alpha: AlphaBase, closes: pd.DataFrame, volumes: pd.DataFrame, out_dir: Path):
    print(f"[Engine] Running Strategy: {alpha.name}")
    closes = closes.ffill().fillna(0.0)
    volumes = volumes.fillna(0.0)
    
    # --- Regime Calculation ---
    hero_counts = calculate_daily_heroes(closes)
    HERO_THRESHOLD = 3.0 # Minimum 3 heroes avg in last 3 days
    
    signals = alpha.calculate_signals(closes, volumes)
    
    # --- Constraints ---
    REBALANCE_PERIOD = 5
    MAX_DAILY_TRADES = 5
    MIN_HOLDING_MINUTES = 15
    POSITION_SCALE = 0.5 
    
    # --- Stop Logic (A2 Spec) ---
    STOP_LOSS_PCT = 0.012     # 1.2%
    TRAILING_STOP_PCT = 0.010 # 1.0% from Peak
    TIME_STOP_MINS = 30       # 30 mins
    TIME_STOP_THRESHOLD = 0.002 # Must be > 0.2% by then
    
    cash = CAPITAL
    pos_sym = None
    pos_qty = 0.0
    entry_px = 0.0
    entry_idx = -999
    max_px_since_entry = 0.0
    
    trade_rows = []
    equity_rows = []
    
    daily_start_equity = CAPITAL
    current_date = None
    kill_switch = False
    daily_trade_count = 0
    FRICTION = 0.0005 

    idx = closes.index
    print(f"[Engine] Start Loop. Stop={STOP_LOSS_PCT*100}%, Trail={TRAILING_STOP_PCT*100}%, Time={TIME_STOP_MINS}m")
    
    for i, ts in enumerate(idx):
        dt_str = ts.strftime("%Y%m%d")
        
        # Daily Reset
        if dt_str != current_date:
            kill_switch = False
            daily_trade_count = 0
            # MTM
            val = cash
            if pos_sym:
                px = closes[pos_sym].iloc[i]
                val += pos_qty * px
            daily_start_equity = val
            current_date = dt_str
            
        # MTM
        current_px = 0.0
        val = cash
        if pos_sym:
            current_px = closes[pos_sym].iloc[i]
            val += pos_qty * current_px
            if current_px > max_px_since_entry:
                max_px_since_entry = current_px
        
        equity_rows.append({"ts": ts, "equity": val})
        
        # 0. Regime Filter (Market Breadth/Hero Check)
        # Check TODAY's regime (based on T-1 stats)
        # ts is timestamp. We need date.
        
        # Look up hero count for this day
        # hero_counts is indexed by Day.
        today_hero_count = 0.0
        try:
            # Floor to day
            day_ts = ts.floor('D')
            today_hero_count = hero_counts.get(day_ts, 0.0)
        except:
            pass
            
        is_market_bad = (today_hero_count < HERO_THRESHOLD)
        
        # 1. Kill Switch (-2% Daily)
        if not kill_switch:
            if daily_start_equity > 0:
                dd = (val / daily_start_equity) - 1.0
                if dd < -0.02:
                    kill_switch = True
                    if pos_sym:
                        # Close
                        exit_px = current_px * (1 - FRICTION)
                        pnl = (exit_px - entry_px) * pos_qty
                        ret = (exit_px / entry_px) - 1.0
                        cash += pos_qty * exit_px
                        trade_rows.append({"exit_ts": ts, "symbol": pos_sym, "pnl": pnl, "return_pct": ret, "reason": "KILL_SWITCH"})
                        pos_sym = None; pos_qty = 0.0
        
        if kill_switch: continue

        # 2. Position Stops (StopLoss, Trailing, Time)
        if pos_sym:
            ret_since_entry = (current_px / entry_px) - 1.0
            dd_from_peak = (current_px / max_px_since_entry) - 1.0
            duration = i - entry_idx
            
            exit_reason = None
            
            # A) Hard Stop
            if ret_since_entry < -STOP_LOSS_PCT:
                exit_reason = "STOP_LOSS"
            # B) Trailing Stop
            elif dd_from_peak < -TRAILING_STOP_PCT:
                exit_reason = "TRAILING"
            # C) Time Stop
            elif duration >= TIME_STOP_MINS and ret_since_entry < TIME_STOP_THRESHOLD:
                exit_reason = "TIME_STOP"
                
            if exit_reason:
                exit_px = current_px * (1 - FRICTION)
                pnl = (exit_px - entry_px) * pos_qty
                ret = (exit_px / entry_px) - 1.0
                cash += pos_qty * exit_px
                trade_rows.append({"exit_ts": ts, "symbol": pos_sym, "pnl": pnl, "return_pct": ret, "reason": exit_reason})
                pos_sym = None; pos_qty = 0.0
                continue # Next iter

        # 3. Rebalancing / Entry
        if i % REBALANCE_PERIOD == 0:
            
            # --- REGIME BLOCK ---
            # If bad market, only allow EXITS (Switch -> Cash), no new entries.
            # Actually, standard behavior: If bad market, force Close Position?
            # Or just block new Signal?
            # User said "No Hero = No Trade". usually implies Stay in Cash.
            # So if we have position, and market is bad -> Switch to Cash (Exit).
            # If no position -> Stay Cash.
            
            if is_market_bad:
                if pos_sym:
                     # Force Exit
                     px = closes[pos_sym].iloc[i]
                     exit_px = px * (1 - FRICTION)
                     cash += pos_qty * exit_px
                     pnl = (exit_px - entry_px) * pos_qty
                     ret = (exit_px / entry_px) - 1.0
                     trade_rows.append({"exit_ts": ts, "symbol": pos_sym, "pnl": pnl, "return_pct": ret, "reason": "REGIME_EXIT"})
                     pos_sym = None; pos_qty = 0.0
                continue # Skip Entry Logic

            # Check Holding Min Period (Only if we haven't stopped out yet)
            if pos_sym and (i - entry_idx) < MIN_HOLDING_MINUTES:
                continue

            scores = signals.iloc[i]
            valid = scores[scores > -999]
            valid = valid[valid.index.isin(closes.columns)] 
            
            best_sym = None
            if not valid.empty:
                best_sym = valid.idxmax()
                
            # A) Switch
            if pos_sym and best_sym and pos_sym != best_sym:
                 # Sell first
                 px = closes[pos_sym].iloc[i]
                 exit_px = px * (1 - FRICTION)
                 cash += pos_qty * exit_px
                 pnl = (exit_px - entry_px) * pos_qty
                 ret = (exit_px / entry_px) - 1.0
                 trade_rows.append({"exit_ts": ts, "symbol": pos_sym, "pnl": pnl, "return_pct": ret, "reason": "SWITCH"})
                 pos_sym = None; pos_qty = 0.0
                 
                 # Buy new
                 if daily_trade_count < MAX_DAILY_TRADES:
                     px = closes[best_sym].iloc[i]
                     if px > 100:
                        entry_price = px * (1 + FRICTION)
                        invest = cash * POSITION_SCALE
                        if invest > 0 and entry_price > 0:
                            qty = invest / entry_price
                            cash -= invest
                            pos_sym = best_sym; pos_qty = qty
                            entry_px = entry_price; entry_idx = i
                            max_px_since_entry = entry_price
                            daily_trade_count += 1
                            trade_rows.append({"entry_ts": ts, "symbol": best_sym, "entry_px": entry_price, "qty": qty, "entry_reason": "ENTRY"})
            
            # B) Entry (from Cash)
            elif not pos_sym and best_sym:
                 if daily_trade_count < MAX_DAILY_TRADES:
                     px = closes[best_sym].iloc[i]
                     if px > 100:
                        entry_price = px * (1 + FRICTION)
                        invest = cash * POSITION_SCALE
                        if invest > 0 and entry_price > 0:
                            qty = invest / entry_price
                            cash -= invest
                            pos_sym = best_sym; pos_qty = qty
                            entry_px = entry_price; entry_idx = i
                            max_px_since_entry = entry_price
                            daily_trade_count += 1
                            trade_rows.append({"entry_ts": ts, "symbol": best_sym, "entry_px": entry_price, "qty": qty, "entry_reason": "ENTRY"})
            
            # C) Exit (Signal Lost)
            elif pos_sym and not best_sym:
                 px = closes[pos_sym].iloc[i]
                 exit_px = px * (1 - FRICTION)
                 cash += pos_qty * exit_px
                 pnl = (exit_px - entry_px) * pos_qty
                 ret = (exit_px / entry_px) - 1.0
                 trade_rows.append({"exit_ts": ts, "symbol": pos_sym, "pnl": pnl, "return_pct": ret, "reason": "NO_SIGNAL"})
                 pos_sym = None; pos_qty = 0.0

    pd.DataFrame(equity_rows).to_csv(out_dir / "equity_curve.csv", index=False)
    pd.DataFrame(trade_rows).to_csv(out_dir / "trades.csv", index=False)
    print(f"[Done] Saved results to {out_dir}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--alpha", required=True)
    parser.add_argument("--start", default="20251001")
    parser.add_argument("--end", default="20251230")
    parser.add_argument("--data_dir", required=True)
    parser.add_argument("--universe_file", required=True)
    parser.add_argument("--out_dir", required=True)
    args = parser.parse_args()
    
    alphas = { 
        "A1": AlphaA1(),
        "A6": AlphaA6(),
        "A2": AlphaA2()
    }
    
    if args.alpha not in alphas:
        print(f"Unknown Alpha: {args.alpha}")
        return
        
    alpha_module = alphas[args.alpha]
    d_path = Path(args.data_dir)
    closes, volumes = load_data(d_path, args.universe_file, args.start, args.end)
    
    if closes.empty:
        print("No data loaded.")
        return

    out_path = Path(args.out_dir) / args.alpha
    out_path.mkdir(parents=True, exist_ok=True)
    run_strategy(alpha_module, closes, volumes, out_path)

if __name__ == "__main__":
    main()
