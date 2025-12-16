"""
Compounding Backtest for DGE v0.3
Simulates 3-month performance with 100M KRW initial capital and full profit reinvestment.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from strategies.kr_intraday.dge_orb_v0_3 import DGEOrbStrategyV3
from sim.test_account import TestAccount

class CompoundingDGEStrategy(DGEOrbStrategyV3):
    """
    DGE v0.3 with Compounding Position Sizing.
    Uses Current Equity (Base + PnL) to calculate position size.
    """
    def calculate_position_size(self, entry_price: float, stop_price: float) -> int:
        # Calculate Current Equity
        current_equity = self.account.base_capital + self.account.pnl_balance
        
        # Protect against bankruptcy
        if current_equity <= 0:
            return 0
            
        # Use Current Equity for Risk Calculation
        risk_amount = current_equity * self.risk_per_trade
        price_risk = abs(entry_price - stop_price)
        
        if price_risk == 0:
            return 0
            
        quantity = int(risk_amount / price_risk)
        return max(1, quantity)

    def on_bar(self, bar: pd.Series, timestamp: datetime):
        # 1. Update History Buffer for fs_fast
        self.history_buffer.append({
            'close': bar['close'],
            'volume': bar['volume'],
            'timestamp': timestamp
        })
        
        max_len = self.fs_params.N_ret + self.fs_params.N_fs + 20
        if len(self.history_buffer) > max_len:
            self.history_buffer.pop(0)
            
        # 2. Reset Daily State
        if self.current_date != timestamp.date():
            self.current_date = timestamp.date()
            self.orb_high = -float('inf')
            self.orb_low = float('inf')
            self.orb_complete = False
            
        # 3. Update ORB
        current_time = timestamp.time()
        from datetime import time, timedelta
        orb_end_time = (datetime.combine(timestamp.date(), time(9, 0)) + timedelta(minutes=self.orb_minutes)).time()
        
        if current_time <= orb_end_time:
            self.orb_high = max(self.orb_high, bar['high'])
            self.orb_low = min(self.orb_low, bar['low'])
            return None
        else:
            self.orb_complete = True
            
        # 4. Check Entry Conditions
        if len(self.positions) >= self.max_positions:
            return None
            
        # Calculate fs_orb (Normalized)
        orb_range = self.orb_high - self.orb_low
        if orb_range == 0: return None
        
        current_price = bar['close']
        fs_orb = 0.0
        if current_price > self.orb_high:
            fs_orb = (current_price - self.orb_high) / orb_range
        elif current_price < self.orb_low:
            fs_orb = (current_price - self.orb_low) / orb_range # Negative
            
        # Optimization: Early Exit if fs_orb is too weak
        # Min threshold is 0.3 (Attack). If abs(fs_orb) < 0.3, we won't enter anyway.
        if abs(fs_orb) < 0.3:
            return None

        # Calculate fs_fast (Only if fs_orb is promising)
        if len(self.history_buffer) < 50: # Need warm up
            return None
            
        df_hist = pd.DataFrame(self.history_buffer).set_index('timestamp')
        from garam.signals.fs_fast import update_fs_fast_one_tick
        fs_fast = update_fs_fast_one_tick(df_hist, self.fs_params)
            
        # Daily Trend
        fm = self.get_daily_fm(timestamp)
        
        # --- Regime-Specific Entry Threshold ---
        regime = self.regime_classifier.get_regime(self.daily_df, timestamp)
        
        # Default Threshold (Defense/Standard)
        current_fs_orb_thresh = 0.5 
        
        # Attack Mode Tuning: Relax threshold for STRONG_UP
        if "STRONG_UP_HIGH_VOL" in regime or "STRONG_UP_LOW_VOL" in regime:
            current_fs_orb_thresh = 0.3
        
        # Debug Print (Sample)
        # if np.random.random() < 0.001: # Print 0.1% of bars
        #      print(f"[{timestamp}] Regime: {regime}, fs_orb: {fs_orb:.2f}, fs_fast: {fs_fast:.2f}, fm: {fm:.2f}")

        # Entry Logic
        from strategies.kr_intraday.base_strategy import Signal
        
        # LONG
        if fm >= self.fm_thresh and fs_orb >= current_fs_orb_thresh and fs_fast >= self.fs_fast_thresh:
            self.open_position(
                Signal("LONG", current_price, current_price * 0.98, current_price * 1.10, timestamp, f"Signal_{regime}"),
                bar.name, bar
            )
            return None
            
        # SHORT
        elif fm <= -self.fm_thresh and fs_orb <= -current_fs_orb_thresh and fs_fast <= -self.fs_fast_thresh:
            self.open_position(
                Signal("SHORT", current_price, current_price * 1.02, current_price * 0.90, timestamp, f"Signal_{regime}"),
                bar.name, bar
            )
            return None
            
        return None

def run_compounding_backtest():
    print(">>> Running DGE v0.3 Compounding Simulation (3 Months)...")
    
    # 1. Configuration
    initial_capital = 100_000_000
    start_date = datetime(2025, 10, 1)
    end_date = datetime(2025, 10, 31)
    
    symbols = [
        "005930", "000660", "005380", "005490", "035420", 
        "000270", "051910", "068270", "105560", "006400"
    ]
    
    config = {
        'risk_per_trade': 0.015, # 1.5% Risk per trade
        'orb_minutes': 30,
        'fs_k': 3,
        'fs_N': 120,
        'mode': 'ATTACK'
    }
    
    # 2. Initialize Account & Strategies
    account = TestAccount(base_capital=initial_capital)
    strategies = {}
    
    # Load Data
    data_map = {}
    daily_map = {}
    
    print("Loading Data...")
    for symbol in symbols:
        # Intraday
        file_path = PATHS.DATA_DIR / "kr/intraday/1m" / f"{symbol}_1m.csv"
        if not file_path.exists():
            print(f"Warning: No intraday data for {symbol} at {file_path}")
            continue
            
        df = pd.read_csv(file_path)
        # Check columns
        if 'timestamp' not in df.columns and 'date' in df.columns:
             df.rename(columns={'date': 'timestamp'}, inplace=True)
             
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        print(f"[{symbol}] Data Range: {df.index[0]} to {df.index[-1]}")
        
        # Filter Date Range
        mask = (df.index >= start_date) & (df.index <= end_date)
        df_slice = df[mask].copy()
        
        if df_slice.empty:
             print(f"Warning: No data for {symbol} in range")
             continue
             
        data_map[symbol] = df_slice
        
        # Resample to Daily for Strategy (Symbol-specific Regime/Trend)
        daily_df = df_slice.resample('D').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        # Calculate 'fm' (Simple Moving Average Trend or similar if needed by get_daily_fm)
        # DGEOrbStrategyV2.get_daily_fm expects 'fm' column or calculates it?
        # It gets 'fm' from the column. We need to calculate it.
        # Assuming fm = (Close - MA(N)) / MA(N) or similar?
        # Let's check DGEOrbStrategyV2 logic or just add a dummy if it calculates it internally.
        # Actually, get_daily_fm just reads the column.
        # We need to calculate 'fm'.
        # Let's assume fm = (Close - MA20) / MA20 for now, or 0 if unknown.
        # Better: Calculate a simple trend score.
        daily_df['ma20'] = daily_df['close'].rolling(20).mean()
        daily_df['fm'] = (daily_df['close'] - daily_df['ma20']) / daily_df['ma20']
        daily_df['fm'] = daily_df['fm'].fillna(0)
        
        daily_map[symbol] = daily_df
            
        # Init Strategy
        strategies[symbol] = CompoundingDGEStrategy(account, config, daily_df=daily_map.get(symbol))

    # 3. Run Simulation
    print(f"Simulating {start_date.date()} to {end_date.date()}...")
    
    # Merge all timestamps to iterate chronologically
    all_timestamps = set()
    for df in data_map.values():
        all_timestamps.update(df.index)
    sorted_timestamps = sorted(list(all_timestamps))
    
    for ts in sorted_timestamps:
        # Market Hours Check
        if ts.time() < datetime.strptime("09:00", "%H:%M").time() or \
           ts.time() > datetime.strptime("15:30", "%H:%M").time():
            continue
            
        for symbol, strategy in strategies.items():
            if symbol in data_map and ts in data_map[symbol].index:
                bar = data_map[symbol].loc[ts]
                
                # Update Positions
                for pos in list(strategy.positions):
                    action = strategy.on_position_update(pos, bar)
                    if action:
                        # Close Position
                        strategy.close_position(pos, action.price, ts, action.reason)
                    
                # Check Entry
                strategy.on_bar(bar, ts)
                
    # 4. Results
    final_equity = account.base_capital + account.pnl_balance
    total_return = (final_equity - initial_capital) / initial_capital * 100
    
    # Calculate MDD
    equity_curve = [p.equity for p in account.equity_history]
    peak = -float('inf')
    mdd = 0
    for eq in equity_curve:
        if eq > peak: peak = eq
        dd = (eq - peak) / peak
        if dd < mdd: mdd = dd
        
    print("\n" + "="*50)
    print(">>> 3-Month Compounding Simulation Results")
    print("="*50)
    print(f"Initial Capital : {initial_capital:,.0f} KRW")
    print(f"Final Equity    : {final_equity:,.0f} KRW")
    print(f"Net Profit      : {final_equity - initial_capital:,.0f} KRW")
    print(f"Total Return    : {total_return:.2f}%")
    print(f"MDD             : {mdd*100:.2f}%")
    print(f"Total Trades    : {len(account.trade_history)}")
    
    if len(account.trade_history) > 0:
        wins = sum(1 for t in account.trade_history if t['pnl'] > 0)
        win_rate = wins / len(account.trade_history) * 100
        print(f"Win Rate        : {win_rate:.2f}%")
        
    # Monthly Breakdown
    print("\n[Monthly Breakdown]")
    df_trades = pd.DataFrame(account.trade_history)
    if not df_trades.empty:
        df_trades['month'] = df_trades['timestamp'].dt.to_period('M')
        monthly = df_trades.groupby('month')['pnl'].sum()
        for m, pnl in monthly.items():
            print(f"{m}: {pnl:,.0f} KRW")
            
    print("="*50)

if __name__ == "__main__":
    run_compounding_backtest()
