"""
Walk-Forward Optimization (WFO) Engine
Executes a rolling window optimization for the Multi-Horizon Policy.
"""

import pandas as pd
import numpy as np
import pickle
import argparse
from pathlib import Path
import sys
import yaml
import copy
import random
from datetime import timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.research.regime.miracle_engine import (
    MiracleBacktester, Policy, 
    ImmediateBreakoutEntry, SignalReversalExit, FixedTargetExit, DGERisk
)

# ==========================================
# Configuration & Search Space
# ==========================================

class WFOConfig:
    def __init__(self, mode="SWING"):
        self.train_days = 365 * 2 # 2 Years
        self.test_days = 180      # 6 Months
        self.n_trials = 20        # Number of random search trials per window
        self.mode = mode
        
        # Frequency Constraints
        if self.mode == "DGE":
            self.min_trades_per_year = 50
        else:
            self.min_trades_per_year = 5 # Minimal check for Swing
        
    @property
    def step_days(self):
        return self.test_days

SEARCH_SPACE = {
    # Coordination Rules Thresholds
    'fs_entry_thresh': [0.3, 0.5, 0.7, 0.8],
    'fm_entry_thresh': [-0.2, 0.0, 0.2, 0.4],
    'fs_exit_thresh': [-0.5, -0.3, -0.1, 0.0],
    
    # Horizon Model Params
    'short_window': [3, 5, 10],
    'mid_window': [20, 40, 60, 100],
    
    # Risk Params (Relative)
    'size_mod_scalp': [0.3, 0.5, 1.0],
}

# ==========================================
# Helper Functions
# ==========================================

def load_data(path):
    if not Path(path).exists():
        raise FileNotFoundError(f"Data not found: {path}")
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').sort_index()
    
    # Pre-calculate ALL potential indicators needed by search space
    # This is faster than calculating inside the loop
    for w in [3, 5, 10, 20, 40, 60, 100, 120]:
        df[f'ma_{w}'] = df['close'].rolling(window=w).mean()
        df[f'mom_{w}'] = df['close'].pct_change(w)
        # Trend proxy: Slope of MA
        df[f'trend_{w}'] = df[f'ma_{w}'].pct_change(1)
        
    df = df.fillna(0)
    return df

def generate_random_params(space):
    params = {}
    for k, v in space.items():
        params[k] = random.choice(v)
    return params

def update_policy_config(base_config, params):
    """
    Updates the base YAML config with selected parameters.
    """
    new_config = copy.deepcopy(base_config)
    
    # 1. Update Horizon Params
    new_config['horizons']['short']['params']['window'] = params['short_window']
    new_config['horizons']['mid']['params']['window'] = params['mid_window']
    
    # 2. Update Coordination Rules (Thresholds)
    # We need to find the specific rules and update their condition strings
    # This is a bit hacky with string replacement, but works for this structure
    
    rules = new_config['coordination_rules']
    
    # FLAT -> StrongTrendEntry
    flat_rules = next(r['rules'] for r in rules if r['state'] == 'FLAT')
    strong_entry = next(r for r in flat_rules if r['name'] == 'StrongTrendEntry')
    strong_entry['condition'] = f"fs > {params['fs_entry_thresh']} and fm >= {params['fm_entry_thresh']}"
    
    # FLAT -> ScalpEntry (Keep fixed relative to entry thresh or separate?)
    # Let's just update StrongTrendEntry for now as primary
    
    # LONG -> TrendReversal
    long_rules = next(r['rules'] for r in rules if r['state'] == 'LONG')
    reversal = next(r for r in long_rules if r['name'] == 'TrendReversal')
    reversal['condition'] = f"fs <= {params['fs_exit_thresh']} and fm < {params['fm_entry_thresh'] - 0.2}" # Heuristic
    
    return new_config

def calculate_objective(trades, start_date, end_date, config):
    if not trades:
        return -999.0
        
    total_pnl = sum(t.pnl_pct for t in trades)
    n_trades = len(trades)
    
    # Simple CAGR proxy
    days = (end_date - start_date).days
    years = days / 365.25
    if years == 0: years = 0.001
    
    # Frequency Check
    trades_per_year = n_trades / years
    if trades_per_year < config.min_trades_per_year:
        return -999.0
    
    cagr = total_pnl / years
    
    # Max Drawdown (approximate from trade stream)
    # Construct equity curve
    equity = [1.0]
    peak = 1.0
    max_dd = 0.0
    for t in trades:
        equity.append(equity[-1] * (1 + t.pnl_pct))
        peak = max(peak, equity[-1])
        dd = (peak - equity[-1]) / peak
        max_dd = max(max_dd, dd)
        
    score = cagr * (1 - max_dd) * np.log1p(n_trades)
    return score

