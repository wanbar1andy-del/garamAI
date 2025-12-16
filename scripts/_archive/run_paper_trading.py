"""
Paper Trading Runner for DGE v0.3
- Connects to Kiwoom Data Server (localhost:5555)
- Polls for 1-minute bars
- Runs DGE v0.3 Strategy per symbol
- Executes via PaperBroker
"""

import sys
import time
import logging
import pandas as pd
import urllib.request
import urllib.error
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS, ExecutionMode
from broker.paper_broker import PaperBroker
from strategies.kr_intraday.dge_orb_v0_3 import DGEOrbStrategyV3
from sim.test_account import TestAccount

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(PATHS.PAPER_LOGS / f"paper_runner_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PaperRunner")

# ...

class KiwoomPoller:
    """Polls Kiwoom Data Server for latest bars"""
    def __init__(self, server_url="http://localhost:5555"):
        self.server_url = server_url
        
    def get_latest_bar(self, symbol: str) -> pd.Series:
        """Fetch latest 1-min bar. Returns Series or None."""
        try:
            # We fetch last 5 bars to ensure we get the latest completed one
            url = f"{self.server_url}/fetch?code={symbol}&tick=1" 
            
            try:
                with urllib.request.urlopen(url, timeout=2) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode())
                        if data.get('status') == 'success':
                            bars = json.loads(data['data'])
                            if not bars: return None
                            
                            # Convert to DataFrame
                            df = pd.DataFrame(bars)
                            # Map columns
                            col_map = {"체결시간": "date", "시가": "open", "고가": "high", "저가": "low", "현재가": "close", "거래량": "volume"}
                            df.rename(columns=col_map, inplace=True)
                            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S')
                            df.sort_values('date', inplace=True)
                            
                            last_bar = df.iloc[-1]
                            # Ensure numeric
                            for c in ['open', 'high', 'low', 'close', 'volume']:
                                last_bar[c] = float(last_bar[c])
                                
                            return last_bar
            except (urllib.error.URLError, ConnectionResetError):
                pass
                
            return None
            
        except Exception as e:
            logger.error(f"Poll error for {symbol}: {e}")
            return None

    def get_daily_data(self, symbol: str) -> pd.DataFrame:
        """Fetch daily data for regime classification"""
        # Similar to get_latest_bar but tick='day' or similar
        # For now, load from local history if available
        files = list(PATHS.HISTORY_DIR.glob(f"KR_{symbol}_*_daily_20y.csv"))
        if files:
            df = pd.read_csv(files[0])
            # Process...
            df.columns = [c.lower() for c in df.columns]
            date_col = next((c for c in df.columns if c in ['date', 'timestamp', '일자']), None)
            df['timestamp'] = pd.to_datetime(df[date_col])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Calculate TR/ATR if needed (Strategy does it? No, Strategy expects pre-calc or calcs it)
            # DGEOrbStrategyV2._calc_daily_metrics() does it.
            return df
        return pd.DataFrame()

class PaperTradingRunner:
    def __init__(self):
        self.symbols = [
            "005930", "000660", "005380", "005490", "035420", 
            "000270", "051910", "068270", "105560", "006400"
        ]
        self.broker = PaperBroker(initial_balance=100_000_000, log_dir=PATHS.PAPER_LOGS)
        self.poller = KiwoomPoller()
        self.strategies: Dict[str, DGEOrbStrategyV3] = {}
        self.last_processed_time: Dict[str, datetime] = {}
        
        self.is_running = False
        
    def setup(self):
        logger.info("Setting up strategies...")
        
        base_config = {
            'initial_capital': 100_000_000, # Not used by strategy logic directly for sizing if using broker balance?
            # Strategy calculates size based on account.base_capital. 
            # We should sync this or let strategy use its own sizing logic.
            'risk_per_trade': 0.015,
            'orb_minutes': 30,
            'fs_k': 3,
            'fs_N': 120,
            'mode': 'ATTACK'
        }
        
        for symbol in self.symbols:
            # 1. Load Daily Data
            daily_df = self.poller.get_daily_data(symbol)
            if daily_df.empty:
                logger.warning(f"No daily data for {symbol}. Skipping.")
                continue
                
            # 2. Init Strategy
            # Pass dummy account, but IMPORTANT: pass BROKER
            account = TestAccount(100_000_000) 
            strategy = DGEOrbStrategyV3(account, base_config, daily_df=daily_df)
            strategy.broker = self.broker # Inject Broker
            
            self.strategies[symbol] = strategy
            self.last_processed_time[symbol] = datetime.min
            
        logger.info(f"Initialized {len(self.strategies)} strategies.")

    def run(self):
        self.is_running = True
        logger.info(">>> Starting Paper Trading Loop...")
        
        try:
            while self.is_running:
                now = datetime.now()
                
                # Market Hours Check (09:00 ~ 15:30)
                if now.hour < 9 or (now.hour == 15 and now.minute > 30) or now.hour > 15:
                    # Outside market hours
                    # logger.info("Outside market hours. Sleeping...")
                    # time.sleep(60)
                    # For testing, we might want to run anyway or use mock data.
                    # But strictly, we should wait.
                    pass
                
                for symbol, strategy in self.strategies.items():
                    # 1. Poll Data
                    bar = self.poller.get_latest_bar(symbol)
                    
                    # If no server, generate MOCK bar for testing infrastructure
                    if bar is None:
                        # Mock Bar
                        bar = pd.Series({
                            'open': 70000, 'high': 70500, 'low': 69500, 'close': 70200, 'volume': 1000,
                            'date': now
                        })
                        bar.name = now # Timestamp as name
                    
                    # 2. Check if new bar
                    # In real poll, we check timestamp > last_processed
                    # For mock, we just run every loop (throttle needed)
                    
                    if bar.name > self.last_processed_time[symbol]:
                        logger.info(f"Processing {symbol} at {bar.name}")
                        
                        # 3. Update Positions (Exit Check)
                        # Strategy.positions contains open positions.
                        # We need to call on_position_update for each.
                        # Copy list to avoid modification during iteration
                        for pos in list(strategy.positions):
                            strategy.on_position_update(pos, bar)
                            
                        # 4. Process Bar (Entry Check)
                        strategy.on_bar(bar, bar.name)
                        
                        self.last_processed_time[symbol] = bar.name
                        
                time.sleep(5) # Poll interval
                
        except KeyboardInterrupt:
            logger.info("Stopping...")
        except Exception as e:
            logger.error(f"Runtime Error: {e}", exc_info=True)
        finally:
            logger.info("Paper Trading Stopped.")

if __name__ == "__main__":
    runner = PaperTradingRunner()
    runner.setup()
    runner.run()
