"""
Live Trading Script for Policy v2 Phase 7 (Baseline)
SSOT Verification: SSOT_Phase7_Baseline.md
Commit: "Phase 7 Winner - Fixed -3% Entry, 1.5x Vol"

[Architecture]
1. DataAggregator: 1m ticks -> 5m Bars (ROC calculation).
2. StrategyEngine: Phase 7 Logic (MA60, ROC, Vol).
3. GuardrailEngine: Risk Control (-5% Cut, Cooldown).
4. OrderManager: Execution (Aggressive Limit/Market).
5. LiveLogger: Structured CSV Logging.
"""

# ... (Imports)
import sys
import time
import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
import json

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# Logger Setup
def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = setup_logger("LiveBot")

class LiveLogger:
    def __init__(self, log_dir):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.log_dir / f"trade_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(self.csv_path, "w", encoding='utf-8') as f:
            f.write("ts,symbol,signal,decision,reason,target_qty,sent_order,filled_qty,avg_fill,pnl,equity,guardrail_flags\n")

    def log(self, ts, symbol, signal, decision, reason, target_qty, sent, filled, avg_fill, pnl, equity, flags):
        line = f"{ts},{symbol},{signal},{decision},{reason},{target_qty},{sent},{filled},{avg_fill},{pnl},{equity},{flags}\n"
        with open(self.csv_path, "a", encoding='utf-8') as f:
            f.write(line)

class DataAggregator:
    """Aggregates 1-minute data into 5-minute bars for ROC calculation."""
    def __init__(self):
        self.bars = {} # {sym: DataFrame of 1m bars}
        
    def update_1m_bar(self, sym, bar_1m):
        """
        bar_1m: Series/Dict with 'close', 'volume', 'time'
        """
        if sym not in self.bars:
            self.bars[sym] = pd.DataFrame(columns=['close', 'volume'])
        
        df = self.bars[sym]
        ts = bar_1m['time']
        
        # Ensure timestamp index
        if not isinstance(ts, pd.Timestamp):
            ts = pd.Timestamp(ts)
            
        df.loc[ts] = {'close': bar_1m['close'], 'volume': bar_1m['volume']}
        df = df.sort_index() # Ensure sorted
        
        # Keep manageable size (last 60 mins)
        # We need historical lookups so don't truncate too aggressively
        if len(df) > 120:
            self.bars[sym] = df.iloc[-120:]
        else:
            self.bars[sym] = df

    def get_features(self, sym):
        if sym not in self.bars: return None
        df = self.bars[sym]
        if df.empty: return None
        
        curr_ts = df.index[-1]
        curr_close = df['close'].iloc[-1]
        curr_vol = df['volume'].iloc[-1]
        
        # 1. ROC 5m (Time-based)
        # Find price at (curr_ts - 5min). 
        # Logic: nearest backward (asof) or exact?
        # Sim Resample('1T').ffill() implies: if 09:09 exists, and 09:04 exists -> use 09:04
        # If 09:04 missing, use 09:03.
        target_ts = curr_ts - timedelta(minutes=5)
        
        # Use asof (find index <= target_ts)
        try:
            # get_loc with method='pad' finds nearest previous index
            # check if target_ts is within range headers
            if target_ts < df.index[0]:
                prev_close_5m = np.nan # Not enough history
            else:
                idx = df.index.get_indexer([target_ts], method='pad')[0]
                if idx != -1:
                    found_ts = df.index[idx]
                    # Tolerance Check (Risk B): If found_ts is too old (Gap > 1min), don't use it.
                    # target_ts is "5 mins ago". found_ts is "actual timestamp found".
                    # If target_ts = 09:05, found_ts = 09:04 -> Gap 1 min -> OK.
                    # If target_ts = 09:05, found_ts = 09:00 -> Gap 5 min -> FAIL.
                    if (target_ts - found_ts).total_seconds() > 60:
                        prev_close_5m = np.nan
                    else:
                         prev_close_5m = df['close'].iloc[idx]
                else:
                    prev_close_5m = np.nan
        except:
             prev_close_5m = np.nan

        if pd.isna(prev_close_5m) or prev_close_5m == 0: 
            return None # Cannot calc ROC
            
        roc_5m = (curr_close / prev_close_5m) - 1.0
        
        # 2. Vol Accel (Time-based Vol MA 10)
        # Mean of volume in [curr_ts - 9m, curr_ts] (10 min window)
        # Note: Sim `rolling(10)` on 1-min resampled array includes 0s for missing bars.
        # Live Raw DF does NOT have 0s.
        # So we must compute stricter: Sum of vol in window / 10. (Since Sim divides by 10)
        # "Vol MA 10" implies Average Volume per Minute over last 10 minutes.
        # If we have 3 bars in last 10 mins with vol 100, 200, 300. 
        # Sum=600. MA = 600 / 10 = 60. (Assuming empty bars have 0 vol).
        # THIS IS CRITICAL. Sim `resample` fills Volume with 0.
        
        start_ts = curr_ts - timedelta(minutes=9) # Window start (inclusive-ish)
        # Actually window is [t-9, t]. 10 minutes.
        
        # Filter rows in window
        window_df = df[start_ts:curr_ts] # Slice using DatetimeIndex
        
        vol_sum = window_df['volume'].sum()
        vol_ma = vol_sum / 10.0 # Time-based mean (assuming 0 for missing mins)
        
        if vol_ma == 0: vol_accel = 0.0
        else: vol_accel = curr_vol / vol_ma
        
        # 3. 30m Return (Score)
        target_ts_30 = curr_ts - timedelta(minutes=30)
        if target_ts_30 < df.index[0]:
            ret_30m = -999.0
        else:
             idx = df.index.get_indexer([target_ts_30], method='pad')[0]
             if idx != -1:
                 prev_close_30m = df['close'].iloc[idx]
                 ret_30m = (curr_close / prev_close_30m) - 1.0
             else:
                 ret_30m = -999.0

        return {'roc_5m': roc_5m, 'vol_accel': vol_accel, 'close': curr_close, 'ret_30m': ret_30m, 'vol_ma': vol_ma}

