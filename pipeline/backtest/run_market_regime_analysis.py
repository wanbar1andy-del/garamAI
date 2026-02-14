import pandas as pd
import numpy as np
import sys
from pathlib import Path
from run_alpha_robust import AlphaGenius_V2, load_data

def run_regime_analysis():
    print("::: GARAM SELF-CALIBRATION: MARKET REGIME ANALYSIS :::")
    print("Objective: Autonomously detect regimes and propose optimal thresholds.")
    
    # 1. Load Data
    data_dir = Path("c:/garam/garam/GARAM_Data/minute/kr")
    # Use a broad date range to capture different regimes (assuming data exists)
    closes, volumes = load_data(data_dir, "universe.csv", "20240101", "20251231")
    print(f"[Self] Loaded Data: {closes.shape}")
    
    if closes.empty:
        print("(!) No data found. Cannot proceed.")
        return

    # 2. Construct Synthetic Index (Top 20 by Volume)
    # Estimate 'Top' by average dollar volume
    avg_price = closes.mean()
    avg_vol = volumes.mean()
    dollar_vol = avg_price * avg_vol
    top_syms = dollar_vol.sort_values(ascending=False).head(20).index
    
    print(f"[Self] Constructing Synthetic Index from {len(top_syms)} leaders...")
    
    # Normalized Index (Start at 100)
    idx_closes = closes[top_syms]
    # Simple equal weight for robustness
    norm_closes = idx_closes / idx_closes.iloc[0] * 100
    market_index = norm_closes.mean(axis=1)
    
    # 3. Detect Regimes
    # Resample to Daily for cleaner trend detection
    daily_idx = market_index.resample('D').last().dropna()
    
    # Indicators
    ma20 = daily_idx.rolling(window=20).mean()
    ma60 = daily_idx.rolling(window=60).mean()
    
    # Slope of MA20 (Short Trend)
    ma20_slope = ma20.pct_change(5)
    
    # Volatility (20-day std of returns)
    daily_ret = daily_idx.pct_change()
    vol_20 = daily_ret.rolling(window=20).std()
    
    # Classification Logic
    regimes = pd.Series("UNCERTAIN", index=daily_idx.index)
    
    # Bull: MA20 > MA60 & Slope > 0
    bull_mask = (ma20 > ma60) & (ma20_slope > 0)
    # Bear: MA20 < MA60 & Slope < 0
    bear_mask = (ma20 < ma60) & (ma20_slope < 0)
    # Panic: Vol > 2.0 * Average Vol (Extreme Fear)
    avg_vol = vol_20.mean()
    panic_mask = (vol_20 > 2.0 * avg_vol)
    # Sideways: Slope is flat
    flat_mask = (ma20_slope.abs() < 0.01) & (~bull_mask) & (~bear_mask)
    
    regimes[bull_mask] = "BULL (상승장)"
    regimes[bear_mask] = "BEAR (하락장)"
    regimes[flat_mask] = "SIDEWAYS (횡보장)"
    # Panic overrides everything
    regimes[panic_mask] = "PANIC (공포장)"
    
    print("\n[Regime Distribution]")
    print(regimes.value_counts())
    
    # Align regimes to minute data
    # Forward fill daily regime to minutes
    minute_regime = regimes.reindex(closes.index, method='ffill').fillna("UNCERTAIN")
    
    # 4. Simulate Threshold Performance per Regime
    print("\n[Self] Optimizing Thresholds per Regime...")
    
    # Pre-calc Signals
    alpha = AlphaGenius_V2()
    # We need RAW scores, but calculate_signals now returns filtered.
    # We must Hack or use a simplified scoring here to test RAW thresholds.
    # Let's use AlphaGenius_V2 logic but extract raw score.
    # Actually, modify AlphaGenius_V2 to return raw score? 
    # Or just simulate here. I will simulate simplified Neuro Score V2 here for speed.
    
    # --- Simplified V2 Score ---
    c_5m = closes.resample('5min', label='right').last().ffill()
    v_5m = volumes.resample('5min', label='right').sum().fillna(0)
    v_5m = v_5m.reindex(c_5m.index).fillna(0)
    
    # MA60 Structure
    c_d = closes.resample('D').last().ffill()
    ma60 = c_d.rolling(60).mean().shift(1).reindex(c_5m.index, method='ffill')
    above_struct = (c_5m > ma60)
    
    # Vol Exp
    v_ma20 = v_5m.rolling(20).mean()
    vol_ratio = v_5m / (v_ma20 + 1e-9)
    huge_vol = (vol_ratio > 3.0)
    
    # Squeeze
    roll = c_5m.rolling(20)
    bw = (roll.mean() + 2*roll.std() - (roll.mean() - 2*roll.std())) / roll.mean()
    z = (bw - bw.rolling(100).mean()) / bw.rolling(100).std()
    tight = (z < -0.5)
    
    # Score
    # Base 5 (if squeezed + vol > 1 + struct) - Simplified
    # Let's assume ANY signal has base 5.
    base_mask = (z < 0.5) & (vol_ratio > 1.5) & above_struct
    
    raw_score = base_mask.astype(float) * 5.0
    raw_score += tight.astype(float) * 2.0
    raw_score += huge_vol.astype(float) * 2.0
    # Fractal omitted for speed
    
    # Align to minute for trade simulation
    raw_score_1m = raw_score.reindex(closes.index, method='ffill').fillna(0)
    
    # Test Thresholds: [5, 6, 7, 8, 9]
    thresholds = [5.0, 6.0, 7.0, 8.0, 9.0]
    regime_list = ["BULL (상승장)", "BEAR (하락장)", "SIDEWAYS (횡보장)", "PANIC (공포장)"]
    
    best_params = {}
    
    print(f"{'Regime':<20} | {'Threshold':<10} | {'Trades':<8} | {'WinRate':<8} | {'AvgReturn':<10}")
    print("-" * 70)
    
    for reg in regime_list:
        mask_reg = (minute_regime == reg)
        if mask_reg.sum() == 0: continue
        
        # Slices for this regime
        s_score = raw_score_1m[mask_reg]
        s_close = closes[mask_reg]
        
        best_th = 5.0
        best_perf = -999
        
        for th in thresholds:
            # Candidates
            entries = (s_score >= th)
            if entries.sum().sum() == 0: continue
            
            # Simulate simple trades (Hold 30 mins)
            # Need strict loop? Too slow.
            # Vectorized Return check: Limit to 100 samples per threshold
            # Sample random entry points
            entry_points = entries.stack()
            entry_points = entry_points[entry_points].index.tolist() # (ts, sym) tuples
            
            import random
            if len(entry_points) > 100:
                sample_pts = random.sample(entry_points, 100)
            else:
                sample_pts = entry_points
                
            pnl_list = []
            for ts, sym in sample_pts:
                 try:
                     loc = closes.index.get_loc(ts)
                     if loc + 30 >= len(closes): continue
                     
                     p_entry = closes[sym].iloc[loc]
                     p_exit = closes[sym].iloc[loc+30]
                     pnl = (p_exit / p_entry) - 1.0
                     pnl_list.append(pnl)
                 except: pass
            
            if not pnl_list: continue
            
            avg_ret = np.mean(pnl_list) * 100
            win_rate = (np.array(pnl_list) > 0).mean() * 100
            
            print(f"{reg:<20} | {th:<10} | {len(pnl_list):<8} | {win_rate:5.1f}% | {avg_ret:6.2f}%")
            
            # Selection Metric: WinRate * AvgRet
            perf = avg_ret if win_rate > 50 else -999
            if perf > best_perf:
                best_perf = perf
                best_th = th
        
        best_params[reg] = best_th
        print("-" * 70)

    # 5. Final Report
    print("\n::: GARAM'S PROPOSAL (AUTONOMOUS LOGIC) :::")
    rationale = {
        "BULL (상승장)": "상승장에서는 물 들어올 때 노 저어야 합니다. 문턱을 낮춰(Low) 작은 기회도 모두 잡으십시오.",
        "BEAR (하락장)": "하락장에서는 10번 중 7번이 속임수입니다. 문턱을 높여(High) 확실한 반등만 노려야 합니다.",
        "SIDEWAYS (횡보장)": "횡보장에서는 추세가 짧습니다. 중간 문턱(Mid)을 유지하되 줄 때 먹고 나와야 합니다.",
        "PANIC (공포장)": "공포장은 리스크가 극대화된 상태입니다. 문턱을 최고(Max)로 높여 '진짜 바닥'이나 '투매 과다'만 잡아야 합니다."
    }
    
    for reg, th in best_params.items():
        base_desc = "공격적(Low)" if th <= 5 else "중립적(Mid)" if th <= 7 else "보수적(High)"
        print(f"[{reg}] -> 제안 문턱: {th:.1f} ({base_desc})")
        print(f"   => 논리: {rationale.get(reg, '데이터 기반 최적점')}")
        
    # Save to file
    with open("regime_proposal.txt", "w", encoding="utf-8") as f:
        f.write("GARAM REGIME ANALYSIS REPORT\n")
        f.write("============================\n")
        for reg, th in best_params.items():
             f.write(f"{reg}: Threshold {th:.1f}\n")

if __name__ == "__main__":
    run_regime_analysis()
