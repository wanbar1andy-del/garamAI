"""
Run Miracle Optimization
Performs a grid search over Policy Vectors to find the optimal strategy for each regime.
Updated to include Fixed Risk, Frequency Constraints, and DGE/Swing separation logic.
"""

import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import sys
import itertools
from concurrent.futures import ProcessPoolExecutor
import math

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS
from garam.research.regime.miracle_engine import (
    MiracleBacktester, Policy, Trade, PerformanceAnalyzer,
    ImmediateBreakoutEntry, ConfirmEntry,
    SignalReversalExit, FixedTargetExit, TimeStopExit,
    DGERisk, VolatilityFilter
)

# FIXED RISK CONFIG for Optimization
FIXED_RISK_PARAMS = {
    'max_daily_loss': 0.03,
    'risk_per_trade': 0.01, # 1% Fixed Risk
    'kelly_fraction': 0.0,  # No Kelly for optimization baseline
    'use_kelly': False
}

def calculate_active_days(trades, all_dates):
    """
    Calculates the number of days with an active position.
    """
    if not trades:
        return 0
    
    active_mask = pd.Series(False, index=all_dates)
    
    for t in trades:
        # Mark days between entry and exit as active
        # This is an approximation if intraday, but good for daily
        try:
            active_mask.loc[t.entry_time:t.exit_time] = True
        except KeyError:
            pass # Handle potential timestamp mismatches
            
    return active_mask.sum()

def evaluate_policy(args):
    """
    Worker function for parallel execution.
    """
    regime_data, entry_tmpl, exit_tmpls, filter_tmpls, params = args
    
    # Construct Policy
    if entry_tmpl == 'ImmediateBreakout':
        entry = ImmediateBreakoutEntry(params)
    elif entry_tmpl == 'ConfirmEntry':
        entry = ConfirmEntry(params)
    else:
        return None
        
    exits = []
    for et in exit_tmpls:
        if et == 'SignalReversal':
            exits.append(SignalReversalExit(params))
        elif et == 'FixedTarget':
            exits.append(FixedTargetExit(params))
        elif et == 'TimeStop':
            exits.append(TimeStopExit(params))
            
    filters = []
    for ft in filter_tmpls:
        if ft == 'VolatilityFilter':
            filters.append(VolatilityFilter(params))
            
    # Use FIXED DGERisk
    risk_params = params.copy()
    risk_params.update(FIXED_RISK_PARAMS)
    risk = DGERisk(risk_params)
            
    policy = Policy(entry, exits, filters, risk)
    tester = MiracleBacktester(regime_data)
    trades = tester.run(policy)
    
    if not trades:
        return {'score': -999, 'trades': 0}
        
    # Calculate Metrics using PerformanceAnalyzer
    total_days = (regime_data.index[-1] - regime_data.index[0]).days
    metrics = PerformanceAnalyzer.calculate_metrics(trades, total_days, regime_data.index)
    
    total_pnl = metrics['total_return']
    win_rate = metrics['win_rate']
    trades_per_year = metrics['trades_per_year']
    active_day_ratio = metrics['active_day_ratio']
    n_trades = metrics['trades']
    
    # Objective Function with Penalties
    # J = Total Return - Penalty(Low Freq)
    
    score = total_pnl
    
    # Frequency Penalty: Heavy penalty if < 10 trades/year (DGE requirement)
    # But for Swing Engine, we might accept lower.
    # Here we optimize for "Miracle" which should be robust.
    
    if trades_per_year < 5:
        score -= 10.0 # Huge penalty
    elif trades_per_year < 20:
        score -= 2.0 # Moderate penalty
        
    # Active Day Penalty (Optional)
    if active_day_ratio < 0.05:
        score *= 0.5 # Reduce score by half
        
    return {
        'score': score,
        'total_return': total_pnl,
        'win_rate': win_rate,
        'trades': n_trades,
        'trades_per_year': trades_per_year,
        'active_day_ratio': active_day_ratio,
        'params': params,
        'entry': entry_tmpl,
        'exits': exit_tmpls,
        'risk': 'DGERisk_Fixed',
        'filters': filter_tmpls
    }

