
import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import glob

# ==========================================
# 1. PARAMETERS & CONFIG
# ==========================================
CONFIG = {
    'data_dir': 'GARAM_Data/60day_replay_kst',
    'initial_cash': 100_000_000,
    # Quantum Params
    'entry_threshold_score': 0.05,  # Min score to collapse superposition
    'switch_ratio': 1.2,            # New must be 20% better
    'min_hold_days': 1,
    'exit_rr_threshold': 0.95,      # Near exhaustion
    'stop_loss_pct': -0.05,         # Hard stop
    'shakeout_limit': 4.0,           # Texture limit (Validation)
    'vol_spike_smoothing': 20,
    'start_date': '2025-10-01',
    'end_date': '2025-12-31'
}

# ==========================================
# 2. DATA LOADER & FEATURE ENGINEERING
# ==========================================
def load_and_process_data(data_dir):
    print(f"Loading data from {data_dir}...")
    # Use Pathlib for robust path handling
    base_path = Path(data_dir)
    files = list(base_path.glob("*.csv"))
    
    if not files:
        print(f"DEBUG: No files found in {base_path.absolute()}")
        # Fallback check
        if not base_path.exists():
            print(f"ERROR: Directory {base_path} does not exist!")
            return {}
    
    all_dfs = {}
    
    for f in files:
        try:
            sym = f.stem
            df = pd.read_csv(f)
            
            # Standardize Columns
            if 'ts' in df.columns:
                df.rename(columns={'ts':'date'}, inplace=True)
            elif 'datetime' in df.columns:
                df.rename(columns={'datetime':'date'}, inplace=True)
            
            # Minimal validation
            req = ['date','open','high','low','close','volume']
            if not all(c in df.columns for c in req): continue
            
            # Sort & Daily Resample (if minute data)
            # Strategy requests Daily OHLCV
            df['date'] = df['date'].astype(str)
            df['day'] = df['date'].str.slice(0, 10)
            
            # Group by Day
            agg_funcs = {
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
            }
            if 'vwap' in df.columns: agg_funcs['vwap'] = 'last' # Approx
            
            daily = df.groupby('day').agg(agg_funcs).reset_index()
            daily['symbol'] = sym
            
            # FEATURE ENGINEERING
            # 1. Returns
            daily['ret5'] = daily['close'].pct_change(5)
            daily['ret20'] = daily['close'].pct_change(20)
            
            # 2. Volume Spike
            daily['vol_avg20'] = daily['volume'].rolling(20).mean()
            daily['vol_spike'] = daily['volume'] / (daily['vol_avg20'] + 1e-9)
            
            # 3. ATR 14
            daily['tr1'] = daily['high'] - daily['low']
            daily['tr2'] = abs(daily['high'] - daily['close'].shift(1))
            daily['tr3'] = abs(daily['low'] - daily['close'].shift(1))
            daily['tr'] = daily[['tr1','tr2','tr3']].max(axis=1)
            daily['atr14'] = daily['tr'].rolling(14).mean()
            
            # 4. Shakeout Texture (5-day vibration)
            # Sum of abs returns / Net return
            daily['abs_ret'] = daily['close'].pct_change().abs()
            daily['sum_abs_ret_5'] = daily['abs_ret'].rolling(5).sum()
            daily['net_ret_5'] = daily['close'].pct_change(5).abs()
            daily['shakeout_texture'] = daily['sum_abs_ret_5'] / (daily['net_ret_5'] + 1e-9)
            
            # Drop NaNs
            daily.dropna(inplace=True)
            
            if len(daily) > 20:
                all_dfs[sym] = daily
                
        except Exception as e:
            # print(f"Error loading {f}: {e}")
            pass
            
    print(f"Loaded {len(all_dfs)} symbols.")
    return all_dfs

