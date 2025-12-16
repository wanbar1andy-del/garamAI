"""
Shadow Loop Runner
Executes the daily trading loop in SHADOW mode.
Simulates real-time operation, fetching data, running strategies, and generating signals.
"""

import time
import logging
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# Add project root parent to path to allow 'garam' package import
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS
from garam.live.shadow_trader import ShadowTrader
from garam.sim.portfolio_simulator import PortfolioSimulator
from garam.data.loaders.kr_realtime_loader import KRRealtimeBarLoader
import yaml
# from surfing_brain.surfing_brain_v1 import SurfingBrain # TODO: Integrate later

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PATHS.SHADOW_LOGS / f"shadow_loop_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ShadowLoop")

def check_safety():
    """Ensure we are in SHADOW mode"""
    try:
        with open(PATHS.TRADING_MODE_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            mode = config.get('trading_mode', 'UNKNOWN')
            
        if mode != 'SHADOW':
            logger.critical(f"SAFETY STOP: TRADING_MODE is {mode}, expected SHADOW.")
            raise RuntimeError(f"Cannot run Shadow Loop in {mode} mode.")
            
        logger.info("Safety Check Passed: Mode is SHADOW")
        
    except FileNotFoundError:
        logger.warning("Trading mode file not found, defaulting to safe/error state.")
        raise
"""
Shadow Loop Runner
Executes the daily trading loop in SHADOW mode.
Simulates real-time operation, fetching data, running strategies, and generating signals.
"""

import time
import logging
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# Add project root parent to path to allow 'garam' package import
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS
from garam.live.shadow_trader import ShadowTrader
from garam.sim.portfolio_simulator import PortfolioSimulator
from garam.data.loaders.kr_realtime_loader import KRRealtimeBarLoader
import yaml
# from surfing_brain.surfing_brain_v1 import SurfingBrain # TODO: Integrate later

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PATHS.SHADOW_LOGS / f"shadow_loop_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ShadowLoop")

import pandas as pd

def check_safety(mode: str):
    """Ensure we are in SHADOW mode (unless Replay)"""
    if mode == 'replay':
        logger.info("Mode is REPLAY. Skipping safety check.")
        return

    try:
        with open(PATHS.TRADING_MODE_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            current_mode = config.get('trading_mode', 'UNKNOWN')
            
        if current_mode not in ['SHADOW', 'LIVE_PAPER']:
            logger.critical(f"SAFETY STOP: TRADING_MODE is {current_mode}, expected SHADOW or LIVE_PAPER.")
            raise RuntimeError(f"Cannot run Shadow Loop in {current_mode} mode.")
            
        logger.info(f"Safety Check Passed: Mode is {current_mode}")
        
    except FileNotFoundError:
        logger.warning("Trading mode file not found, defaulting to safe/error state.")
        raise

def run_replay_loop(date_str: str = None):
    """
    Replay Loop
    Feeds historical data to ShadowTrader.
    """
    logger.info("Starting Replay Loop...")
    
    # Use today if date not provided
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")
        
    target_symbol = '005930' # Samsung Electronics
    
    # Load Data
    data_path = PATHS.DATA_DIR / "kr" / "realtime" / "1m" / f"{target_symbol}_{date_str}.csv"
    if not data_path.exists():
        logger.error(f"No data found for {target_symbol} on {date_str} at {data_path}")
        return

    logger.info(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    # Initialize Trader in Manual Mode
    trader = ShadowTrader(symbol=target_symbol, feed_mode='manual')
    trader.start()
    
    # Replay
    count = 0
    for _, row in df.iterrows():
        # Construct tick from 1m bar (Approximation)
        # We treat the close of the bar as the tick for simplicity in replay
        tick = {
            'symbol': target_symbol,
            'timestamp': row['datetime'], # Assuming 'datetime' column
            'close': row['close'],
            'volume': row['volume'],
            'open': row['open'],
            'high': row['high'],
            'low': row['low']
        }
        
        trader.on_tick(tick)
        count += 1
        
        if count % 100 == 0:
            print(f"Replayed {count} bars...", end='\r')
            
    logger.info(f"Replay Complete. Processed {count} bars.")
    trader.stop()

def run_market_loop(dry_run: bool = False, mode: str = "SHADOW"):
    """
    Main Market Loop (09:00 - 15:30)
    """
    logger.info(f"Starting Market Loop in {mode} mode...")
    
    # Load Risk Config if LIVE_PAPER
    risk_config = {}
    if mode == "LIVE_PAPER":
        risk_path = PATHS.CONFIG_DIR / "risk_live_paper.yaml"
        if risk_path.exists():
            with open(risk_path, 'r', encoding='utf-8') as f:
                risk_config = yaml.safe_load(f)
            logger.info(f"Loaded risk config: {risk_config}")
    
    # Initialize Components
    # Load Universe
    universe_path = PATHS.CONFIG_DIR / "kr_shadow_universe.yaml"
    if universe_path.exists():
        with open(universe_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            target_symbols = [item['code'] for item in config.get('symbols', [])]
    else:
        target_symbols = ['005930'] # Default
        
    logger.info(f"Loaded {len(target_symbols)} symbols: {target_symbols}")
    
    # Initialize Traders
    traders = []
    for symbol in target_symbols:
        # For now, limit to 1 symbol to avoid API limits/complexity in this phase
        # unless we are in replay mode or have a robust multi-feed
        # if len(traders) >= 1 and not dry_run: 
        #      logger.warning("Limiting to 1 symbol for safety in initial Phase.")
        #      break
             
        # Feed Mode: 'mock' for dry-run/testing without Kiwoom, 'real' for actual connection
        # For LIVE_PAPER, we want real data.
        feed_mode = 'real' if mode == 'LIVE_PAPER' and not dry_run else 'mock'
        
        trader = ShadowTrader(
            symbol=symbol, 
            feed_mode=feed_mode,
            mode=mode,
            risk_config=risk_config
        )
        traders.append(trader)
        trader.start()
    
    try:
        while True:
            time.sleep(1)
            if dry_run:
                break
            # In a real loop, we might check for market close time
            now = datetime.now()
            if now.hour >= 15 and now.minute >= 35:
                logger.info("Market Closed. Stopping loop.")
                break
    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        for trader in traders:
            trader.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Shadow Loop")
    parser.add_argument("--dry-run", action="store_true", help="Run a single iteration and exit")
    parser.add_argument("--mode", type=str, default="shadow", choices=["shadow", "live_paper", "replay"], help="Operation mode")
    parser.add_argument("--date", type=str, help="Date for replay (YYYYMMDD)")
    
    args = parser.parse_args()
    
    # Set TRADING_MODE env var for other components
    import os
    os.environ["TRADING_MODE"] = args.mode.upper()
    
    try:
        check_safety(args.mode)
        
        if args.mode == 'replay':
            run_replay_loop(args.date)
        else:
            run_market_loop(dry_run=args.dry_run, mode=args.mode.upper())
            
    except Exception as e:
        logger.error(f"Shadow Loop Failed: {e}")
        sys.exit(1)