def run_optimization():
    # 1. Load Data
    data_path = Path("g:/내 드라이브/garamdata/history/labeled_KR_KOSPI_daily_20y.csv")
    if not data_path.exists():
        print("Data not found.")
        return

    df = pd.read_csv(data_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').sort_index()
    
    # Filter 2005+
    df = df[df.index >= '2005-01-01']
    
    # Pre-calculate Indicators
    for w in [3, 5, 10, 15, 20, 30, 40, 50, 60, 100, 120, 200]:
        df[f'ma_{w}'] = df['close'].rolling(window=w).mean()
        
    for w in [5, 10, 20, 40]:
        for std in [1.0, 1.5, 2.0, 2.5, 3.0]:
            ma = df['close'].rolling(window=w).mean()
            s = df['close'].rolling(window=w).std()
            df[f'upper_{w}_{std}'] = ma + (s * std)
            df[f'lower_{w}_{std}'] = ma - (s * std)

    regimes = ['GREEN', 'YELLOW', 'RED']
    best_policies = {}

    # 2. Define Search Space
    
    # Trend Params
    trend_windows = list(itertools.product(
        [5, 10, 20], # fast
        [20, 60, 120] # slow
    ))
    
    # MR Params
    mr_params = list(itertools.product(
        [10, 20, 40], # window
        [1.5, 2.0, 2.5] # std
    ))
    
    # Exit Params
    exit_configs = [
        ['SignalReversal'],
        ['FixedTarget', 'TimeStop'],
        ['SignalReversal', 'TimeStop']
    ]
    
    sl_tp_params = list(itertools.product(
        [0.02, 0.05, 0.10], # SL
        [0.05, 0.10, 0.20]  # TP
    ))
    
    time_stop_days = [5, 10, 20, 40]
    
    # Filter Configs (Simplified)
    filter_configs = [
        [], # No filter
        # ['VolatilityFilter'] # Skip for speed in this run, or add if needed
    ]

    # 3. Optimization Loop
    for regime in regimes:
        print(f"\nOptimizing {regime}...")
        regime_data = df[df['state'] == regime].copy()
        
        tasks = []
        
        # Helper to add tasks
        def add_task(base_p, entry_t, exit_ts):
            for fc in filter_configs:
                p = base_p.copy()
                # Risk is fixed, so no loop over risk_configs
                tasks.append((regime_data, entry_t, exit_ts, fc, p))

        # A. Trend Strategies
        for fast, slow in trend_windows:
            if fast >= slow: continue
            
            base_params = {
                'strategy_type': 'TrendFollowing',
                'window_fast': fast, 
                'window_slow': slow
            }
            
            for exits in exit_configs:
                if 'FixedTarget' in exits:
                    for sl, tp in sl_tp_params:
                        p = base_params.copy()
                        p['sl_pct'] = sl
                        p['tp_pct'] = tp
                        if 'TimeStop' in exits:
                            for d in time_stop_days:
                                p2 = p.copy()
                                p2['max_days'] = d
                                add_task(p2, 'ImmediateBreakout', exits)
                        else:
                            add_task(p, 'ImmediateBreakout', exits)
                elif 'TimeStop' in exits:
                     for d in time_stop_days:
                        p = base_params.copy()
                        p['max_days'] = d
                        add_task(p, 'ImmediateBreakout', exits)
                else:
                    add_task(base_params, 'ImmediateBreakout', exits)

        # B. MR Strategies
        for w, std in mr_params:
            base_params = {
                'strategy_type': 'MeanReversion',
                'window': w,
                'std_dev': std
            }
            for sl, tp in sl_tp_params:
                p = base_params.copy()
                p['sl_pct'] = sl
                p['tp_pct'] = tp
                add_task(p, 'ImmediateBreakout', ['FixedTarget'])

        print(f"  Evaluating {len(tasks)} policies...")
        
        best_res = None
        # Sequential execution for now to avoid pickling issues with complex objects if any
        # Or use ProcessPoolExecutor if safe
        for t in tasks:
            res = evaluate_policy(t)
            if not res: continue
            
            if best_res is None or res['score'] > best_res['score']:
                best_res = res
                
        if best_res:
            print(f"  Best: {best_res['entry']} + {best_res['exits']}")
            print(f"  Params: {best_res['params']}")
            print(f"  Return: {best_res['total_return']:.2%} (Trades: {best_res['trades']}, Freq: {best_res['trades_per_year']:.1f}/yr)")
            
            best_policies[regime] = {
                'entry_template': best_res['entry'],
                'exit_templates': best_res['exits'],
                'risk_template': best_res['risk'],
                'filter_templates': best_res['filters'],
                'params': best_res['params'],
                'metrics': {
                    'total_return': float(best_res['total_return']),
                    'win_rate': float(best_res['win_rate']),
                    'trades': int(best_res['trades']),
                    'trades_per_year': float(best_res['trades_per_year']),
                    'active_day_ratio': float(best_res['active_day_ratio'])
                }
            }

    # 4. Save Results
    output_file = PATHS.CONFIG_DIR / "miracle_strategy_matrix_v2.yaml"
    with open(output_file, 'w') as f:
        yaml.dump(best_policies, f)
    print(f"\nSaved Miracle Matrix v2 to {output_file}")

if __name__ == "__main__":
    run_optimization()