class OrderManager:
    def __init__(self, bot):
        self.bot = bot 
        self.mode = bot.mode

    def calculate_qty(self, price, alloc_amount):
        if price <= 0: return 0
        return int(alloc_amount / price)
        
    def send_order(self, ts, sym, side, qty, price=0, reason=""):
        if qty <= 0: return False
        
        logger.info(f"[Order] {ts} {side} {sym} Qty:{qty} Price:{price} ({reason})")
        
        if self.mode == 'PAPER' or self.mode == 'REPLAY':
            self.simulate_fill(ts, sym, side, qty, price, reason)
            return True
        return False

    def simulate_fill(self, ts, sym, side, qty, price=0, reason=""):
        fill_price = price
        if fill_price == 0:
            feat = self.bot.data_agg.get_features(sym)
            if feat: fill_price = feat['close']
        
        if fill_price == 0: 
            return # Cannot fill

        slippage = 0.0005 
        if side == 'BUY': exec_price = fill_price * (1 + slippage)
        else: exec_price = fill_price * (1 - slippage)

        self.bot.ledger.update(ts, sym, side, qty, exec_price, reason)
    
class TraceLogger:
    """Decision Trace Logger for Debugging Mismatches"""
    def __init__(self, log_dir):
        self.path = Path(log_dir) / f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(self.path, "w") as f:
            f.write("ts,sym,close,ma60,trend_ok,roc_5m,trigger_ok,vol,vol_ma,vol_accel,vol_ok,score,decision,reason\n")
            
    def log(self, ts, sym, close, ma60, trend_ok, roc, trig_ok, vol, vol_ma, vol_acc, vol_ok, score, dec, reason):
        with open(self.path, "a") as f:
            f.write(f"{ts},{sym},{close},{ma60},{trend_ok},{roc:.4f},{trig_ok},{vol},{vol_ma:.1f},{vol_acc:.2f},{vol_ok},{score:.4f},{dec},{reason}\n")
            f.flush()
            os.fsync(f.fileno())


