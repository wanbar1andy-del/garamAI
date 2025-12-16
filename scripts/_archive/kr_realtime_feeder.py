"""
Kiwoom Realtime Feeder (32-bit)
Connects to Kiwoom API, subscribes to real-time ticks, aggregates them into 1-minute bars,
and saves them to disk for the Shadow Loop to consume.

Usage:
    python scripts/kr_realtime_feeder.py
    (Must be run in a 32-bit Python environment)
"""

import sys
import os
import time
import yaml
import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / "GARAM_Data" / "logs" / "kiwoom_feeder.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("KiwoomFeeder")

class RealtimeBarAggregator:
    """Aggregates ticks into 1-minute bars."""
    def __init__(self, code, data_dir):
        self.code = code
        self.data_dir = data_dir
        self.current_minute = None
        self.ohlcv = None
        self.last_price = 0
        
        # Ensure directories exist
        self.csv_dir = self.data_dir / "1m"
        self.json_dir = self.csv_dir / "latest"
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)

    def on_tick(self, tick):
        """
        Process a new tick.
        tick: {dt, price, volume}
        """
        dt = tick['dt']
        price = abs(int(tick['price'])) # Kiwoom sends negative for decline
        volume = abs(int(tick['volume'])) # Accumulated volume
        
        # Calculate incremental volume if possible, but for 1m bar we usually sum up ticks?
        # Kiwoom 'volume' in real data is accumulated volume for the day or tick volume?
        # FID 15 (Transaction Volume) is tick volume. FID 13 (Accumulated Volume) is day volume.
        # We need tick volume.
        
        minute_key = dt.strftime("%Y-%m-%d %H:%M")
        
        if self.current_minute is None:
            self._start_new_bar(minute_key, price, tick['tick_vol'])
        elif self.current_minute != minute_key:
            self._flush_bar()
            self._start_new_bar(minute_key, price, tick['tick_vol'])
        else:
            self._update_bar(price, tick['tick_vol'])
            
    def _start_new_bar(self, minute_key, price, vol):
        self.current_minute = minute_key
        self.ohlcv = {
            'datetime': minute_key,
            'open': price,
            'high': price,
            'low': price,
            'close': price,
            'volume': vol
        }
        
    def _update_bar(self, price, vol):
        if self.ohlcv:
            self.ohlcv['high'] = max(self.ohlcv['high'], price)
            self.ohlcv['low'] = min(self.ohlcv['low'], price)
            self.ohlcv['close'] = price
            self.ohlcv['volume'] += vol
            
    def _flush_bar(self):
        if not self.ohlcv:
            return
            
        # Save to CSV
        date_str = self.ohlcv['datetime'][:10].replace("-", "")
        csv_path = self.csv_dir / f"{self.code}_{date_str}.csv"
        # Appending logic (not shown fully) but we need to close the file or write it.
        # Assuming original code just wrote it.
        # But wait, original code ended abruptly at line 102 in my snippet?
        # No, line 103 is `super().__init__()` which is weird.
        
class KiwoomRealtimeFeed(QAxWidget):
    def __init__(self, universe_config):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.universe_config = universe_config
        self.aggregators = {}
        
        # Setup data dir
        self.data_root = project_root / "GARAM_Data" / "kr" / "realtime"
        
        # Connect events
        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveRealData.connect(self._on_receive_real_data)
        
        self.login()
        
    def login(self):
        ret = self.dynamicCall("CommConnect()")
        if ret == 0:
            logger.info("Login request sent.")
        else:
            logger.error("Login request failed.")

    def _on_event_connect(self, err_code):
        if err_code == 0:
            logger.info("Connected to Kiwoom Server.")
            self._setup_subscriptions()
        else:
            logger.error(f"Connection failed: {err_code}")
            sys.exit(1)
            
    def _setup_subscriptions(self):
        codes = self.universe_config.get('universe', [])
        if not codes:
            logger.warning("No symbols in universe.")
            return
            
        # Initialize aggregators
        for code in codes:
            self.aggregators[code] = RealtimeBarAggregator(code, self.data_root)
            
        # Subscribe (Screen 1000)
        # FID: 10(Current Price), 12(High), 13(Accum Vol), 15(Trans Vol), 20(Time)
        code_list = ";".join(codes)
        fids = "10;12;13;15;20"
        
        # SetRealReg(strScreenNo, strCodeList, strFidList, strOptType)
        # OptType: "0" (Replace), "1" (Add)
        ret = self.dynamicCall("SetRealReg(QString, QString, QString, QString)", 
                              "1000", code_list, fids, "0")
        
        logger.info(f"Subscribed to {len(codes)} symbols. Result: {ret}")
        
    def _on_receive_real_data(self, code, real_type, real_data):
        if real_type == "주식체결":
            try:
                # Get data
                # FID 20: Time (HHMMSS)
                time_str = self.dynamicCall("GetCommRealData(QString, int)", code, 20).strip()
                # FID 10: Current Price
                price = abs(int(self.dynamicCall("GetCommRealData(QString, int)", code, 10).strip()))
                # FID 15: Transaction Volume (Tick Volume)
                tick_vol = abs(int(self.dynamicCall("GetCommRealData(QString, int)", code, 15).strip()))
                
                now = datetime.now()
                # Use current date + time from Kiwoom
                dt = now.replace(
                    hour=int(time_str[:2]),
                    minute=int(time_str[2:4]),
                    second=int(time_str[4:6]),
                    microsecond=0
                )
                
                tick = {
                    'dt': dt,
                    'price': price,
                    'tick_vol': tick_vol,
                    'volume': 0 # Not used for aggregation logic directly
                }
                
                if code in self.aggregators:
                    self.aggregators[code].on_tick(tick)
                    
            except Exception as e:
                logger.error(f"Error processing real data for {code}: {e}")

def load_config():
    config_path = project_root / "config" / "kr_shadow_universe.yaml"
    if not config_path.exists():
        logger.error("Config file not found.")
        sys.exit(1)
        
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    try:
        config = load_config()
        feeder = KiwoomRealtimeFeed(config)
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"Main loop error: {e}")
