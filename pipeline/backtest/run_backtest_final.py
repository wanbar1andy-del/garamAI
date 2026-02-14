import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from run_alpha_robust import load_data

def calculate_signals_local(closes, volumes):
    print("[Signal] Calculating V3 Organic Signals (Local)...")
    
    # 1. Indicators
    # 5m Resample
    c_5m = closes.resample('5min', label='right').last().ffill()
    v_5m = volumes.resample('5min', label='right').sum().fillna(0)
    
    # Volatility Ratio
    v_ma20 = v_5m.rolling(20).mean()
    vol_ratio = v_5m / (v_ma20 + 1e-9)
    
    # Squeeze
    roll = c_5m.rolling(20)
    mid = roll.mean()
    std = roll.std()
    bb_w = (mid + 2*std - (mid - 2*std)) / (mid + 1e-9)
    z_score = (bb_w - bb_w.rolling(100).mean()) / (bb_w.rolling(100).std() + 1e-9)
    is_squeeze = z_score < 0.5
    
    # Explosion
    is_exploded = vol_ratio > 1.5
    
    # Prophet: Churning
    ret = c_5m.pct_change()
    is_churning = (vol_ratio > 3.0) & (ret.abs() < 0.002)
    
    # Structure (Daily MA60)
    c_d = closes.resample('D').last().ffill()
    ma60 = c_d.rolling(60).mean().shift(1).reindex(c_5m.index, method='ffill')
    struct = (c_5m > ma60)
    
    # Hurdle (Potential Reward)
    # ATR
    tr = c_5m.diff().abs()
    atr = tr.rolling(14).mean()
    reward = (5.0 * atr) / c_5m
    # Dynamic Hurdle (Risk based) -> Simplified to 2% (Guerrilla)
    is_worth = reward > 0.02
    
    # Final Mask
    # Squeeze + Explode + Struct + Not Churn + Worth
    sig_5m = is_squeeze & is_exploded & struct & (~is_churning) & is_worth
    
    # Score
    # Base 5 + Boosts
    score_5m = sig_5m.astype(float) * 5.0
    # Boosts
    score_5m += (z_score < -0.5).astype(float) * 2.0 # Tight Squeeze
    score_5m += (vol_ratio > 3.0).astype(float) * 2.0 # Huge Vol
    
    # Reindex to 1m
    score_1m = score_5m.reindex(closes.index, method='ffill').fillna(0)
    
    # Thresholding (Dynamic)
    # Market Vol based
    ret_1m = closes.pct_change()
    vol_market = ret_1m.rolling(20).std().mean(axis=1)
    vol_base = vol_market.rolling(100).mean()
    v_ratio_m = (vol_market / (vol_base + 1e-9)).fillna(1.0)
    
    # Thresh = 5.0 * (0.5 + 0.5 * Ratio)
    thresh = 5.0 * (0.5 + 0.5 * v_ratio_m)
    
    # Filter
    final_score = score_1m * score_1m.ge(thresh, axis=0).astype(float)
    
    return final_score.shift(1).fillna(0)

def calculate_exhaustion_local(closes, volumes):
    # RSI > 75 & Vol > 4x
    delta = closes.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100/(1+rs))
    
    v_ma = volumes.rolling(20).mean()
    climax = volumes > 4.0 * v_ma
    
    return (rsi > 75) & climax

def run_final_test():
    print("::: ALPHA GENIUS V3: 1M KRW FINAL TEST (LOCAL LOGIC) :::")
    start_date = "20250601"
    end_date = "20260205"
    initial_capital = 1_000_000 
    
    data_dir = Path("c:/garam/garam/GARAM_Data/minute/kr")
    universe_file = "universe_test.csv"
    
    closes, volumes = load_data(data_dir, universe_file, start_date, end_date)
    if closes.empty: return

    # Local Signals (Safe)
    signals = calculate_signals_local(closes, volumes)
    exhaustion = calculate_exhaustion_local(closes, volumes)
    
    # Execution
    cash = float(initial_capital)
    equity_curve = []
    trades = []
    
    pos_sym = None
    pos_qty = 0
    entry_px = 0.0
    
    params = {"stop": 0.02, "target": 0.10, "fee": 0.0015, "slip": 0.002}
    
    print("[Execution] Simulating...")
    for ts in closes.index:
        current_prices = closes.loc[ts]
        current_sigs = signals.loc[ts]
        current_exh = exhaustion.loc[ts]
        
        equity = cash
        if pos_sym:
            curr_px = current_prices.get(pos_sym, entry_px)
            if pd.isna(curr_px): curr_px = entry_px
            equity += pos_qty * curr_px
            
            # EXIT
            reason = None
            if current_exh.get(pos_sym, False): reason = "PROPHET"
            
            ret = (curr_px / entry_px) - 1.0
            if ret < -params["stop"]: reason = "STOP"
            elif ret > params["target"]: reason = "PROFIT"
            
            if reason:
                exit_px = curr_px * (1 - params["slip"])
                cash += pos_qty * exit_px * (1 - params["fee"])
                pnl = (exit_px / entry_px) - 1.0
                trades.append({"ts": ts, "type": reason, "pnl": pnl})
                pos_sym = None; pos_qty = 0; continue
                
        # ENTRY
        if pos_sym is None:
            cands = current_sigs[current_sigs > 0].sort_values(ascending=False)
            if not cands.empty:
                best_sym = cands.index[0]
                price = current_prices.get(best_sym, 0)
                if price > 0:
                     # 95% Bet
                     invest = cash * 0.95
                     qty = int(invest / (price * (1 + params["slip"])))
                     if qty > 0:
                         cost = qty * price * (1 + params["slip"]) * (1 + params["fee"])
                         if cost <= cash:
                             cash -= cost
                             pos_sym = best_sym; pos_qty = qty; entry_px = price
                             trades.append({"ts": ts, "type": "ENTRY"})

        equity_curve.append({"ts": ts, "equity": equity})
        
    # Report
    final_eq = equity_curve[-1]["equity"]
    roi = (final_eq / initial_capital) - 1.0
    print("\n" + "="*50)
    print(f"FINAL EQUITY: {final_eq:,.0f} KRW ({roi*100:+.2f}%)")
    print(f"TRADES: {len([t for t in trades if t['type'] != 'ENTRY'])}")
    print("="*50)

if __name__ == "__main__":
    run_final_test()
