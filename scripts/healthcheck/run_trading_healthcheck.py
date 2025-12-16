"""
Trading Logic Health Check & Anomaly Hunter
Goal: Identify "debris" code and "blocking conditions" that hinder performance.
"""

import sys
import os
import re
import glob
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from strategies.kr_intraday.dge_orb_v0_3 import DGEOrbStrategyV3
from strategies.kr_intraday.backtest_runner import IntradayBacktestRunner
from sim.test_account import TestAccount
from garam.signals.fs_fast import update_fs_fast_one_tick

# --- 1. Static Code Scan ---

def scan_static_debris():
    print(">>> Starting Static Code Scan...")
    
    keywords = [
        "TODO", "FIXME", "HACK", "TMP", "TEMP",
        "DEPRECATED", "LEGACY", "OLD", "TEST", "MOCK",
        "DISABLE_", "ENABLE_", "SAFE_MODE", "DRY_RUN", "PAPER", "SIM_ONLY",
        "MAX_TRADES", "LIMIT", "CAP", "BLOCK", "SKIP", "RETURN"
    ]
    
    # Files to scan (Strategies, Config, Sim, Scripts)
    scan_paths = [
        PATHS.BASE_DIR / "strategies",
        PATHS.BASE_DIR / "config.py",
        PATHS.BASE_DIR / "sim",
        PATHS.BASE_DIR / "scripts"
    ]
    
    findings = []
    
    for path in scan_paths:
        if path.is_file():
            files = [path]
        else:
            files = path.rglob("*.py")
            
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines):
                    for kw in keywords:
                        # Use regex for word boundary check
                        # Escape kw just in case
                        pattern = r'\b' + re.escape(kw) + r'\b'
                        if re.search(pattern, line) and not line.strip().startswith("#"):
                            
                            # Classify
                            category = "UNKNOWN"
                            if kw in ["TODO", "FIXME", "HACK"]: category = "DEBUG_STUB"
                            elif kw in ["DEPRECATED", "LEGACY", "OLD"]: category = "LEGACY"
                            elif kw in ["LIMIT", "CAP", "MAX_TRADES", "BLOCK"]: category = "RISK_LIMIT"
                            elif kw in ["SAFE_MODE", "DRY_RUN", "DISABLE_"]: category = "ENV_FLAG"
                            
                            findings.append({
                                "file": str(file_path.relative_to(PATHS.BASE_DIR)),
                                "line": i + 1,
                                "keyword": kw,
                                "category": category,
                                "content": line.strip()
                            })
            except Exception as e:
                print(f"Error scanning {file_path}: {e}")
                
    return pd.DataFrame(findings)

# --- 2. Dynamic Health Check (Instrumented Strategy) ---

class HealthCheckStrategy(DGEOrbStrategyV3):
    """
    Instrumented Strategy to log decision paths.
    Inherits from v0.3 but overrides logic to capture 'Why didn't we buy?'.
    """
    def __init__(self, account, config, daily_df=None):
        super().__init__(account, config, daily_df)
        self.blocked_logs = [] # List of dicts
        
    def on_bar(self, bar: pd.Series, timestamp: datetime):
        # Replicating v0.2/v0.3 logic with instrumentation
        
        # 1. Update History (Standard)
        self.history_buffer.append({
            'close': bar['close'],
            'volume': bar['volume'],
            'timestamp': timestamp
        })
        max_len = self.fs_params.N_ret + self.fs_params.N_fs + 20
        if len(self.history_buffer) > max_len:
            self.history_buffer.pop(0)
            
        # 2. Daily State (Standard)
        if self.current_date != timestamp.date():
            self.current_date = timestamp.date()
            self.orb_high = -float('inf')
            self.orb_low = float('inf')
            self.orb_complete = False
            
        # 3. ORB Update (Standard)
        current_time = timestamp.time()
        from datetime import time, timedelta
        orb_end_time = (datetime.combine(timestamp.date(), time(9, 0)) + timedelta(minutes=self.orb_minutes)).time()
        
        if current_time <= orb_end_time:
            self.orb_high = max(self.orb_high, bar['high'])
            self.orb_low = min(self.orb_low, bar['low'])
            # Log: Blocked by ORB Period (Optional: too verbose)
            # self.log_block(timestamp, "ORB_PERIOD", f"Time {current_time} <= {orb_end_time}")
            return None
        else:
            self.orb_complete = True
            
        # 4. Check Entry Conditions (Instrumented)
        
        # Blocker: Max Positions
        if len(self.positions) >= self.max_positions:
            self.log_block(timestamp, "MAX_POSITIONS", f"Positions {len(self.positions)} >= {self.max_positions}")
            return None
            
        # Blocker: Warmup
        if len(self.history_buffer) < 50:
            return None
            
        # Calc Indicators
        df_hist = pd.DataFrame(self.history_buffer).set_index('timestamp')
        fs_fast = update_fs_fast_one_tick(df_hist, self.fs_params)
        
        orb_range = self.orb_high - self.orb_low
        if orb_range == 0: 
            self.log_block(timestamp, "ORB_RANGE_ZERO", "High == Low")
            return None
            
        current_price = bar['close']
        fs_orb = 0.0
        if current_price > self.orb_high:
            fs_orb = (current_price - self.orb_high) / orb_range
        elif current_price < self.orb_low:
            fs_orb = (current_price - self.orb_low) / orb_range
            
        fm = self.get_daily_fm(timestamp)
        
        # Check Thresholds
        # LONG
        long_cond = (fm >= self.fm_thresh) and (fs_orb >= self.fs_orb_thresh) and (fs_fast >= self.fs_fast_thresh)
        # SHORT
        short_cond = (fm <= -self.fm_thresh) and (fs_orb <= -self.fs_orb_thresh) and (fs_fast <= -self.fs_fast_thresh)
        
        if long_cond:
            self.open_position_instrumented("LONG", bar, timestamp)
            return None
        elif short_cond:
            self.open_position_instrumented("SHORT", bar, timestamp)
            return None
        else:
            # Failed - Why?
            reasons = []
            if abs(fm) >= self.fm_thresh:
                # fm passed, what failed?
                if abs(fs_orb) < self.fs_orb_thresh: reasons.append(f"fs_orb({fs_orb:.2f}) < {self.fs_orb_thresh}")
                if abs(fs_fast) < self.fs_fast_thresh: reasons.append(f"fs_fast({fs_fast:.2f}) < {self.fs_fast_thresh}")
                
                if reasons:
                    self.log_block(timestamp, "SIGNAL_FILTER", ", ".join(reasons), 
                                   extra={'fm': fm, 'fs_orb': fs_orb, 'fs_fast': fs_fast})
            
            return None

    def log_block(self, timestamp, stage, reason, extra=None):
        self.blocked_logs.append({
            'timestamp': timestamp,
            'stage': stage,
            'reason': reason,
            'extra': extra
        })
        
    def open_position_instrumented(self, direction, bar, timestamp):
        from strategies.kr_intraday.base_strategy import Signal
        price = bar['close']
        sig = Signal(direction, price, price, price, timestamp, "Signal")
        self.open_position(sig, "SYMBOL", bar)

