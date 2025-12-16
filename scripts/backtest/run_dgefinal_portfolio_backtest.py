"""
DGE Final Portfolio Backtest Engine
- Universe: 100 Symbols
- Logic: Score-based Dynamic Allocation
- Compounding: 100% Reinvestment
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import matplotlib.pyplot as plt

def run_portfolio_backtest(universe_file, scores_file, start_date, end_date, initial_capital, max_weight, min_score, use_compounding, results_dir):
    print("=== DGE Final Portfolio Backtest ===")
    print(f"Capital: {initial_capital:,.0f}")
    print(f"Max Weight: {max_weight*100}%")
    print(f"Min Score: {min_score}")
    
    # Load Data
    scores_df = pd.read_csv(scores_file)
    scores_df['date'] = pd.to_datetime(scores_df['date'])
    
    # Pivot Scores: Index=Date, Columns=Symbol
    score_matrix = scores_df.pivot(index='date', columns='symbol', values='score').fillna(0)
    
    # Pre-load returns for all symbols
    print("Pre-loading returns for all symbols...")
    returns_data = {}
    data_dir = Path("g:/내 드라이브/garamdata/history/daily")
    
    for sym in score_matrix.columns:
        csv_file = data_dir / f"{sym}_daily.csv"
        if csv_file.exists():
            try:
                df = pd.read_csv(csv_file)
                # Standardize
                df.rename(columns={'일자': 'date', '현재가': 'close', 'timestamp': 'date'}, inplace=True)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)
                
                # Calculate Daily Return
                df['return'] = df['close'].pct_change()
                returns_data[sym] = df['return']
            except:
                pass
                
    returns_df = pd.DataFrame(returns_data)
    
    # Simulation Loop
    current_equity = initial_capital
    equity_curve = []
    daily_returns = []
    
    dates = score_matrix.index.sort_values()
    
    for d in dates:
        daily_scores = score_matrix.loc[d]
        
        # 1. Filter Candidates
        candidates = daily_scores[daily_scores >= min_score].sort_values(ascending=False)
        
        if candidates.empty:
            # All Cash ( 관망 )
            equity_curve.append({'date': d, 'equity': current_equity, 'exposure': 0.0, 'positions': 0})
            daily_returns.append(0.0)
            continue
            
        # 2. Allocate Weights (Sequential Concentration)
        # Rule: Sort by Score desc. Allocate Weight = Score until Capital is full (1.0).
        
        # 2. Allocate Weights (Sequential Concentration)
        # Rule: Sort by Score desc. Allocate Weight = Score until Capital is full (1.0).
        # CRITICAL FIX: Skip symbols with no return data for this date!
        
        weights = {}
        remaining_capacity = 1.0
        
        for sym, score in candidates.items():
            if remaining_capacity <= 0:
                break
                
            # Check Data Availability
            if sym not in returns_df.columns or d not in returns_df.index or pd.isna(returns_df.loc[d, sym]):
                # print(f"Skipping {sym} on {d} (No Data)")
                continue
                
            # Allocate min(Score, Remaining)
            w = min(score, remaining_capacity)
            weights[sym] = w
            remaining_capacity -= w
            
        # 3. Calculate PnL
        day_pnl = 0
        exposure = 0
        
        for sym, w in weights.items():
            symbol_ret = returns_df.loc[d, sym] # Guaranteed to exist now
            
            position_size = current_equity * w
            trade_pnl = position_size * symbol_ret
            
            day_pnl += trade_pnl
            exposure += w
            
        # Update Equity
        current_equity += day_pnl
        equity_curve.append({'date': d, 'equity': current_equity, 'exposure': exposure, 'positions': len(weights)})
        daily_returns.append(day_pnl / current_equity if current_equity > 0 else 0)

    # Save Selected Symbols
    selected_symbols = list(set(sym for d in dates for sym in score_matrix.loc[d][score_matrix.loc[d] >= min_score].index if score_matrix.loc[d, sym] >= min_score))
    # Actually, we only care about symbols that were *actually allocated* (Top N).
    # But to be safe, let's save all that met the threshold, or better, just the ones in 'weights' history.
    # Since we didn't store weights history, let's just save all candidates > min_score for now, 
    # OR better: modify the loop to track unique allocated symbols.
    
    # Re-running logic to capture unique allocated
    unique_allocated = set()
    for d in dates:
        daily_scores = score_matrix.loc[d]
        candidates = daily_scores[daily_scores >= min_score].sort_values(ascending=False)
        if candidates.empty: continue
        
        rem_cap = 1.0
        for sym, score in candidates.items():
            if rem_cap <= 0: break
            # Data check (same as loop)
            if sym not in returns_df.columns or d not in returns_df.index or pd.isna(returns_df.loc[d, sym]):
                continue
            unique_allocated.add(sym)
            rem_cap -= min(score, rem_cap)
            
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    pd.DataFrame({'symbol': list(unique_allocated)}).to_csv(Path(results_dir) / "selected_symbols.csv", index=False)
    print(f"Saved {len(unique_allocated)} unique selected symbols to selected_symbols.csv")

    # Results
    results_df = pd.DataFrame(equity_curve).set_index('date')
    final_equity = results_df.iloc[-1]['equity']
    total_return = (final_equity - initial_capital) / initial_capital
    
    print("-" * 30)
    print(f"Final Equity: {final_equity:,.0f}")
    print(f"Total Return: {total_return*100:.2f}%")
    
    # Save
    out_dir = Path(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(out_dir / "equity_curve.csv")
    print(f"Saved results to {out_dir}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--universe-file', required=True)
    parser.add_argument('--scores-file', required=True)
    parser.add_argument('--start-date', required=True)
    parser.add_argument('--end-date', required=True)
    parser.add_argument('--initial-capital', type=float, required=True)
    parser.add_argument('--max-weight-per-symbol', type=float, default=1.0)
    parser.add_argument('--min-top-score', type=float, default=0.3)
    parser.add_argument('--use-compounding', type=bool, default=True)
    parser.add_argument('--results-dir', required=True)
    args = parser.parse_args()
    
    run_portfolio_backtest(
        args.universe_file,
        args.scores_file,
        args.start_date,
        args.end_date,
        args.initial_capital,
        args.max_weight_per_symbol,
        args.min_top_score,
        args.use_compounding,
        args.results_dir
    )

if __name__ == "__main__":
    main()
