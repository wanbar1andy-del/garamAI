"""
Historical Data Replay for Paper Trading
Replays past 1 year of market data to demonstrate live trading system behavior
Uses virtual money and shows real-time flow
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import logging
import time

sys.path.insert(0, 'c:/garam')
from garam.config import PATHS
from garam.engine.controller import HybridController
from garam.engine.legacy import LegacyEngine
from garam.engine.advanced import AdvancedEngine

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("paper_trading_replay.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HistoricalReplayEngine:
    def __init__(self, start_date, end_date, initial_capital=100_000_000):
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.initial_capital = initial_capital
        self.current_equity = initial_capital
        self.current_cash = initial_capital
        self.positions = {}
        self.trade_history = []
        
        # Initialize Strategy A Controller
        # HybridController doesn't take engines as parameters, it creates them internally
        self.controller = HybridController()
        
        logger.info(f"Initialized Paper Trading Replay: {start_date} to {end_date}")
        logger.info(f"Initial Capital: {initial_capital:,} KRW")
        
    def load_market_data(self):
        """Load 1-year historical market data"""
        logger.info("Loading market data...")
        
        # Use top KOS PI symbols as universe (simplified)
        symbols = [
            "005930", "000660", "005380", "005490", "035420",  # Top 5
            "000270", "051910", "068270", "105560", "006400",  # Next 5
            "207940", "035720", "003670", "096770", "000810",  # Next 5
            "051900", "009150", "005935", "017670", "030200",  # Next 5
            "033780", "003550", "018260", "009830", "010130",  # Next 5
            "000100", "011200", "003490", "032830", "028260",  # Next 5
            "012330", "066570", "024110", "015760", "010950",  # Next 5
            "034730", "011170", "326030", "047810", "086790",  # Next 5
            "000720", "018880", "042660", "023530", "009540",  # Next 5
            "036570", "011070", "010140", "010060", "012450"   # Last 5 (Total 50)
        ]
        
        logger.info(f"Universe: {len(symbols)} symbols")
        
        # Load price data
        market_data = {}
        loaded_symbols = []
        
        for sym in symbols:
            csv_path = PATHS.HISTORY_DIR / f"labeled_KR_{sym}_daily_20y.csv"
            if not csv_path.exists():
                continue
                
            try:
                df = pd.read_csv(csv_path)
                df.columns = [c.lower() for c in df.columns]
                date_col = 'timestamp' if 'timestamp' in df.columns else 'date'
                df[date_col] = pd.to_datetime(df[date_col])
                df.set_index(date_col, inplace=True)
                df.sort_index(inplace=True)
                
                # Filter date range
                df = df.loc[self.start_date:self.end_date]
                
                if len(df) > 0:
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        if col not in market_data:
                            market_data[col] = {}
                        market_data[col][sym] = df[col]
                    loaded_symbols.append(sym)
                    
            except Exception as e:
                logger.warning(f"Failed to load {sym}: {e}")
                continue
        
        # Convert to DataFrame format
        for key in market_data:
            market_data[key] = pd.DataFrame(market_data[key])
        
        logger.info(f"Loaded {len(loaded_symbols)} symbols with data")
        return market_data, loaded_symbols
    
    def get_turbo_multiplier(self):
        """Read current turbo settings"""
        try:
            turbo_file = PATHS.DATA_DIR / "system" / "turbo_state.json"
            if turbo_file.exists():
                with open(turbo_file, 'r') as f:
                    state = json.load(f)
                    if state.get('mode') == 'manual':
                        return state.get('manual_value', 1.0)
            return 1.0  # Default
        except:
            return 1.0
    
    def execute_day(self, date, market_data, universe):
        """Execute one trading day"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Trading Day: {date.strftime('%Y-%m-%d')}")
        logger.info(f"{'='*60}")
        
        # Get signals from controller
        context = {
            'market_data': market_data,
            'universe': universe,
            'regime': 'R3_UP_BOX'  # Simplified
        }
        
        result_a = self.controller.eng1.analyze(date, context)
        signals = result_a.get('signals', {})
        
        if not signals:
            logger.info("No signals generated")
            return
        
        # Get top signals
        sorted_signals = sorted(signals.items(), key=lambda x: x[1], reverse=True)
        top_signals = sorted_signals[:20]  # Top 20
        
        logger.info(f"Generated {len(signals)} signals, selecting top {len(top_signals)}")
        
        # Get turbo multiplier
        multiplier = self.get_turbo_multiplier()
        logger.info(f"Turbo Multiplier: {multiplier}x")
        
        # Calculate position sizes
        total_score = sum([score for _, score in top_signals])
        target_positions = {}
        
        for sym, score in top_signals:
            weight = score / total_score if total_score > 0 else 0
            target_value = self.current_equity * weight * multiplier
            
            # Get current price
            if sym in market_data['close'].columns:
                price = market_data['close'][sym].loc[date]
                if pd.notna(price) and price > 0:
                    target_positions[sym] = {
                        'value': target_value,
                        'price': price,
                        'shares': int(target_value / price)
                    }
        
        # Execute trades (simplified - no transaction costs)
        logger.info(f"\nTarget Positions: {len(target_positions)}")
        
        # Close positions not in target
        for sym in list(self.positions.keys()):
            if sym not in target_positions:
                pos = self.positions[sym]
                sell_price = market_data['close'][sym].loc[date]
                sell_value = pos['shares'] * sell_price
                self.current_cash += sell_value
                
                pnl = sell_value - pos['cost']
                pnl_pct = (pnl / pos['cost']) * 100
                
                logger.info(f"  SELL {sym}: {pos['shares']} shares @ {sell_price:,.0f} = {sell_value:,.0f} KRW (PnL: {pnl:+,.0f} / {pnl_pct:+.1f}%)")
                
                self.trade_history.append({
                    'date': date,
                    'symbol': sym,
                    'action': 'SELL',
                    'shares': pos['shares'],
                    'price': sell_price,
                    'value': sell_value,
                    'pnl': pnl
                })
                
                del self.positions[sym]
        
        # Open/adjust positions
        for sym, target in target_positions.items():
            current_shares = self.positions.get(sym, {}).get('shares', 0)
            target_shares = target['shares']
            
            if target_shares > current_shares:
                # Buy more
                buy_shares = target_shares - current_shares
                buy_value = buy_shares * target['price']
                
                if buy_value <= self.current_cash:
                    self.current_cash -= buy_value
                    
                    if sym in self.positions:
                        self.positions[sym]['shares'] += buy_shares
                        self.positions[sym]['cost'] += buy_value
                    else:
                        self.positions[sym] = {
                            'shares': buy_shares,
                            'cost': buy_value,
                            'entry_price': target['price']
                        }
                    
                    logger.info(f"  BUY {sym}: {buy_shares} shares @ {target['price']:,.0f} = {buy_value:,.0f} KRW")
                    
                    self.trade_history.append({
                        'date': date,
                        'symbol': sym,
                        'action': 'BUY',
                        'shares': buy_shares,
                        'price': target['price'],
                        'value': buy_value
                    })
        
        # Calculate current equity
        portfolio_value = sum([
            pos['shares'] * market_data['close'][sym].loc[date]
            for sym, pos in self.positions.items()
            if sym in market_data['close'].columns
        ])
        
        self.current_equity = self.current_cash + portfolio_value
        
        daily_return = ((self.current_equity / self.initial_capital) - 1) * 100
        
        logger.info(f"\n{'='*60}")
        logger.info(f"End of Day Summary:")
        logger.info(f"  Cash: {self.current_cash:,.0f} KRW")
        logger.info(f"  Positions: {len(self.positions)} stocks, Value: {portfolio_value:,.0f} KRW")
        logger.info(f"  Total Equity: {self.current_equity:,.0f} KRW")
        logger.info(f"  Return: {daily_return:+.2f}%")
        logger.info(f"{'='*60}\n")
    
    def run(self, speed=1.0):
        """Run the simulation"""
        market_data, universe = self.load_market_data()
        
        if market_data is None or len(universe) == 0:
            logger.error("Failed to load market data")
            return
        
        # Get trading days
        trading_days = market_data['close'].index
        
        logger.info(f"\nStarting Paper Trading Replay")
        logger.info(f"Period: {trading_days[0].strftime('%Y-%m-%d')} to {trading_days[-1].strftime('%Y-%m-%d')}")
        logger.info(f"Trading Days: {len(trading_days)}")
        logger.info(f"Speed: {speed}x (Real-time simulation)")
        logger.info(f"\n{'='*60}\n")
        
        for date in trading_days:
            self.execute_day(date, market_data, universe)
            
            # Simulate real-time delay
            if speed > 0:
                time.sleep(1 / speed)  # Adjust speed (1.0 = 1 day per second)
        
        # Final summary
        total_return = ((self.current_equity / self.initial_capital) - 1) * 100
        
        logger.info(f"\n{'='*60}")
        logger.info(f"PAPER TRADING SIMULATION COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Start Date: {trading_days[0].strftime('%Y-%m-%d')}")
        logger.info(f"End Date: {trading_days[-1].strftime('%Y-%m-%d')}")
        logger.info(f"Trading Days: {len(trading_days)}")
        logger.info(f"Total Trades: {len(self.trade_history)}")
        logger.info(f"\nFinal Results:")
        logger.info(f"  Initial Capital: {self.initial_capital:,.0f} KRW")
        logger.info(f"  Final Equity: {self.current_equity:,.0f} KRW")
        logger.info(f"  Total Return: {total_return:+.2f}%")
        logger.info(f"{'='*60}\n")

if __name__ == "__main__":
    # Run 1-year replay
    engine = HistoricalReplayEngine(
        start_date="2024-12-01",
        end_date="2025-12-05",
        initial_capital=100_000_000
    )
    
    # Speed: 10 = 10 days per second, 1 = 1 day per second, 0 = instant
    engine.run(speed=2.0)
