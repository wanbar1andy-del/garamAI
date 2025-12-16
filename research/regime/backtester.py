import pandas as pd
import numpy as np
from typing import Dict, List, Callable, Any
from dataclasses import dataclass

@dataclass
class Trade:
    entry_time: pd.Timestamp
    entry_price: float
    exit_time: pd.Timestamp
    exit_price: float
    signal: int
    regime: str
    pnl: float
    pnl_pct: float
    duration: int

class RegimeBacktester:
    """
    Backtests a strategy logic across different market regimes.
    """
    def __init__(self):
        pass

    def run(self, 
            data: pd.DataFrame, 
            strategy_func: Callable[[Dict[str, Any]], int], 
            price_col='close') -> List[Trade]:
        """
        Run backtest loop.
        
        Args:
            data: DataFrame with features and 'regime' column.
            strategy_func: Function taking a row dict and returning signal (1, -1, 0).
        """
        trades = []
        position = 0
        entry_price = 0.0
        entry_time = None
        
        # Ensure data is sorted
        data = data.sort_index()
        
        for i in range(len(data)):
            row = data.iloc[i]
            timestamp = data.index[i]
            price = row[price_col]
            regime = row.get('regime', 'UNKNOWN')
            
            # Convert row to dict for strategy
            # (In real system, we might pass more context)
            features = row.to_dict()
            features['timestamp'] = timestamp
            
            # Get Signal
            signal = strategy_func(features)
            
            # Simple execution logic (Long Only for now, or Long/Short)
            # Assuming Long Only for simplicity in this demo, or Reversal
            
            # Close existing position if signal opposes
            if position != 0:
                if (position == 1 and signal == -1) or (position == -1 and signal == 1):
                    # Exit
                    pnl = (price - entry_price) * position
                    pnl_pct = pnl / entry_price
                    duration = (timestamp - entry_time).days
                    
                    trades.append(Trade(
                        entry_time=entry_time,
                        entry_price=entry_price,
                        exit_time=timestamp,
                        exit_price=price,
                        signal=position,
                        regime=regime, # Regime at exit? Or entry? Usually Entry or Majority. Let's use Exit for now.
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        duration=duration
                    ))
                    position = 0
            
            # Open new position
            if position == 0 and signal != 0:
                position = signal
                entry_price = price
                entry_time = timestamp
                
        return trades

    def analyze_by_regime(self, trades: List[Trade]) -> pd.DataFrame:
        """
        Aggregate performance metrics by regime.
        """
        if not trades:
            return pd.DataFrame()
            
        df_trades = pd.DataFrame([t.__dict__ for t in trades])
        
        # Group by Regime
        stats = df_trades.groupby('regime').agg({
            'pnl_pct': ['count', 'mean', 'sum', 'std', 'min', 'max'],
            'duration': 'mean'
        })
        
        # Flatten columns
        stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
        
        # Add Win Rate
        win_rates = df_trades.groupby('regime').apply(lambda x: (x['pnl_pct'] > 0).mean())
        stats['win_rate'] = win_rates
        
        # Add Sharpe (Daily) - Approximate
        # Sharpe = Mean / Std
        stats['sharpe'] = stats['pnl_pct_mean'] / stats['pnl_pct_std']
        
        return stats
