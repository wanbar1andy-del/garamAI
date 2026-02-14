
import os
import sys
import argparse
import datetime as dt
import time
import json
import logging
import traceback
import csv
import pandas as pd
import numpy as np

# Ensure path
sys.path.append(os.getcwd())

from pipeline.live.engine import BaseEngine
from pipeline.live.order_manager import OrderManager
from pipeline.live.realtime_feed import RealtimeProcessor
# Assuming ingest_kiwoom_realtime acts as Producer. This script acts as Consumer.

# --- Log Setup ---
log_dir = "logs/phase38"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, f"live_switching_{dt.date.today().strftime('%Y%m%d')}.log"),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)

class LiveSwitchingStrategy:
    """
    Phase 36 Conservative Switching Strategy (Live Version)
    - Bear Cap: 50%
    - Switching: Max 3/day, Threshold -1.5%
    - Daily Stop: -2.5%
    - Hero: PnL > 3% & Rank#1 (3 bars) -> 80% Conc
    """
    def __init__(self, config=None):
        self.config = config or {}
        
        # Params
        self.max_equity_alloc = 0.50 # Bear Cap (Conservative)
        self.max_switches = 3
        self.switch_thresh = -0.015
        self.daily_stop_loss = 0.025
        self.concentration_trigger = 0.03
        self.concentration_target = 0.80
        self.max_slots = 5
        
        # State
        self.positions = {} # {sym: {qty, avg_px}}
        self.cash = 1_000_000 # Default Micro Live Cap
        self.start_equity = 1_000_000
        self.switches_today = 0
        self.rank_history = []
        self.concentrated_set = set()
        self.last_ts = None
        self.is_halted = False

    def on_market_open(self, equity):
        self.start_equity = equity
        self.switches_today = 0
        self.is_halted = False
        self.rank_history = []
        self.concentrated_set = set()
        logging.info(f"[OPEN] Start Equity: {self.start_equity}")

    def on_tick(self, market_data, current_equity):
        """
        market_data: dict of {sym: {close, volume, high_roll, vol_ma}}
        """
        if self.is_halted: return []

        # 0. Daily Loss Check
        pnl_pct = (current_equity - self.start_equity) / self.start_equity
        if pnl_pct < -self.daily_stop_loss:
            logging.warning(f"[HALT] Daily Loss {pnl_pct:.2%} exceeds limit {-self.daily_stop_loss:.2%}")
            self.is_halted = True
            return self.close_all(market_data)

        # 1. Bear Regime Check (Simplified: Always Bear Mode for Safety initially)
        # Or use real regime filter? Paper used 50% cap as "Bear Mode".
        # We stick to Phase 36 Spec: 50% Cap IF Bear, 100% IF Bull.
        # Live proxies: Use simple daily trend of KOSDAQ/KOSPI? 
        # For safety in Phase 38, we default to 50% ALLOCATION CAP as per "Conservative" logic.
        allocation_cap = current_equity * self.max_equity_alloc
        
        # 2. Hero Candidates
        candidates = []
        for sym, feats in market_data.items():
            if feats['vol_ma'] == 0: continue
            if feats['volume'] > feats['vol_ma'] * 2.0 and feats['close'] >= feats['high_roll']:
                score = feats['volume'] / feats['vol_ma']
                candidates.append((sym, score))
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Rank History
        leader = candidates[0][0] if candidates else None
        self.rank_history.append(leader)
        if len(self.rank_history) > 3: self.rank_history.pop(0)

        orders = []
        current_exposure = current_equity - self.cash # Approx
        slot_size = allocation_cap / self.max_slots

        # 3. Position Management
        # Check Concentration
        # Check Stops (-1% Base Trail?)
        
        # 4. Entry logic (simplified for snippet)
        # This is a skeleton. Full logic needs OrderManager etc.
        
        return orders

    def close_all(self, market_data):
        orders = []
        for sym in self.positions:
            orders.append({"type": "SELL", "symbol": sym, "qty": self.positions[sym]['qty']})
        return orders

def run_live():
    print("Starting Phase 38 Live Switching Engine (Conservative)...")
    # Feed Connect...
    # Loop...
    pass

if __name__ == "__main__":
    run_live()