class Ledger:
    def __init__(self, initial_capital, cost_rate=0.0015):
        self.cash = initial_capital
        self.positions = {} # {sym: {qty, avg_price}}
        self.cost_rate = cost_rate
        self.realized_pnl = 0.0
        self.trade_history = []
        self.equity_curve = [] # (ts, equity)

    def update(self, ts, sym, side, qty, price, reason):
        txn_amt = qty * price
        cost = txn_amt * self.cost_rate
        
        if side == 'BUY':
            self.cash -= (txn_amt + cost)
            if sym not in self.positions:
                self.positions[sym] = {'qty': 0, 'avg_price': 0.0}
            
            # Avg Price Update
            old_qty = self.positions[sym]['qty']
            old_cost = old_qty * self.positions[sym]['avg_price']
            new_qty = old_qty + qty
            new_avg = (old_cost + txn_amt) / new_qty
            
            self.positions[sym]['qty'] = new_qty
            self.positions[sym]['avg_price'] = new_avg
            
            pnl = 0.0
            
        elif side == 'SELL':
            self.cash += (txn_amt - cost)
            pos = self.positions.get(sym)
            if pos:
                buy_avg = pos['avg_price']
                pnl = (price - buy_avg) * qty - (cost + (buy_avg * qty * self.cost_rate)) 
                # Approx Net PnL: (Sell - Buy)*Qty - Costs
                # Actually: (SellAmt - SellCost) - (BuyAmt + BuyCost)
                # But BuyCost was paid at entry.
                # So PnL = (SellAmt - SellCost) - (BuyAvg * Qty)
                # Wait, Ledger cash tracks balance. PnL is descriptive.
                
                # Correct PnL for logging
                net_proceeds = txn_amt - cost
                cost_basis = buy_avg * qty
                trade_pnl = net_proceeds - cost_basis
                
                self.realized_pnl += trade_pnl
                
                rem_qty = pos['qty'] - qty
                if rem_qty <= 0:
                    del self.positions[sym]
                else:
                    self.positions[sym]['qty'] = rem_qty
            else:
                trade_pnl = 0.0 # Error?

        self.trade_history.append({
            'ts': ts, 'sym': sym, 'side': side, 'qty': qty, 'price': price, 
            'pnl': trade_pnl if side == 'SELL' else 0, 'reason': reason
        })

    def get_equity(self, current_prices):
        val = 0.0
        for sym, pos in self.positions.items():
            p = current_prices.get(sym, pos['avg_price']) # Fallback to cost if no price
            val += pos['qty'] * p
        return self.cash + val