# ==========================================
# 3. QUANTUM METRICS CALCULATION
# ==========================================
def compute_erc_rr_score(row):
    """
    Compute ERC, ReactionRatio, Probability Mass (Score)
    """
    price = row['close']
    ret5 = row['ret5'] if not pd.isna(row['ret5']) else 0
    ret20 = row['ret20'] if not pd.isna(row['ret20']) else 0
    vol_spike = row['vol_spike'] if not pd.isna(row['vol_spike']) else 1.0
    
    # ERC: Expected Target
    # Logic: Current Price * (1 + momentum_potential)
    # Momentum Potential = max(Ret20,0) + max(Ret5,0)*VolSpike contribution
    mom_pot = max(ret20, 0) + (max(ret5, 0) * min(vol_spike, 3.0)) # Cap spike at 3x
    erc = price * (1 + mom_pot)
    
    # ReactionRatio (RR)
    # Price / ERC. 
    # If ERC == Price, RR = 1.0 (Exhausted)
    # Ideally RR should be < 1.0. 
    # If price drops, RR drops.
    rr = price / (erc + 1e-9)
    
    # Score (Probability Mass)
    # Higher is better.
    # Base: Ret5 * VolSpike (Momentum Power)
    # Modifier: (1 - abs(RR - 0.5)) -> Prefer RR around 0.5 (Mid-flight), penalize 0.0 (start) and 1.0 (end)
    # We want a "Bell Curve" preference for Trend Maturity.
    
    maturity_factor = 1.0 - abs(rr - 0.5) * 2 # Normalized 0..1 (1 at 0.5)
    if maturity_factor < 0: maturity_factor = 0
    
    # Raw Score
    score = (ret5 * 100) * min(vol_spike, 3.0) * maturity_factor
    
    # Texture Penalty
    if row['shakeout_texture'] > CONFIG['shakeout_limit']:
        score = 0 # Too shaky, wave function decoherence
        
    return erc, rr, score

