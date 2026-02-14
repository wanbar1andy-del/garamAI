import pandas as pd
import numpy as np
import itertools
from pathlib import Path
from run_backtest_final import calculate_signals_local, calculate_exhaustion_local, load_data

def run_optimization():
    print("::: GARAM TACTICAL CALIBRATION (REAL DATA) :::")
    print("목표: 2025.06 ~ 2026.02 하락장 구간 최대 수익 파라미터 발굴")
    
    # 1. Load Data (Real)
    data_dir = Path("c:/garam/garam/GARAM_Data/minute/kr")
    universe_file = "universe_test.csv"
    start_date = "20250601"
    end_date = "20260205"
    
    closes, volumes = load_data(data_dir, universe_file, start_date, end_date)
    if closes.empty: return

    # 2. Base Signals (V3)
    base_signals = calculate_signals_local(closes, volumes)
    exhaustion = calculate_exhaustion_local(closes, volumes)
    
    # 3. Grid Search Space
    # 하락장에서는 짧게 먹고(Short Target) 빨리 튀거나(Tight Stop),
    # 아니면 아예 큰 것만 노려야(High Thresh) 함.
    stop_losses = [0.02, 0.03, 0.05]       # 2%, 3%, 5%
    take_profits = [0.03, 0.05, 0.10]      # 3%, 5%, 10%
    thresholds = [5.0, 7.0, 9.0]           # 진입 장벽
    hurdles = [0.02, 0.05]                 # 최소 기대 수익
    
    best_roi = -999.0
    best_params = None
    best_trades = 0
    
    combinations = list(itertools.product(stop_losses, take_profits, thresholds, hurdles))
    print(f"[Optimization] 총 {len(combinations)}개 전술 시나리오 테스트 시작...")
    
    for stop, target, thresh, hurdle in combinations:
        # Simulate Result
        # Filter Signals by Threshold & Hurdle logic
        # Note: 'hurdle' logic was inside calculate_signals_local (hardcoded 0.02).
        # We can simulate threshold filtering here easily.
        # But hurdle filtering is baked in 0.02. 
        # For optimization speed, let's assume hurdle 0.02 base, and filter strictly by NeuroScore threshold.
        # (NeuroScore correlates with conviction, so higher thresh = better quality)
        
        current_signals = base_signals * base_signals.ge(thresh).astype(float)
        
        cash = 1_000_000
        initial_capital = cash
        equity = cash
        
        trades_count = 0
        pos_sym = None
        pos_qty = 0
        entry_px = 0.0
        
        # Fast Loop
        # Vectorized simulation is hard with path dependency (cash).
        # Use simple simplified loop.
        
        # Pre-calculate entry events to save time? 
        # No, sequential is needed for capital check.
        
        for ts in closes.index:
            # Check Exit
            if pos_sym:
                curr_px = closes.at[ts, pos_sym]
                if pd.isna(curr_px): continue
                
                # Check Stop/Target
                ret = (curr_px / entry_px) - 1.0
                
                # Prophet Exit (Exhaustion)
                is_exhausted = exhaustion.at[ts, pos_sym] if pos_sym in exhaustion.columns else False
                
                exit_signal = False
                if ret < -stop: exit_signal = True
                elif ret > target: exit_signal = True
                elif is_exhausted: exit_signal = True
                
                if exit_signal:
                    cash += pos_qty * curr_px * 0.998 # 0.2% fee+slip
                    pos_sym = None
                    pos_qty = 0
                    continue
            
            # Check Entry
            if pos_sym is None:
                # Get candidates
                row = current_signals.loc[ts]
                cands = row[row > 0]
                if not cands.empty:
                    # Pick best
                    sym = cands.idxmax()
                    price = closes.at[ts, sym]
                    if price > 0:
                        # Full Bet (Guerrilla)
                        qty = int((cash * 0.98) / (price * 1.002))
                        if qty > 0:
                            cash -= qty * price * 1.002 # Buy cost
                            pos_sym = sym
                            pos_qty = qty
                            entry_px = price
                            trades_count += 1
        
        # End simulation
        if pos_sym:
            curr_px = closes.iloc[-1].get(pos_sym, entry_px)
            cash += pos_qty * curr_px * 0.998
            
        roi = (cash / initial_capital) - 1.0
        
        if roi > best_roi:
            best_roi = roi
            best_params = (stop, target, thresh, hurdle)
            best_trades = trades_count
            print(f" -> 신기록! ROI: {roi*100:+.2f}% | Stop:{stop} Target:{target} Thresh:{thresh} (매매 {trades_count}회)")

    print("\n" + "="*50)
    print("🏆 [최적화 결과] 챔피언 파라미터")
    print(f"수익률      : {best_roi*100:+.2f}%")
    print(f"손절(Stop)  : {best_params[0]*100}%")
    print(f"익절(Target): {best_params[1]*100}%")
    print(f"진입장벽    : {best_params[2]}점")
    print(f"매매횟수    : {best_trades}회")
    print("="*50)
    
    # Save to file
    with open("optimization_result.txt", "w") as f:
        f.write(f"ROI: {best_roi}\nParams: {best_params}")

if __name__ == "__main__":
    run_optimization()