class LiveTradingBot:
    def __init__(self, mode='PAPER', date_str=None):
        self.mode = mode
        self.initial_capital = 10_000_000.0 
        
        # SSOT Params
        self.max_slots = 3
        self.entry_roc = -0.030 
        self.entry_vol = 1.5 
        self.exit_sl = -0.020 
        self.exit_tp = 0.030 
        self.cost_rate = 0.0015 
        
        # Components
        self.ledger = Ledger(self.initial_capital, self.cost_rate)
        self.data_agg = DataAggregator()
        self.order_mgr = OrderManager(self)
        self.order_mgr = OrderManager(self)
        self.logger_csv = LiveLogger(project_root / "results" / "logs")
        self.trace = TraceLogger(project_root / "results" / "logs") # Enabled for Debug
        
        # State
        self.ma60_cache = {} 
        self.cooldown_map = {} 
        self.daily_loss_limit = -0.05
        self.consecutive_losses = 0
        self.start_of_day_equity = self.initial_capital 
        self.is_active = True
        self.eod_mode = False # Block new entries if True
        
        # Load Universe & MA60
        self.load_universe_and_ma60(date_str)

    def load_universe_and_ma60(self, date_str=None):
        logger.info("Loading Universe & Daily MA60...")
        univ_path = project_root / "GARAM_Data" / "real_universe_400.csv"
        df_univ = pd.read_csv(univ_path)
        symbols = df_univ['Code'].astype(str).str.zfill(6).tolist()
        self.universe_symbols = symbols
        
        # Load MA60 from market_status.csv if available
        status_path = project_root / "GARAM_Data" / "market_status.csv"
        if status_path.exists():
            try:
                df_status = pd.read_csv(status_path, dtype={'symbol': str})
                # Ensure columns: symbol, ma60
                # Map to cache
                for _, row in df_status.iterrows():
                    sym = str(row['symbol']).zfill(6)
                    self.ma60_cache[sym] = float(row['ma60'])
                logger.info(f"Loaded MA60 for {len(self.ma60_cache)} symbols.")
            except Exception as e:
                logger.error(f"Failed to load market_status.csv: {e}")
        else:
            logger.warning("market_status.csv NOT FOUND. MA60 checks will fail.")

    def on_tick(self, ts, sym, bar_data):
        self.data_agg.update_1m_bar(sym, {'time': ts, 'close': bar_data['close'], 'volume': bar_data['volume']})
        if not self.is_active: return
        
        # EOD Mode Logic:
        # 1. Always allow position management (Exit processing)
        # 2. Block NEW Entry Scanning if EOD Mode is active
        
        if sym in self.ledger.positions:
            self.manage_position(ts, sym)
        elif not self.eod_mode:
            # Only scan if NOT in EOD mode
            # Replay Mode: We process symbol by symbol, but to sort by score, 
            # we need to know if this tick completes a "batch" for the minute?
            # For Phase 8 Sim Parity: The Harness feeds ticks sorted by TS.
            # Sim Logic processes ALL symbols for TS, then sorts.
            # Here in Live loop, we get one tick.
            
            # Temporary Fix for Phase 8 Equality:
            # We assume Harness will call "flush_candidates(ts)" if needed?
            # Or we just Execute immediately if logic meets.
            # Sim Parity Failure 4): "Decision Trace" shows why we differ.
            # If we don't sort, we might pick different Entry order.
            # But let's first check if Conditions (MA60, ROC, Vol) match.
            # Direct execution with Trace Log.
            
            cand = self.scan_entry_candidate(ts, sym)
            if cand:
                # Immediate Execution for now (First Come First Serve)
                # Note: This might cause mismatch if Sim sorted.
                # But let's verify Logic Predicates first.
                self.execute_candidate(ts, cand)

    def scan_entry_candidate(self, ts, sym):
        # 0. Warm-up Check (09:05 Strict)
        # Checkpoint 2: No Entry before 09:05
        if ts.hour < 9 or (ts.hour == 9 and ts.minute < 5):
            return None

        # Cooldown Check
        if sym in self.cooldown_map:
            if (ts - self.cooldown_map[sym]).seconds < 3600:
                self.trace.log(ts, sym, 0, 0, False, 0, False, 0, 0, 0, False, 0, "SKIP", "COOLDOWN")
                return None

        feat = self.data_agg.get_features(sym)
        if not feat: 
            self.trace.log(ts, sym, 0, 0, False, 0, False, 0, 0, 0, False, 0, "SKIP", "FEAT_FAIL")
            return None
        
        close = feat['close']
        roc = feat['roc_5m']
        vol_accel = feat['vol_accel']
        vol_ma = feat['vol_ma']
        ret_30m = feat['ret_30m']
        
        ma60 = self.ma60_cache.get(sym, 0)
        
        # 1. MA60 Check (Strict)
        if ma60 == 0:
            self.trace.log(ts, sym, close, 0, False, roc, False, 0, vol_ma, vol_accel, False, ret_30m, "SKIP", "NO_MA60")
            return None
            
        trend_ok = close > ma60
        trigger_ok = roc <= self.entry_roc
        vol_ok = vol_accel >= self.entry_vol
        
        decision = "ENTRY" if (trend_ok and trigger_ok and vol_ok) else "SKIP"
        reason = []
        if not trend_ok: reason.append("TREND_FAIL")
        if not trigger_ok: reason.append("ROC_FAIL")
        if not vol_ok: reason.append("VOL_FAIL")
        reason_str = "+".join(reason) if reason else "Sniper"
        
        self.trace.log(ts, sym, close, ma60, trend_ok, roc, trigger_ok, 0, vol_ma, vol_accel, vol_ok, ret_30m, decision, reason_str)
        
        if decision == "ENTRY":
            return {'sym': sym, 'price': close, 'score': ret_30m}
        return None

    def execute_candidate(self, ts, cand):
        # Check Guardrails
        if "MaxLossStrike" in self.check_guardrails()[1]: return
        if len(self.ledger.positions) >= self.max_slots: return
        
        sym = cand['sym']
        if sym in self.ledger.positions: return
        
        alloc = self.initial_capital / self.max_slots
        close = cand['price']
        qty = self.order_mgr.calculate_qty(close, alloc)
        
        if qty > 0:
            if self.order_mgr.send_order(ts, sym, "BUY", qty, 0, "Sniper"):
                equity = self.get_current_equity()
                self.logger_csv.log(ts, sym, f"Score:{cand['score']:.4f}", "ENTRY", "Sniper", qty, "Y", qty, close, 0, equity, "")

    def manage_position(self, ts, sym):
        feat = self.data_agg.get_features(sym)
        if not feat: return
        
        curr_p = feat['close']
        pos = self.ledger.positions[sym]
        entry_p = pos['avg_price']
        pnl = (curr_p / entry_p) - 1.0
        
        action = None
        reason = ""
        
        ma60 = self.ma60_cache.get(sym, 0)
        if ma60 > 0 and curr_p < ma60:
            action = "SELL"
            reason = "TrendBreak"
        elif pnl < self.exit_sl:
            action = "SELL"
            reason = "SL"
        elif pnl > self.exit_tp:
            action = "SELL"
            reason = "TP"
            
        if action == "SELL":
            self.order_mgr.send_order(ts, sym, "SELL", pos['qty'], 0, reason)
            
            last_trade = self.ledger.trade_history[-1]
            if last_trade['pnl'] < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0
                
            self.cooldown_map[sym] = ts
            
            equity = self.get_current_equity()
            self.logger_csv.log(ts, sym, f"Pnl:{pnl:.2%}", "EXIT", reason, 0, "Y", pos['qty'], curr_p, last_trade['pnl'], equity, "")


    def get_current_equity(self):
        # Need current prices for all positions
        # Simpler: use last close in DataAggregator
        prices = {}
        for s in self.ledger.positions:
            f = self.data_agg.get_features(s)
            if f: prices[s] = f['close']
        return self.ledger.get_equity(prices)

    def check_guardrails(self):
        equity = self.get_current_equity()
        ret = (equity / self.start_of_day_equity) - 1.0
        
        flags = []
        if ret <= self.daily_loss_limit:
            if self.is_active:
                logger.critical(f"GUARDRAIL: Daily Loss Limit Hit ({ret*100:.2f}%). HALTING.")
                self.close_all(datetime.now(), "guard_loss_limit") # Using approx time
                self.is_active = False
            return False, "DailyLoss"
            
        if self.consecutive_losses >= 3:
            flags.append("MaxLossStrike")
            
        return True, ",".join(flags)

    def close_all(self, ts, reason):
        for sym in list(self.ledger.positions.keys()):
            qty = self.ledger.positions[sym]['qty']
            self.order_mgr.send_order(ts, sym, "SELL", qty, 0, reason)

    # Replay Harness Entry Point
    def run_replay(self, tick_feed):
        # tick_feed: iterator of (ts, sym, row) sorted by ts
        logger.info(f"Starting Replay... (Initial Equity: {self.start_of_day_equity})")
        
        for ts, sym, row in tick_feed:
            # EOD Check (15:20)
            if ts.hour == 15 and ts.minute == 20:
                self.close_all(ts, "EOD")
                # Continue consuming ticks? or Break?
                # Break usually.
                break
                
            # Guardrail
            ok, flags = self.check_guardrails()
            if not ok: break
            
            # Feed
            self.on_tick(ts, sym, row)
            
        # Final Report
        final_eq = self.get_current_equity()
        logger.info(f"Replay Finished. Final Equity: {final_eq:.0f} Return: {(final_eq/self.start_of_day_equity - 1)*100:.2f}%")
        
    def run_live(self):
        """
        Phase 9: Real-time File Watching Loop
        Watches GARAM_Data/realtime/*.csv for updates.
        """
        import time
        from glob import glob
        from datetime import datetime
        from pathlib import Path
        import pandas as pd # Assuming pandas is used for pd.to_datetime

        # --- Phase 9 Operational Loggers ---
        class HeartbeatLogger:
            def __init__(self, log_dir):
                self.path = Path(log_dir) / "engine_heartbeat.csv"
                if not self.path.exists():
                    with open(self.path, "w") as f:
                        f.write("ts,loop_count,files_seen,lines_processed,positions,equity\n")
            
            def beat(self, loop_count, files_seen, lines_processed, positions_count, equity):
                with open(self.path, "a") as f:
                    f.write(f"{datetime.now()},{loop_count},{files_seen},{lines_processed},{positions_count},{equity:.2f}\n")
                    f.flush()
        
        realtime_dir = project_root / "GARAM_Data" / "realtime"
        logger.info(f"Starting Live Engine (Phase 9 Paper Trading). Watching: {realtime_dir}")
        self.is_active = True
        
        # Track process state per symbol: {sym: last_processed_ts}
        processed_state = {}
        # Track file state: {sym: {mtime, offset}}
        file_cursors = {}
        
        # Operational Metrics (Restored)
        loop_count = 0
        total_lines_processed = 0
        last_heartbeat = datetime.now()
        
        hb_logger = HeartbeatLogger(project_root / "results" / "logs")
        crash_log_path = project_root / "results" / "logs" / "crash.log"

        # EOD State
        eod_processed = False
        
        try:
            while self.is_active:
                loop_count += 1
                now = datetime.now()
                files_seen_this_loop = 0
                
                # --- P0 Gate: Heartbeat (Every 10s) ---
                if (now - last_heartbeat).total_seconds() >= 10:
                    eq = self.get_current_equity()
                    hb_logger.beat(loop_count, len(file_cursors), total_lines_processed, len(self.ledger.positions), eq)
                    last_heartbeat = now
                    # Also log cursor progress for P2 (Debug Level)
                    # logger.debug(f"Cursors: {file_cursors}")

                # --- 1. E & S Checks ---
                if now.hour >= 15 and now.minute >= 30:
                    logger.info("Market Closed (15:30). Shutting down.")
                    break
                    
                # Robust EOD Trigger (Hotfix C)
                # Trigger once if time >= 15:20
                if now.hour == 15 and now.minute >= 20 and not eod_processed: 
                     if len(self.ledger.positions) > 0:
                         logger.warning("EOD Force Close Triggered (15:20) [Checkpoint 4 Passed]")
                         self.close_all(now, "EOD")
                     eod_processed = True
                     self.eod_mode = True
                     logger.info("EOD Mode Activated. No new entries.")
                
                # Prevent entry after 15:20
                if now.hour == 15 and now.minute >= 20:
                     # Just ensure we don't process new entries. 
                     # self.on_tick -> scan_entry_candidate -> already checks nothing? No.
                     # We should block scan_entry_candidate? 
                     # scan_entry_candidate checks time? Currently only warm-up.
                     pass # We rely on close_all clearing positions. But new entries?
                     # Let's add a check in on_tick or just trust loop speed?
                     # Better: if eod_processed, skip scanning.
                     pass 

                ok, flags = self.check_guardrails()
                if not ok: 
                    logger.critical(f"Guardrail Triggered: {flags}. Stopping.")
                    break

                # --- 2. File Scan ---
                # Only scan .csv (Atomic feeder uses .tmp -> .csv)
                files = list(realtime_dir.glob("*.csv"))
                files_seen_this_loop = len(files)
                
                if not files:
                     time.sleep(0.1)
                     continue
                     
                for p in files:
                    sym = p.stem
                    try:
                        current_size = p.stat().st_size
                        
                        # New file or grew?
                        if sym not in file_cursors:
                            file_cursors[sym] = 0 # Start from beginning
                        
                        # Handle File Rotation / Truncation (P2 Gate)
                        if current_size < file_cursors[sym]:
                            logger.warning(f"File {p.name} shrank/rotated (Size: {current_size} < Cursor: {file_cursors[sym]}). Resetting cursor.")
                            file_cursors[sym] = 0
                            
                        cursor = file_cursors[sym]
                        if current_size == cursor:
                             continue # No new data
                            
                        # Read new lines
                        new_lines = []
                        with open(p, "r") as f:
                            f.seek(cursor)
                            new_lines = f.readlines()
                            file_cursors[sym] = f.tell() # Update cursor
                        
                        if not new_lines: continue
                        
                        for line in new_lines:
                            line = line.strip()
                            if not line: continue
                            
                            parts = line.split(',')
                            if len(parts) < 6 or parts[0] == 'date': continue # Skip header
                            
                            ts_str = parts[0]
                            if len(ts_str) != 14: continue
                            
                            bar_ts = pd.to_datetime(ts_str, format="%Y%m%d%H%M%S")
                            
                            # Idempotency
                            if sym in processed_state and bar_ts <= processed_state[sym]:
                                continue
                            processed_state[sym] = bar_ts
                            total_lines_processed += 1
                            
                            # Data
                            tick_row = {
                                "time": bar_ts,
                                "close": float(parts[4]),
                                "volume": float(parts[5])
                            }
                            
                            # Process
                            self.on_tick(bar_ts, sym, tick_row)
                            
                    except Exception as e:
                        logger.error(f"Error reading {p.name}: {e}")
                
                time.sleep(0.1) # Fast polling for Seek Reader
                
        except Exception as e:
            # P3: Crash Logging
            import traceback
            err_msg = traceback.format_exc()
            logger.critical(f"ENGINE CRASHED: {e}")
            with open(crash_log_path, "a") as f:
                f.write(f"\n[{datetime.now()}] CRASH:\n{err_msg}\n")
            raise e

if __name__ == "__main__":
    # Standard Live Entry
    from datetime import datetime
    bot = LiveTradingBot()
    # bot.run_replay() # Debug only
    bot.run_live()
