"""
Compute Regime Summary
- Inputs: trades_by_regime.csv, equity_curve.csv (optional for MDD)
- Outputs: summary_by_regime.csv, summary_by_market_phase.csv
"""
import pandas as pd
import numpy as np
import sys
import argparse

def compute_stats(group_df):
    if group_df.empty:
        return pd.Series({
            'num_trades': 0,
            'win_rate': 0.0,
            'total_return': 0.0,
            'avg_trade_return': 0.0,
            'avg_win_pct': 0.0,
            'avg_loss_pct': 0.0,
            'profit_factor': 0.0,
            'avg_holding_days': 0.0
        })
        
    wins = group_df[group_df['pnl'] > 0]
    losses = group_df[group_df['pnl'] <= 0]
    
    num_trades = len(group_df)
    win_rate = len(wins) / num_trades
    total_pnl = group_df['pnl'].sum()
    # Approx Total Return (sum of trade returns - not accurate for portfolio but good for relative comparison)
    total_return = group_df['return_pct'].sum() 
    
    avg_trade_return = group_df['return_pct'].mean()
    avg_win_pct = wins['return_pct'].mean() if not wins.empty else 0.0
    avg_loss_pct = losses['return_pct'].mean() if not losses.empty else 0.0
    
    gross_profit = wins['pnl'].sum()
    gross_loss = abs(losses['pnl'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Holding Days
    group_df['entry_time'] = pd.to_datetime(group_df['entry_time'])
    group_df['exit_time'] = pd.to_datetime(group_df['exit_time'])
    avg_holding_days = (group_df['exit_time'] - group_df['entry_time']).dt.total_seconds().mean() / 86400
    
    return pd.Series({
        'num_trades': num_trades,
        'win_rate': win_rate,
        'total_return': total_return,
        'avg_trade_return': avg_trade_return,
        'avg_win_pct': avg_win_pct,
        'avg_loss_pct': avg_loss_pct,
        'profit_factor': profit_factor,
        'avg_holding_days': avg_holding_days
    })

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trades-file', required=True)
    parser.add_argument('--output-regime', required=True)
    parser.add_argument('--output-phase', required=True)
    args = parser.parse_args()
    
    trades = pd.read_csv(args.trades_file)
    
    # Group by Regime
    regime_stats = trades.groupby('entry_regime').apply(compute_stats).reset_index()
    regime_stats.to_csv(args.output_regime, index=False)
    print(f"Regime summary saved to {args.output_regime}")
    
    # Group by Phase
    phase_stats = trades.groupby('entry_phase').apply(compute_stats).reset_index()
    phase_stats.to_csv(args.output_phase, index=False)
    print(f"Phase summary saved to {args.output_phase}")

if __name__ == "__main__":
    main()
