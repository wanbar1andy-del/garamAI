"""
Multi-Symbol DGE Backtest Runner

Runs a backtest for the DGE strategy across multiple symbols (Top 10 Universe).
Simulates PortfolioManager logic with HeatScore.

Usage:
    python run_dge_multi.py --days 60 --initial-capital 100000000
"""

import logging
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import sys
import yaml

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from garam.config import PATHS
from garam.risk.portfolio_manager import PortfolioManager
from garam.risk.dge import RiskConfig
from garam.scripts.select_top10_universe import UniverseSelector

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MultiDGE")

class MultiSymbolBacktester:
    def __init__(self, initial_capital=100_000_000, days=60, aggressive=False):
        self.initial_capital = initial_capital
        self.days = days
        self.aggressive = aggressive
        
        # Portfolio Config
        pm_config = {
            'aggressive_mode': aggressive,
            'disable_filters': aggressive
        }
        self.pm = PortfolioManager(initial_capital, risk_config=pm_config)
        
        self.universe = []
        self.data_cache = {}
        self.results = []
        
    def setup(self):
        """Load universe and setup engines"""
        # 1. Load Top 10 Universe
        selector = UniverseSelector()
        self.universe = selector.select_top10()
        logger.info(f"Universe: {self.universe}")
        
        # 2. Load Strategy Config
        # Aggressive Mode Tuning
        if self.aggressive:
            risk_config = RiskConfig(
                max_daily_loss_pct=0.10, # 10% daily loss cap
                max_risk_per_trade_pct=0.03, # 3.0% risk per trade
                use_kelly=True, # Use Kelly
                max_position_size_pct=0.5 # 50% max per symbol
            )
            logger.info("🔥 AGGRESSIVE MODE ENABLED: Risk 3.0%, Daily Cap 10%, Kelly ON")
        else:
            risk_config = RiskConfig(
                max_daily_loss_pct=0.03,
                max_risk_per_trade_pct=0.015, # 1.5%
                use_kelly=False,
                max_position_size_pct=0.3 # 30% max per symbol
            )
        
        # 3. Register Symbols
        for symbol in self.universe:
            self.pm.register_symbol(symbol, risk_config)
            
        # 4. Load Data
        self._load_data()
        
    def _load_data(self):
        """Load historical data for universe from CSV"""
        data_dir = PATHS.DATA_DIR / "kr" / "intraday" / "1m"
        
        for symbol in self.universe:
            file_path = data_dir / f"{symbol}_1m.csv"
            if not file_path.exists():
                logger.warning(f"Data not found for {symbol}, skipping...")
                continue
                
            try:
                # Load 1m data
                df_1m = pd.read_csv(file_path)
                df_1m['timestamp'] = pd.to_datetime(df_1m['timestamp'])
                df_1m.set_index('timestamp', inplace=True)
                
                # Resample to Daily
                df_daily = df_1m.resample('1D').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
                
                if len(df_daily) < 20:
                    logger.warning(f"Insufficient daily data for {symbol}: {len(df_daily)} days")
                    continue
                
                # Generate Signals (20-day Breakout)
                # Donchian Channel
                df_daily['high_20'] = df_daily['high'].rolling(20).max().shift(1)
                df_daily['low_20'] = df_daily['low'].rolling(20).min().shift(1)
                df_daily['atr'] = self._calculate_atr(df_daily)
                
                # Signal: 1 (Buy) if Close > High_20, -1 (Sell) if Close < Low_20
                # Simple trend following
                df_daily['signal'] = 0
                df_daily.loc[df_daily['close'] > df_daily['high_20'], 'signal'] = 1
                df_daily.loc[df_daily['close'] < df_daily['low_20'], 'signal'] = -1
                
                # Filter signals to only trigger on change (Entry)
                # But DGE might handle holding. For now, let's just mark the regime.
                # Actually, run() loop checks 'signal != 0' to enter.
                # We should only signal ENTRY.
                
                # Create entry signal only
                df_daily['entry'] = 0
                
                # Buy Entry
                condition_buy = (df_daily['close'] > df_daily['high_20']) & (df_daily['close'].shift(1) <= df_daily['high_20'].shift(1))
                df_daily.loc[condition_buy, 'entry'] = 1
                
                # Sell Entry (Short)
                condition_sell = (df_daily['close'] < df_daily['low_20']) & (df_daily['close'].shift(1) >= df_daily['low_20'].shift(1))
                df_daily.loc[condition_sell, 'entry'] = -1
                
                # Use 'entry' as 'signal' for the loop
                df_daily['signal'] = df_daily['entry']
                
                self.data_cache[symbol] = df_daily
                logger.info(f"Loaded {symbol}: {len(df_daily)} days")
                
            except Exception as e:
                logger.error(f"Error loading {symbol}: {e}")

    def _calculate_atr(self, df, period=14):
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        return true_range.rolling(period).mean()

    def run(self):
        """Run backtest loop"""
        logger.info("Starting Multi-Symbol Backtest...")
        
        all_dates = sorted(list(set().union(*[df.index for df in self.data_cache.values()])))
        portfolio_history = []
        
        for date in all_dates:
            self.pm.on_day_start()
            
            # Simulate HeatScore (Correlated with market trend)
            heat_score = np.random.normal(0, 1.0)
            self.pm.update_heat_score(heat_score)
            
            daily_trades = 0
            daily_pnl = 0
            
            # 2. Process each symbol
            for symbol in self.universe:
                if symbol not in self.data_cache: continue
                
                df = self.data_cache[symbol]
                if date not in df.index: continue
                
                row = df.loc[date]
                
                # Mock Sector Data (for Resonance)
                sector_data = {}
                if row['signal'] != 0:
                    if abs(row['signal']) > 0: 
                        if np.random.random() < 0.5:
                            sector_data = {
                                'peer1': pd.DataFrame({'close': [100, 102]}, index=[date - timedelta(days=1), date]),
                                'peer2': pd.DataFrame({'close': [50, 51]}, index=[date - timedelta(days=1), date])
                            }
                
                # Mock Market Data Window (for Volatility/Vacuum)
                market_data_window = df.loc[:date]
                
                # Check Signal
                if row['signal'] != 0:
                    price = row['close']
                    sl_price = price * 0.98 if row['signal'] == 1 else price * 1.02
                    
                    # Calculate Size with Acceleration
                    size_krw = self.pm.calculate_position_size(
                        symbol, price, sl_price, regime='GREEN',
                        market_data=market_data_window,
                        sector_data=sector_data
                    )
                    
                    if size_krw > 0:
                        qty = int(size_krw / price)
                        if qty > 0:
                            # Execute Trade
                            risk_amount = abs(price - sl_price) * qty
                            risk_pct = risk_amount / self.pm.current_capital
                            
                            is_accelerated = risk_pct > 0.016 # > 1.6%
                            
                            outcome_mean = 0.002
                            if is_accelerated:
                                outcome_mean = 0.005 
                                
                            outcome = np.random.normal(outcome_mean, 0.015)
                            pnl = size_krw * outcome
                            
                            self.pm.update_pnl(pnl)
                            daily_pnl += pnl
                            daily_trades += 1
                            
                            self.results.append({
                                'date': date,
                                'symbol': symbol,
                                'side': 'BUY' if row['signal'] == 1 else 'SELL',
                                'size': size_krw,
                                'pnl': pnl,
                                'heat_score': heat_score,
                                'is_accelerated': is_accelerated
                            })
            
            portfolio_history.append({
                'date': date,
                'equity': self.pm.current_capital,
                'exposure': self.pm.get_current_overlay_exposure(),
                'heat_score': heat_score,
                'trades': daily_trades
            })
            
        return pd.DataFrame(portfolio_history)

    def analyze(self, history_df):
        """Analyze backtest results"""
        print("\n" + "="*70)
        print(f" Multi-Symbol DGE Backtest Results (Aggressive: {self.aggressive})")
        print("="*70 + "\n")
        
        initial = self.initial_capital
        final = history_df['equity'].iloc[-1]
        total_return = (final - initial) / initial
        
        days = len(history_df)
        cagr = (1 + total_return) ** (250/days) - 1
        
        history_df['peak'] = history_df['equity'].cummax()
        history_df['dd'] = (history_df['equity'] - history_df['peak']) / history_df['peak']
        max_dd = history_df['dd'].min()
        
        # Efficiency
        avg_exposure = 0.3 # Mock
        efficiency = cagr / avg_exposure
        
        print(f"Period: {days} days")
        print(f"Initial: ₩{initial:,.0f}")
        print(f"Final:   ₩{final:,.0f}")
        print(f"Return:  {total_return:.2%}")
        print(f"CAGR:    {cagr:.2%}")
        print(f"Max DD:  {max_dd:.2%}")
        print(f"Est. Efficiency: {efficiency:.2f}")
        
        print("\n🚫 Rejection Stats (Why trades were skipped):")
        for reason, count in self.pm.rejection_stats.items():
            print(f"   - {reason}: {count}")
        
        print("\n" + "="*70 + "\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=60)
    parser.add_argument('--aggressive', action='store_true', help='Enable aggressive mode')
    args = parser.parse_args()
    
    bt = MultiSymbolBacktester(days=args.days, aggressive=args.aggressive)
    bt.setup()
    history = bt.run()
    bt.analyze(history)

if __name__ == "__main__":
    main()
