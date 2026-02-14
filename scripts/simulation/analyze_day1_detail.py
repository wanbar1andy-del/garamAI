import pandas as pd
from pathlib import Path
import sys

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

def analyze_day1():
    target_date = "2025-12-15"
    
    # 1. Load Trade Log
    sim_path = project_root / "results" / "simulation" / "week1_v1_1" / "trades_week1_policy_v1_1.csv"
    if not sim_path.exists():
        print("Simulation file not found")
        return

    df_trades = pd.read_csv(sim_path)
    df_trades['date'] = pd.to_datetime(df_trades['date'])
    df_day = df_trades[df_trades['date'] == target_date]
    
    if df_day.empty:
        print(f"No trades on {target_date}")
        return

    trades_count = len(df_day)
    unique_symbols = df_day['symbol'].unique()
    
    print(f"\n[Analysis for {target_date}]")
    print(f"Total Trades: {trades_count}")
    print(f"Traded Symbols ({len(unique_symbols)}): {list(unique_symbols)}")
    
    # Analyze PnL per symbol
    # Group by symbol and sum net_pnl
    pnl_by_sym = df_day.groupby('symbol')['net_pnl'].sum().sort_values(ascending=False)
    print("\n[PnL by Symbol]")
    print(pnl_by_sym)
    
    # 2. Load Oracle (Hero Rank)
    oracle_path = project_root / "results" / "labels" / f"day={target_date.replace('-','')}" / "hero_rank.csv"
    if not oracle_path.exists():
        print("Oracle file not found")
        return
        
    df_oracle = pd.read_csv(oracle_path)
    # Assume cols: symbol, score, total_return?
    # Let's check columns or just print head
    # Usually it has 'symbol', 'score', 'start_time', 'end_time', 'max_return'
    
    print("\n[Top-5 Oracle Heroes]")
    # Sort by 'total_return' or 'score'? Usually 'score' is the ranking metric.
    # Let's select Top-5 unique symbols
    top_heroes = df_oracle.drop_duplicates('symbol').head(5)
    print(top_heroes[['symbol', 'score', 'total_return']])
    
    # 3. Missed Opportunities
    print("\n[Missed Opportunities]")
    traded_set = set(unique_symbols)
    missed = []
    
    for _, row in top_heroes.iterrows():
        sym = row['symbol']
        if sym not in traded_set:
            missed.append(row)
            
    if not missed:
        print("None! Captured all Top-5 Heroes.")
    else:
        for m in missed:
            print(f"Missed {m['symbol']} (Score: {m['score']:.2f}, Ret: {m['total_return']*100:.2f}%)")

if __name__ == "__main__":
    analyze_day1()