# ==========================================
# 4. SIMULATION LOOP (STATE MACHINE)
# ==========================================
def run_simulation(all_dfs):
    # Merge all days to find timeline
    timeline = set()
    data_by_date = {} # {date: {sym: row}}
    
    print("Indexing data...")
    for sym, df in all_dfs.items():
        # Pre-calc metrics
        # Vectorized is faster but row-based easier for logic reading
        # Let's simple apply row-wise for clarity or vectorized
        
        # Vectorized Calc
        mom_pot = np.maximum(df['ret20'], 0) + (np.maximum(df['ret5'], 0) * np.minimum(df['vol_spike'], 3.0))
        df['erc'] = df['close'] * (1 + mom_pot)
        df['rr'] = df['close'] / (df['erc'] + 1e-9)
        
        mf = 1.0 - np.abs(df['rr'] - 0.5) * 2
        mf = np.maximum(mf, 0)
        
        df['score'] = (df['ret5'] * 100) * np.minimum(df['vol_spike'], 3.0) * mf
        
        # Texture Filter
        df.loc[df['shakeout_texture'] > CONFIG['shakeout_limit'], 'score'] = 0
        
        # Index
        for row in df.itertuples():
            d = row.day
            timeline.add(d)
            if d not in data_by_date: data_by_date[d] = {}
            data_by_date[d][sym] = row
            
    sorted_days = sorted(list(timeline))
    sorted_days = [d for d in sorted_days if d >= CONFIG['start_date'] and d <= CONFIG['end_date']]
    
    # Simulation State
    cash = CONFIG['initial_cash']
    holdings = {} # {symbol: {qty, entry_px, entry_date, max_px}} # Only 1 Active Hero supported for pure test
    
    equity_curve = []
    trade_log = []
    
    current_hero = None # Active Symbol
    hero_hold_days = 0
    
    print(f"Starting Simulation on {len(sorted_days)} days...")
    
    for day in sorted_days:
        daily_data = data_by_date.get(day, {})
        if not daily_data: continue
        
        # 1. Update Portfolio Value
        current_eq = cash
        active_px = 0
        
        if current_hero:
            if current_hero in daily_data:
                row = daily_data[current_hero]
                pos = holdings[current_hero]
                val = pos['qty'] * row.close
                current_eq += val
                active_px = row.close
                
                # Update Max Px
                if row.high > pos['max_px']: holdings[current_hero]['max_px'] = row.high
            else:
                # Missing data? Assume flat or last
                pos = holdings[current_hero]
                val = pos['qty'] * pos['entry_px'] # Fallback
                current_eq += val
        
        equity_curve.append({'date': day, 'equity': current_eq, 'hero': current_hero if current_hero else 'CASH'})
        
        # 2. Ranking & Superposition (Top 5)
        # Sort all symbols by Score
        scores = []
        for sym, row in daily_data.items():
            if row.score > 0:
                scores.append((sym, row.score, row))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        top5 = scores[:5]
        
        top1_sym = top5[0][0] if top5 else None
        top1_score = top5[0][1] if top5 else 0
        
        # 3. State Machine
        
        # A. EXIT CHECKS (If Active)
        if current_hero:
            hero_hold_days += 1
            pos = holdings[current_hero]
            
            # Check Exit Conditions
            should_exit = False
            exit_reason = ""
            
            # Data availability
            if current_hero not in daily_data:
                should_exit = True
                exit_reason = "DATA_MISSING"
                cur_px = pos['entry_px'] # Fallback
            else:
                row = daily_data[current_hero]
                cur_px = row.close
                pnl_pct = (cur_px / pos['entry_px']) - 1
                
                # 1. Hard Stop
                if pnl_pct <= CONFIG['stop_loss_pct']:
                    should_exit = True
                    exit_reason = "STOP_LOSS"
                    
                # 2. Exhaustion (RR > threshold)
                if row.rr > CONFIG['exit_rr_threshold']:
                    should_exit = True
                    exit_reason = "EXHAUSTION_RR"
                    
                # 3. Broken Trend (Score < 0 or Low)
                if row.score <= 0:
                    should_exit = True
                    exit_reason = "SCORE_BROKEN"
                    
            if should_exit:
                # Execute Sell
                cash += pos['qty'] * cur_px * 0.999 # Commission
                trade_log.append({
                    'symbol': current_hero, 'entry_date': pos['entry_date'], 'exit_date': day,
                    'entry_px': pos['entry_px'], 'exit_px': cur_px, 'return': (cur_px/pos['entry_px'])-1,
                    'reason': exit_reason
                })
                del holdings[current_hero]
                current_hero = None
                hero_hold_days = 0
                
        # B. ENTRY / SWITCH CHECKS
        
        # If Cash (Candidate State) -> Active
        if not current_hero:
            if top1_sym and top1_score > CONFIG['entry_threshold_score']:
                # Collapse Superposition -> Enter Top1
                row = daily_data[top1_sym]
                qty = int(cash / row.close)
                if qty > 0:
                    cost = qty * row.close * 1.001 # Comm
                    cash -= cost
                    holdings[top1_sym] = {
                        'qty': qty, 'entry_px': row.close, 'entry_date': day, 'max_px': row.high
                    }
                    current_hero = top1_sym
                    hero_hold_days = 0
                    print(f"[{day}] ENTER HERO: {top1_sym} (Score: {top1_score:.2f})")

        # If Active -> Transfer (Switch)
        elif current_hero:
            # Check Switch
            # Condition: New Hero Score > Current Hero Score * Ratio
            # And Min Hold
            
            if top1_sym and top1_sym != current_hero and hero_hold_days >= CONFIG['min_hold_days']:
                # Get current hero score
                curr_row = daily_data.get(current_hero)
                curr_score = curr_row.score if curr_row else 0
                
                if top1_score > curr_score * CONFIG['switch_ratio']:
                    # EXECUTE SWITCH
                    # 1. Sell Current
                    pos = holdings[current_hero]
                    # Current Px
                    c_row = daily_data.get(current_hero)
                    c_px = c_row.close if c_row else pos['entry_px']
                    
                    cash += pos['qty'] * c_px * 0.999
                    trade_log.append({
                        'symbol': current_hero, 'entry_date': pos['entry_date'], 'exit_date': day,
                        'entry_px': pos['entry_px'], 'exit_px': c_px, 'return': (c_px/pos['entry_px'])-1,
                        'reason': f"SWITCH_TO_{top1_sym}"
                    })
                    del holdings[current_hero]
                    
                    # 2. Buy New
                    n_row = daily_data[top1_sym]
                    qty = int(cash / n_row.close)
                    if qty > 0:
                        cost = qty * n_row.close * 1.001
                        cash -= cost
                        holdings[top1_sym] = {
                            'qty': qty, 'entry_px': n_row.close, 'entry_date': day, 'max_px': n_row.high
                        }
                        current_hero = top1_sym
                        hero_hold_days = 0
                        print(f"[{day}] SWITCH: {current_hero} -> {top1_sym} (Score: {curr_score:.2f}->{top1_score:.2f})")
                        
    # Finalize
    print("Simulation Complete.")
    final_eq = equity_curve[-1]['equity']
    print(f"Final Equity: {final_eq:,.0f}")
    
    # Save Results
    pd.DataFrame(equity_curve).to_csv("quantum_hero_equity.csv", index=False)
    pd.DataFrame(trade_log).to_csv("quantum_hero_trades.csv", index=False)
    
if __name__ == "__main__":
    dfs = load_and_process_data(CONFIG['data_dir'])
    run_simulation(dfs)
