"""
Run Policy Backtest
Executes a specific Policy (defined by YAML or arguments) and saves the result (trades, equity) to a pickle file.
This serves as the input generator for Gap Analysis.
"""

import pandas as pd
import pickle
import argparse
from pathlib import Path
import sys
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS
from garam.research.regime.miracle_engine import (
    MiracleBacktester, Policy, 
    ImmediateBreakoutEntry, ConfirmEntry,
    SignalReversalExit, FixedTargetExit, TimeStopExit,
    StandardRisk, DGERisk, VolatilityFilter, RegimeFilter
)

def load_data(path):
    if not Path(path).exists():
        raise FileNotFoundError(f"Data not found: {path}")
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').sort_index()
    # Pre-calculate indicators (simplified for now, should match optimization script)
    for w in [3, 5, 10, 20, 40, 60, 100, 120]:
        df[f'ma_{w}'] = df['close'].rolling(window=w).mean()
        # Momentum: ROC
        df[f'mom_{w}'] = df['close'].pct_change(w)
        # Trend: MA Slope
        df[f'trend_{w}'] = df[f'ma_{w}'].pct_change(1)
        
    # Fill NA
    df = df.fillna(0)
    return df

def construct_policy(config):
    """
    Constructs a Policy object from a dictionary configuration.
    """
    params = config.get('params', {})
    
    # Entry
    entry_tmpl = config.get('entry_template')
    if entry_tmpl == 'ImmediateBreakout' or entry_tmpl == 'ImmediateBreakoutEntry':
        entry = ImmediateBreakoutEntry(params)
    elif entry_tmpl == 'ConfirmEntry':
        entry = ConfirmEntry(params)
    else:
        raise ValueError(f"Unknown Entry Template: {entry_tmpl}")
        
    # Exits
    exits = []
    for et in config.get('exit_templates', []):
        if et == 'SignalReversal' or et == 'SignalReversalExit':
            exits.append(SignalReversalExit(params))
        elif et == 'FixedTarget' or et == 'FixedTargetExit':
            exits.append(FixedTargetExit(params))
        elif et == 'TimeStop' or et == 'TimeStopExit':
            exits.append(TimeStopExit(params))
            
    # Filters
    filters = []
    for ft in config.get('filter_templates', []):
        if ft == 'VolatilityFilter':
            filters.append(VolatilityFilter(params))
        elif ft == 'RegimeFilter':
            filters.append(RegimeFilter(params))
            
    # Risk
    risk_tmpl = config.get('risk_template', 'StandardRisk')
    if risk_tmpl == 'DGERisk' or risk_tmpl == 'DGERisk_Fixed':
        risk = DGERisk(params)
    else:
        risk = StandardRisk(params)
        
    # Multi-Horizon
    horizons = config.get('horizons', {})
    coordination_rules = config.get('coordination_rules', [])
        
    return Policy(entry, exits, filters, risk, horizons=horizons, coordination_rules=coordination_rules)

def main():
    parser = argparse.ArgumentParser(description="Run Policy Backtest")
    parser.add_argument("--config", type=str, required=True, help="Path to Policy YAML config")
    parser.add_argument("--data", type=str, default="g:/내 드라이브/garamdata/history/labeled_KR_KOSPI_daily_20y.csv", help="Path to data CSV")
    parser.add_argument("--out", type=str, required=True, help="Output pickle file path")
    parser.add_argument("--regime", type=str, default="GREEN", help="Regime to filter data by (optional)")
    
    args = parser.parse_args()
    
    # 1. Load Data
    print(f"Loading data from {args.data}...")
    df = load_data(args.data)
    
    # 2. Load Policy
    print(f"Loading policy from {args.config}...")
    with open(args.config, 'r') as f:
        policy_config = yaml.safe_load(f)
    print(f"DEBUG: Loaded config keys: {policy_config.keys()}")
    if 'policy' in policy_config:
        print("DEBUG: Found 'policy' key, unwrapping...")
        policy_config = policy_config['policy']
    print(f"DEBUG: Config keys after unwrap: {policy_config.keys()}")
        
    # Inject RegimeFilter if regime is specified and not ALL/NONE
    if args.regime and args.regime.upper() not in ['ALL', 'NONE']:
        print(f"Enforcing regime: {args.regime}")
        if 'filter_templates' not in policy_config:
            policy_config['filter_templates'] = []
        if 'RegimeFilter' not in policy_config['filter_templates']:
            policy_config['filter_templates'].append('RegimeFilter')
        
        if 'params' not in policy_config:
            policy_config['params'] = {}
        policy_config['params']['allowed_regimes'] = [args.regime]
        
    policy = construct_policy(policy_config)
    
    # 3. Run Backtest
    print("Running backtest...")
    tester = MiracleBacktester(df)
    trades = tester.run(policy)
    
    # 4. Save Results
    result = {
        'policy_config': policy_config,
        'trades': trades,
        'signal_logs': tester.signal_logs, # Added logs
        'data_path': args.data,
        'regime': args.regime
    }
    
    print(f"Saving {len(trades)} trades to {args.out}...")
    with open(args.out, 'wb') as f:
        pickle.dump(result, f)
        
    print("Done.")

if __name__ == "__main__":
    main()