def run_dynamic_check():
    print(">>> Starting Dynamic Pipeline Check...")
    
    # Setup - Expand Universe to test Portfolio Limits
    universe = ["000660", "005930", "005380", "051910", "000270"] 
    
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
            
            # Calc ATR
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
        'start_date': '2025-10-01', 
        'end_date': '2025-10-31',
        'mode': 'ATTACK',
        'max_positions': 3 # Force limit
    }
    
    all_logs = []
    
    # We need to run them together to test portfolio limits?
    # IntradayBacktestRunner runs ONE symbol at a time.
    # To test portfolio limits, we need a PortfolioRunner or simulate them sequentially?
    # Sequential run won't trigger cross-symbol max_positions limit in the strategy instance 
    # unless they share the same strategy instance.
    # But IntradayBacktestRunner takes a strategy instance.
    # If we reuse the strategy instance across runners? 
    # No, runner loops through bars. We need to interleave bars.
    # The current infrastructure doesn't support multi-symbol intraday backtest easily without the PortfolioSimulator.
    # But PortfolioSimulator is for daily.
    
    # Workaround: Run individually and just check per-symbol limits.
    # OR: Just accept that we are testing logic per symbol.
    # The user wants to find "Hidden Constraints".
    # If I run individually, I can't test "Total Portfolio Cap".
    # But I can test "Max Positions" per strategy instance if I pretend it's a portfolio strategy?
    # No, let's stick to individual run for now to find signal blockers.
    # Portfolio limits are usually handled by the Trader/Broker in live, or PortfolioSimulator.
    
    for symbol in universe:
        if symbol not in daily_data: continue
        
        print(f"Scanning {symbol}...")
        account = TestAccount(base_config['initial_capital'])
        strategy = HealthCheckStrategy(account, base_config, daily_df=daily_data[symbol])
        runner = IntradayBacktestRunner(strategy, symbol)
        runner.run(start_date=base_config['start_date'], end_date=base_config['end_date'])
        
        for log in strategy.blocked_logs:
            log['symbol'] = symbol
            all_logs.append(log)
            
    return pd.DataFrame(all_logs)

# --- 3. Report Generation ---

def generate_report():
    static_df = scan_static_debris()
    dynamic_df = run_dynamic_check()
    
    report_path = PATHS.BASE_DIR / "docs" / "trading_logic_health_report.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Trading Logic Health & Anomaly Report\n\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        
        f.write("## 1. Static Code Analysis (Debris Hunting)\n")
        if not static_df.empty:
            f.write(f"Found {len(static_df)} items.\n\n")
            # Group by Category
            for cat, group in static_df.groupby('category'):
                f.write(f"### {cat}\n")
                f.write(group[['file', 'line', 'keyword', 'content']].to_markdown(index=False))
                f.write("\n\n")
        else:
            f.write("No debris found (Clean!).\n\n")
            
        f.write("## 2. Dynamic Pipeline Check (Blocking Conditions)\n")
        if not dynamic_df.empty:
            f.write(f"Total Blocked Events: {len(dynamic_df)}\n\n")
            
            # Summary by Stage
            f.write("### Blocks by Stage\n")
            stage_counts = dynamic_df['stage'].value_counts().reset_index()
            stage_counts.columns = ['Stage', 'Count']
            f.write(stage_counts.to_markdown(index=False))
            f.write("\n\n")
            
            # Sample Logs
            f.write("### Sample Blocked Logs (Top 20)\n")
            f.write(dynamic_df[['timestamp', 'symbol', 'stage', 'reason']].head(20).to_markdown(index=False))
            f.write("\n\n")
        else:
            f.write("No blocking events recorded (or no signals generated).\n\n")
            
    print(f"Report generated: {report_path}")

if __name__ == "__main__":
    generate_report()
