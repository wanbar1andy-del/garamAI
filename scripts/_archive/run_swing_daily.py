"""
Daily DGE Routine
Generates the trading plan for the next day based on:
1. Latest Market Data
2. Current Regime (RegimeRouter)
3. Optimized Policy (WFO Results)
"""

import pandas as pd
import numpy as np
import json
import pickle
import yaml
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from garam.live.regime_router import RegimeRouter
from garam.research.regime.miracle_engine import CoordinationEngine, Policy, ImmediateBreakoutEntry, SignalReversalExit, FixedTargetExit, DGERisk

def load_latest_data(path):
    if not Path(path).exists():
        raise FileNotFoundError(f"Data not found: {path}")
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').sort_index()
    return df

def load_wfo_params(path):
    if not Path(path).exists():
        print(f"Warning: WFO results not found at {path}. Using default params.")
        return None
        
    with open(path, 'rb') as f:
        data = pickle.load(f)
        
    # Get the latest window's best params
    wfo_summary = data.get('wfo_summary', [])
    if not wfo_summary:
        return None
        
    # Sort by test_end to find latest
    latest = sorted(wfo_summary, key=lambda x: x['test_end'])[-1]
    print(f"Loaded WFO params from window ending {latest['test_end'].date()}")
    return latest['best_params']

def calculate_signals(df, params):
    # Calculate indicators needed for fs, fm
    # fs: Momentum (short_window)
    # fm: Trend (mid_window)
    
    short_w = params.get('short_window', 5)
    mid_w = params.get('mid_window', 60)
    
    # Calculate on full history to ensure valid values
    close = df['close']
    
    # fs: Normalized Momentum (tanh scaled)
    mom = close.pct_change(short_w)
    # Scale factor assumption (from config or fixed)
    # In backtest config it was 100.0. Let's stick to that or params.
    fs = np.tanh(mom * 100.0)
    
    # fm: Normalized Trend (MA Slope)
    ma_mid = close.rolling(window=mid_w).mean()
    trend = ma_mid.pct_change(1)
    fm = np.tanh(trend * 50.0) # Scale factor 50.0
    
    return fs.iloc[-1], fm.iloc[-1]

def update_config_with_params(base_config, params):
    # Similar to run_wfo.py
    if not params: return base_config
    
    import copy
    new_config = copy.deepcopy(base_config)
    
    # Update Rules
    rules = new_config.get('coordination_rules', [])
    for r_group in rules:
        if r_group['state'] == 'FLAT':
            for r in r_group['rules']:
                if r['name'] == 'StrongTrendEntry':
                    r['condition'] = f"fs > {params['fs_entry_thresh']} and fm >= {params['fm_entry_thresh']}"
        elif r_group['state'] == 'LONG':
            for r in r_group['rules']:
                if r['name'] == 'TrendReversal':
                    r['condition'] = f"fs <= {params['fs_exit_thresh']} and fm < {params['fm_entry_thresh'] - 0.2}"
                    
    return new_config

def generate_plan(data_path, config_path, wfo_path, out_dir):
    print("Generating Daily DGE Plan...")
    
    # 1. Load Data
    df = load_latest_data(data_path)
    last_date = df.index[-1]
    print(f"Latest Data Date: {last_date.date()}")
    
    # 2. Regime
    router = RegimeRouter()
    regime_info = router.get_regime_details(df)
    print(f"Current Regime: {regime_info['regime']}")
    
    # 3. Load Params & Config
    wfo_params = load_wfo_params(wfo_path)
    
    with open(config_path, 'r') as f:
        base_config = yaml.safe_load(f)
        if 'policy' in base_config: base_config = base_config['policy']
        
    final_config = update_config_with_params(base_config, wfo_params)
    
    # 4. Calculate Signals
    # Use default params if WFO missing
    calc_params = wfo_params if wfo_params else {'short_window': 5, 'mid_window': 60}
    fs, fm = calculate_signals(df, calc_params)
    print(f"Signals: fs={fs:.4f}, fm={fm:.4f}")
    
    # 5. Determine Action
    # We need to know current state. For daily generation, we might assume FLAT or check current positions.
    # For this script, let's assume we are generating a plan for a NEW entry or managing existing.
    # Ideally, we pass "Current State" as arg. Default to FLAT for now.
    current_state = "FLAT" 
    
    engine = CoordinationEngine(final_config['coordination_rules'])
    action, action_params = engine.evaluate(current_state, fs, fm)
    print(f"Recommended Action: {action} (Params: {action_params})")
    
    # 6. Sizing (if Entry)
    size_pct = 0.0
    if action in ['ENTER_LONG', 'SCALP_LONG']:
        # Calculate DGE Size
        # Mocking DGE Risk calculation here or instantiating DGERisk
        # DGERisk needs a 'trade' object or similar context.
        # Let's do a simplified calc using DGE logic
        risk_per_trade = 0.01 # Fixed 1%
        # Volatility based sizing?
        # For now, just output the base risk % and let execution handle exact quantity
        size_pct = risk_per_trade * action_params.get('size_mod', 1.0)
        
    # 7. Output JSON
    plan = {
        'date': str(last_date.date()),
        'regime': regime_info,
        'signals': {'fs': fs, 'fm': fm},
        'wfo_params': wfo_params,
        'decision': {
            'state': current_state,
            'action': action,
            'action_params': action_params,
            'target_size_risk_pct': size_pct
        }
    }
    
    out_path = Path(out_dir) / f"swing_plan_{last_date.date()}.json"
    with open(out_path, 'w') as f:
        json.dump(plan, f, indent=4)
        
    print(f"Swing Plan saved to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="g:/내 드라이브/garamdata/history/labeled_KR_KOSPI_daily_20y.csv")
    parser.add_argument("--config", default="c:/garam/garam/configs/policy_multi_horizon.yaml")
    parser.add_argument("--wfo", default="c:/garam/garam/data/wfo_results.pkl")
    parser.add_argument("--out", default="c:/garam/garam/data")
    args = parser.parse_args()
    
    generate_plan(args.data, args.config, args.wfo, args.out)
