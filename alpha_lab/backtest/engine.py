import pandas as pd
import numpy as np
from typing import Dict, Any, Callable, List
import logging

logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    Core engine for running backtests on historical data.
    Simple event-driven simulation.
    """
    
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.0005):
        self.initial_capital = initial_capital
        self.commission = commission
        self.reset()

    def reset(self):
        self.cash = self.initial_capital
        self.position = 0
        self.equity_curve = []
        self.trades = []
        self.current_equity = self.initial_capital

    def run(self, df: pd.DataFrame, strategy_logic: Callable[[pd.Series, Dict], int]) -> Dict[str, Any]:
        """
        Execute backtest.
        
        Args:
            df: DataFrame with OHLCV and Features.
            strategy_logic: Function(row, context) -> signal (1: Buy, -1: Sell, 0: Hold)
            
        Returns:
            Dict with 'metrics', 'trades', 'equity_curve'
        """
        self.reset()
        logger.info(f"Starting backtest on {len(df)} bars.")
        
        context = {} # Strategy context (e.g. for stateful strategies)
        
        for i, row in df.iterrows():
            # 1. Update Equity (Mark to Market)
            price = row['close']
            market_value = self.position * price
            self.current_equity = self.cash + market_value
            self.equity_curve.append({'timestamp': row['timestamp'] if 'timestamp' in row else row.name, 'equity': self.current_equity})
            
            # 2. Get Signal
            signal = strategy_logic(row, context)
            
            # 3. Execute Signal
            if signal == 1 and self.position == 0:
                # Buy (All-in for simplicity in v0)
                shares = int(self.cash / price)
                if shares > 0:
                    cost = shares * price
                    fee = cost * self.commission
                    self.cash -= (cost + fee)
                    self.position = shares
                    self.trades.append({
                        'type': 'BUY', 'price': price, 'shares': shares, 
                        'time': row['timestamp'] if 'timestamp' in row else row.name,
                        'cost': cost, 'fee': fee
                    })
                    
            elif signal == -1 and self.position > 0:
                # Sell (Close all)
                revenue = self.position * price
                fee = revenue * self.commission
                self.cash += (revenue - fee)
                
                # Calculate PnL for this trade cycle
                last_buy = next((t for t in reversed(self.trades) if t['type'] == 'BUY'), None)
                pnl = 0
                if last_buy:
                    pnl = revenue - last_buy['cost'] - fee - last_buy['fee']
                
                self.trades.append({
                    'type': 'SELL', 'price': price, 'shares': self.position, 
                    'time': row['timestamp'] if 'timestamp' in row else row.name,
                    'revenue': revenue, 'fee': fee, 'pnl': pnl
                })
                self.position = 0
                
        # Finalize
        final_equity = self.current_equity
        total_return = (final_equity - self.initial_capital) / self.initial_capital
        
        results = {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'total_trades': len([t for t in self.trades if t['type'] == 'SELL']),
            'trades': self.trades,
            'equity_curve': pd.DataFrame(self.equity_curve)
        }
        
        logger.info(f"Backtest complete. Return: {total_return:.2%}")
        return results
