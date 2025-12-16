"""
fs_orb Tuning Sweep
Runs 4 scenarios to optimize fs_orb threshold in STRONG_UP regime.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from strategies.kr_intraday.dge_orb_v0_3 import DGEOrbStrategyV3
from strategies.kr_intraday.backtest_runner import IntradayBacktestRunner
from sim.test_account import TestAccount
from strategies.kr_intraday.base_strategy import Signal

class DGEOrbStrategyV3_Tuning(DGEOrbStrategyV3):
    """
    Subclass to override open_position logic for fs_orb tuning.
    We need to intercept the signal generation logic, which is in on_bar (v2) or open_position (v3)?
    v3 inherits on_bar from v2. v2 has hardcoded fs_orb check.
    We need to override on_bar to implement dynamic fs_orb check.
    """
    def __init__(self, account, config, daily_df=None):
        super().__init__(account, config, daily_df)
        self.tuning_mode = config.get('tuning_mode', 'base') # base, 0.3, 0.2, dynamic
        
    def on_bar(self, bar: pd.Series, timestamp: datetime):
        # We must replicate v2.on_bar but with dynamic threshold logic.
        # This is unavoidable unless we refactor v2.
        
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
        from datetime import time, timedelta
        orb_end_time = (datetime.combine(timestamp.date(), time(9, 0)) + timedelta(minutes=self.orb_minutes)).time()
        
        if current_time <= orb_end_time:
            self.orb_high = max(self.orb_high, bar['high'])
            self.orb_low = min(self.orb_low, bar['low'])
            return None
        else:
            self.orb_complete = True
            
        # 4. Check Entry
        if len(self.positions) >= self.max_positions: return None
        if len(self.history_buffer) < 50: return None
            
        df_hist = pd.DataFrame(self.history_buffer).set_index('timestamp')
        from garam.signals.fs_fast import update_fs_fast_one_tick
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
        
        # --- Dynamic Threshold Logic ---
        regime = self.regime_classifier.get_regime(self.daily_df, timestamp)
        
        # Default Threshold
        current_thresh = self.fs_orb_thresh # 0.5
        
        if "STRONG_UP" in regime:
            if self.tuning_mode == '0.3':
                current_thresh = 0.3
            elif self.tuning_mode == '0.2':
                current_thresh = 0.2
            elif self.tuning_mode == 'dynamic':
                if fs_fast >= 2.0: current_thresh = 0.2
                elif fs_fast >= 1.0: current_thresh = 0.3
                else: current_thresh = 0.5
                
        # Entry Logic
        if fm >= self.fm_thresh and fs_orb >= current_thresh and fs_fast >= self.fs_fast_thresh:
            self.open_position(
                Signal("LONG", current_price, current_price * 0.98, current_price * 1.10, timestamp, f"Signal_{regime}"),
                bar.name, bar
            )
            return None
            
        elif fm <= -self.fm_thresh and fs_orb <= -current_thresh and fs_fast <= -self.fs_fast_thresh:
            self.open_position(
                Signal("SHORT", current_price, current_price * 1.02, current_price * 0.90, timestamp, f"Signal_{regime}"),
                bar.name, bar
            )
            return None
            
        return None

def run_sweep():
    print(">>> Running fs_orb Tuning Sweep...")
    
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

    scenarios = ['base', '0.3', '0.2', 'dynamic']
    results = []
    
    for sc in scenarios:
        print(f"\nRunning Scenario: {sc}")
        
        base_config = {
            'initial_capital': 100_000_000,
            'risk_per_trade': 0.015,
            'orb_minutes': 30,
            'fs_k': 3,
            'fs_N': 120,
            'start_date': '2025-09-01',
            'end_date': '2025-11-30',
            'mode': 'ATTACK',
            'tuning_mode': sc
        }
        
        total_pnl = 0
        total_trades = 0
        wins = 0
        su_pnl = 0
        su_trades = 0
        
        for symbol in universe:
            if symbol not in daily_data: continue
            
            account = TestAccount(base_config['initial_capital'])
            strategy = DGEOrbStrategyV3_Tuning(account, base_config, daily_df=daily_data[symbol])
            runner = IntradayBacktestRunner(strategy, symbol)
            res = runner.run(start_date=base_config['start_date'], end_date=base_config['end_date'])
            
            if 'metrics' in res:
                m = res['metrics']
                total_pnl += m.get('total_pnl', 0)
                total_trades += m.get('num_trades', 0)
                
                # Analyze Trades for STRONG_UP
                for t in account.trade_history:
                    if t['pnl'] > 0: wins += 1
                    
                    # Re-check regime (since we didn't store it in trade history by default in v3 base, 
                    # but v3_tuning inherits v3 which stores params in position_params but not trade history)
                    # We can use the 'entry_reason' if we appended it?
                    # v3.open_position doesn't append to entry_reason in base implementation?
                    # Wait, I modified v3.open_position to log regime?
                    # "new_pos.entry_reason += f" [{signal['regime']}]"" -> This was in the diff I applied?
                    # No, I commented it out or put 'pass'.
                    # So I need to recalculate regime here.
                    
                    regime = strategy.regime_classifier.get_regime(strategy.daily_df, t['entry_time'])
                    if "STRONG_UP" in regime:
                        su_pnl += t['pnl']
                        su_trades += 1
                        
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        avg_pnl = (total_pnl / total_trades) if total_trades > 0 else 0
        
        print(f"  Total PnL: {total_pnl:,.0f}")
        print(f"  Trades: {total_trades}")
        print(f"  STRONG_UP PnL: {su_pnl:,.0f}")
        
        results.append({
            "Scenario": sc,
            "Total PnL": total_pnl,
            "Trades": total_trades,
            "Win Rate": win_rate,
            "Avg PnL": avg_pnl,
            "STRONG_UP PnL": su_pnl,
            "STRONG_UP Trades": su_trades
        })
        
    df_res = pd.DataFrame(results)
    print("\nSweep Results:")
    print(df_res.to_markdown(index=False))
    df_res.to_csv(PATHS.EXPERIMENTS_DIR / "analysis" / "fs_orb_sweep_results.csv", index=False)

if __name__ == "__main__":
    from datetime import datetime
    run_sweep()
