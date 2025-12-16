# scripts/research/run_strategy_loop.py
import sys
import argparse
import pandas as pd
from pathlib import Path

# Setup path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# Imports
from garam_core.strategy.registry import discover_strategies
from garam_core.backtest.engine_unified import run_backtest_unified
from garam_core.research.pulse.load_data import load_minute_data, enhance_features # Reuse loader
try:
    from scripts.research.reporter import generate_report
except ImportError:
    # Local import fix if running as script
    sys.path.append(str(Path(__file__).parent))
    from reporter import generate_report

def run_loop(symbol: str, data_dir: str):
    print(f"=== Starting Integrated Backtest Loop for {symbol} ===")
    
    # 1. Load Data
    try:
        print(f"Loading data from {data_dir}...")
        df = load_minute_data(symbol, data_dir)
        df = enhance_features(df)
        print(f"Loaded {len(df)} bars.")
    except Exception as e:
        print(f"Data Load Failed: {e}")
        return

    # 2. Discover Strategies
    strategies = discover_strategies()
    print(f"Discovered {len(strategies)} strategy classes: {[s.__name__ for s in strategies]}")
    
    results = []
    
    # 3. Execution Loop
    for StratClass in strategies:
        # Instantiate with default params (or we could have a config loader)
        try:
            strat = StratClass() 
            print(f"Testing {strat.name}...", end=" ")
            
            res = run_backtest_unified(strat, df)
            results.append(res)
            
            print(f"ROI: {res['roi']:.2%}, Trades: {res['trades']}")
        except Exception as e:
            print(f"Failed to run {StratClass.__name__}: {e}")
            
    # 4. Report
    if results:
        out_dir = PROJECT_ROOT / "reports"
        generate_report(results, out_dir)
    else:
        print("No results to report.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", help="Target symbol")
    parser.add_argument("--data_dir", default=str(PROJECT_ROOT/"GARAM_Data/minute/kr"), help="Data dir")
    args = parser.parse_args()
    
    run_loop(args.symbol, args.data_dir)
