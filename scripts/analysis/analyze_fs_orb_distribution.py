"""
Analyze fs_orb Distribution by Regime
Goal: Quantify blocked signals in STRONG_UP regime.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from strategies.kr_intraday.dge_orb_v0_3 import DGEOrbStrategyV3
from strategies.kr_intraday.backtest_runner import IntradayBacktestRunner
from sim.test_account import TestAccount
from garam.signals.fs_fast import update_fs_fast_one_tick

class DistributionAnalyzer(DGEOrbStrategyV3):
    """
    Instrumented Strategy to collect fs_orb values.
    """
    def __init__(self, account, config, daily_df=None):
        super().__init__(account, config, daily_df)
        self.candidates = [] # List of dicts
        
    def on_bar(self, bar: pd.Series, timestamp: datetime):
        # 1. Update History
        self.history_buffer.append({
            'close': bar['close'],
            'volume': bar['volume'],
            'timestamp': timestamp
        })
        max_len = self.fs_params.N_ret + self.fs_params.N_fs + 20
        if len(self.history_buffer) > max_len:
            self.history_buffer.pop(0)
            
        # 2. Daily State
        if self.current_date != timestamp.date():
            self.current_date = timestamp.date()
            self.orb_high = -float('inf')
            self.orb_low = float('inf')
            self.orb_complete = False
            
        # 3. ORB Update
        current_time = timestamp.time()
        orb_end_time = (datetime.combine(timestamp.date(), time(9, 0)) + timedelta(minutes=self.orb_minutes)).time()
        
        if current_time <= orb_end_time:
            self.orb_high = max(self.orb_high, bar['high'])
            self.orb_low = min(self.orb_low, bar['low'])
            return None
        else:
            self.orb_complete = True
            
        # 4. Check Candidates
        if len(self.history_buffer) < 50: return None
            
        df_hist = pd.DataFrame(self.history_buffer).set_index('timestamp')
        fs_fast = update_fs_fast_one_tick(df_hist, self.fs_params)
        
        orb_range = self.orb_high - self.orb_low
        if orb_range == 0: return None
            
        current_price = bar['close']
        fs_orb = 0.0
        if current_price > self.orb_high:
            fs_orb = (current_price - self.orb_high) / orb_range
        elif current_price < self.orb_low:
            fs_orb = (current_price - self.orb_low) / orb_range
            
        fm = self.get_daily_fm(timestamp)
        regime = self.regime_classifier.get_regime(self.daily_df, timestamp)
        
        # Collect Data if fm condition is met (Trend Alignment)
        # We only care about signals that align with daily trend
        is_long_candidate = (fm >= self.fm_thresh)
        is_short_candidate = (fm <= -self.fm_thresh)
        
        if is_long_candidate or is_short_candidate:
            self.candidates.append({
                'timestamp': timestamp,
                'regime': regime,
                'fm': fm,
                'fs_orb': fs_orb,
                'fs_fast': fs_fast,
                'direction': 'LONG' if is_long_candidate else 'SHORT'
            })
            
        # We don't actually trade here, just collect data
        return None

def analyze_distribution():
    print(">>> Analyzing fs_orb Distribution...")
    
    universe = [
        "000270", "000660", "005380", "005490", "005930", 
        "006400", "035420", "051910", "068270", "105560"
    ]
    
    # Load Daily
    daily_data = {}
    for symbol in universe:
        files = list(PATHS.HISTORY_DIR.glob(f"KR_{symbol}_*_daily_20y.csv"))
        if files:
            df = pd.read_csv(files[0])
            df.columns = [c.lower() for c in df.columns]
            date_col = next((c for c in df.columns if c in ['date', 'timestamp', '일자']), None)
            df['timestamp'] = pd.to_datetime(df[date_col])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            df['tr'] = np.maximum(df['high'] - df['low'], 
                                  np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                             abs(df['low'] - df['close'].shift(1))))
            df['atr_20'] = df['tr'].rolling(20).mean()
            daily_data[symbol] = df

    base_config = {
        'initial_capital': 100_000_000,
        'risk_per_trade': 0.015,
        'orb_minutes': 30,
        'fs_k': 3,
        'fs_N': 120,
        'start_date': '2025-09-01',
        'end_date': '2025-11-30',
        'mode': 'ATTACK'
    }
    
    all_candidates = []
    
    for symbol in universe:
        if symbol not in daily_data: continue
        
        print(f"Scanning {symbol}...")
        account = TestAccount(base_config['initial_capital'])
        strategy = DistributionAnalyzer(account, base_config, daily_df=daily_data[symbol])
        runner = IntradayBacktestRunner(strategy, symbol)
        runner.run(start_date=base_config['start_date'], end_date=base_config['end_date'])
        
        for c in strategy.candidates:
            c['symbol'] = symbol
            all_candidates.append(c)
            
    df = pd.DataFrame(all_candidates)
    if df.empty:
        print("No candidates found.")
        return

    # Group Regimes
    def get_regime_group(r):
        if "STRONG_UP" in r: return "STRONG_UP"
        if "WEAK_UP" in r: return "WEAK_UP"
        if "FLAT" in r: return "FLAT"
        if "DOWN" in r: return "DOWN"
        return "OTHER"
        
    df['regime_group'] = df['regime'].apply(get_regime_group)
    
    # Analyze STRONG_UP
    su_df = df[df['regime_group'] == 'STRONG_UP']
    print(f"\nSTRONG_UP Candidates: {len(su_df)}")
    
    # Bins
    bins = [-np.inf, 0.0, 0.2, 0.3, 0.5, 0.7, 1.0, np.inf]
    labels = ['<0', '0-0.2', '0.2-0.3', '0.3-0.5', '0.5-0.7', '0.7-1.0', '>1.0']
    su_df['orb_bin'] = pd.cut(su_df['fs_orb'].abs(), bins=bins, labels=labels)
    
    print("\nfs_orb Distribution in STRONG_UP:")
    dist = su_df['orb_bin'].value_counts().sort_index()
    print(dist.to_markdown())
    
    # Potential Gain
    current_pass = su_df[su_df['fs_orb'].abs() >= 0.5]
    potential_03 = su_df[su_df['fs_orb'].abs() >= 0.3]
    potential_02 = su_df[su_df['fs_orb'].abs() >= 0.2]
    
    print(f"\nCurrent (>=0.5): {len(current_pass)}")
    print(f"Relaxed (>=0.3): {len(potential_03)} (+{len(potential_03)-len(current_pass)})")
    print(f"Relaxed (>=0.2): {len(potential_02)} (+{len(potential_02)-len(current_pass)})")
    
    df.to_csv(PATHS.EXPERIMENTS_DIR / "analysis" / "fs_orb_distribution.csv", index=False)

if __name__ == "__main__":
    analyze_distribution()