# ==========================================
# Core WFO Logic
# ==========================================

def construct_policy_object(config):
    # Simplified version of run_policy_backtest.construct_policy
    # Assuming standard structure
    params = config.get('params', {})
    entry = ImmediateBreakoutEntry(params) # Placeholder, logic driven by Coordination
    exits = [SignalReversalExit(params), FixedTargetExit(params)]
    risk = DGERisk(params)
    
    horizons = config.get('horizons', {})
    coordination_rules = config.get('coordination_rules', [])
    
    return Policy(entry, exits, [], risk, horizons=horizons, coordination_rules=coordination_rules)

def optimize_window(df_train, base_config, wfo_config):
    best_score = -float('inf')
    best_params = None
    
    start_date = df_train.index[0]
    end_date = df_train.index[-1]
    
    for _ in range(wfo_config.n_trials):
        # 1. Sample Params
        params = generate_random_params(SEARCH_SPACE)
        
        # 2. Update Config
        trial_config = update_policy_config(base_config, params)
        policy = construct_policy_object(trial_config)
        
        # 3. Run Backtest
        tester = MiracleBacktester(df_train)
        trades = tester.run(policy)
        
        # 4. Evaluate
        score = calculate_objective(trades, start_date, end_date, wfo_config)
        
        if score > best_score:
            best_score = score
            best_params = params
            
    return best_params, best_score

def run_wfo(data_path, base_config_path, out_path, mode):
    print(f"Starting WFO (Mode: {mode})...")
    
    # 1. Load Data & Config
    df = load_data(data_path)
    with open(base_config_path, 'r') as f:
        base_config = yaml.safe_load(f)
        if 'policy' in base_config: base_config = base_config['policy']
        
    wfo_config = WFOConfig(mode=mode)
    
    # 2. Define Windows
    start_idx = 0
    max_idx = len(df)
    
    wfo_results = []
    all_test_trades = []
    
    current_date = df.index[0]
    final_date = df.index[-1]
    
    while True:
        train_end_date = current_date + timedelta(days=wfo_config.train_days)
        test_end_date = train_end_date + timedelta(days=wfo_config.test_days)
        
        if test_end_date > final_date:
            break
            
        print(f"\nProcessing Window: Train[{current_date.date()} ~ {train_end_date.date()}] -> Test[~ {test_end_date.date()}]")
        
        # Slice Data
        df_train = df[current_date:train_end_date]
        df_test = df[train_end_date:test_end_date]
        
        if len(df_train) < 100 or len(df_test) < 20:
            print("  Skipping: Insufficient data")
            current_date += timedelta(days=wfo_config.step_days)
            continue
            
        # 3. Optimize (Train)
        best_params, best_score = optimize_window(df_train, base_config, wfo_config)
        print(f"  Best Train Score: {best_score:.4f}")
        print(f"  Best Params: {best_params}")
        
        if best_params is None:
            print("  Optimization failed (no valid trades). Using default.")
            best_params = generate_random_params(SEARCH_SPACE) # Fallback
            
        # 4. Validate (Test)
        test_config = update_policy_config(base_config, best_params)
        test_policy = construct_policy_object(test_config)
        
        tester = MiracleBacktester(df_test)
        test_trades = tester.run(test_policy)
        
        n_test_trades = len(test_trades)
        test_pnl = sum(t.pnl_pct for t in test_trades)
        print(f"  Test Result: {n_test_trades} trades, {test_pnl:.2%} PnL")
        
        # Store Results
        wfo_results.append({
            'window_start': current_date,
            'train_end': train_end_date,
            'test_end': test_end_date,
            'best_params': best_params,
            'train_score': best_score,
            'test_trades': n_test_trades,
            'test_pnl': test_pnl
        })
        
        all_test_trades.extend(test_trades)
        
        # Move Window
        current_date += timedelta(days=wfo_config.step_days)
        
    # 5. Save Results
    print(f"\nTotal WFO Trades: {len(all_test_trades)}")
    
    result_pack = {
        'wfo_summary': wfo_results,
        'trades': all_test_trades
    }
    
    with open(out_path, 'wb') as f:
        pickle.dump(result_pack, f)
    print(f"Saved WFO results to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="g:/내 드라이브/garamdata/history/labeled_KR_KOSPI_daily_20y.csv")
    parser.add_argument("--config", default="c:/garam/garam/configs/policy_multi_horizon.yaml")
    parser.add_argument("--out", default="c:/garam/garam/data/wfo_results.pkl")
    parser.add_argument("--mode", default="SWING", choices=["SWING", "DGE"], help="Optimization Mode")
    args = parser.parse_args()
    
    run_wfo(args.data, args.config, args.out, args.mode)
