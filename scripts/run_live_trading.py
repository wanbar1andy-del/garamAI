import argparse
import time
import yaml
import pandas as pd
import numpy as np
import os
from pathlib import Path
import sys

# [FIX] Ensure Project Root is in sys.path for module resolution
# This handles the case where the script is run directly from the scripts/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime, timedelta

from pipeline.live.live_resampler import LiveResampler
from pipeline.live.universe_loader import UniverseLoader
from pipeline.live.signal_a2 import SignalA2
from pipeline.live.order_mock import OrderMock
from pipeline.live.order_real import OrderReal # [NEW] Real Adapter
from pipeline.live.risk_manager import RiskManager
from pipeline.live.logger import LiveLogger
from pipeline.live.risk_manager import RiskManager

from pipeline.live.realtime.envelope import RealtimeEvent, EventType
from pipeline.live.realtime.consumer import RealtimeQueueConsumer
from pipeline.live.realtime.adapter import RealtimeAdapter
from pipeline.live.realtime.processor import RealtimeProcessor
from pipeline.live.realtime.file_consumer import FileTailConsumer


def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    
    # [Hardening] Phase 30-2: Merge Defaults for Robustness
    defaults = {
        'execution': {
            'capital': 100_000_000,
            'slippage_bps': 5,
            'fee_bps': 1
        },
        # [FIX] Add Defaults for SignalA2 (Missing in profile_champion_v3)
        'factors': {
            'lookback_window': 60,
            'bb_window': 20,
            'breakout_window': 20,
            'vol_ma_window': 20
        },
        'weights': {
            'compression': 0.4,
            'breakout': 0.4,
            'volume': 0.2
        },
        'gates': {
            'breakout_min': 0.0015,
            'vol_ratio_min': 1.3
        },
        'risk': {
            'daily_kill_switch': -0.02,
            'time_stop_minutes': 30,
            'time_stop_threshold': 0.002,
            'post_entry_cooldown_min': 5
        }
    }
    
    for section, keys in defaults.items():
        if section not in cfg:
            cfg[section] = keys
        else:
            for k, v in keys.items():
                if k not in cfg[section]:
                    cfg[section][k] = v
                    
    return cfg

def load_day_events(data_dir, date_str, universe):
    target_int = int(date_str.replace('-', ''))  # 20250702
    target_prefix = str(target_int)
    print(f"[Loader] Loading {date_str} (Int: {target_int}) ...")

    all_events = []
    usecols = ['date','open','high','low','close','volume']
    dtypes = {'date': 'string', 'open':'float64','high':'float64','low':'float64','close':'float64','volume':'float64'}

    for sym in universe:
        f = Path(data_dir) / f"{sym}.csv"
        if not f.exists():
            continue
        try:
            df = pd.read_csv(f, usecols=usecols, dtype=dtypes)
            mask = df['date'].str.startswith(target_prefix)
            day_data = df.loc[mask].copy()
            if day_data.empty:
                continue

            day_data['dt'] = pd.to_datetime(day_data['date'], format="%Y%m%d%H%M%S", errors='coerce')
            day_data = day_data.dropna(subset=['dt'])

            # Optimization: Keep dt as Timestamp, but convert to python for loop if needed?
            # Actually, keeping as Timestamp is fine for comparison if we compare properly.
            for row in day_data.itertuples(index=False):
                all_events.append({
                    'ts': row.dt, # Keep as Timestamp for floor()
                    'symbol': sym,
                    'open': row.open, 'high': row.high, 'low': row.low,
                    'close': row.close, 'volume': row.volume
                })
        except Exception:
            continue

    all_events.sort(key=lambda x: x['ts'])
    print(f"[Loader] Loaded {len(all_events)} events for {date_str}")
    return all_events

def load_recent_history(data_dir, universe, days=5):
    """
    Load recent daily data to calculate regime.
    Reads minute CSVs, resamples to Daily > Close.
    """
    print(f"[Regime] Loading recent history for {len(universe)} symbols (Last {days} days)...")
    daily_closes = {}
    
    # We need a date range to filter. 
    # Just reading the whole file isn't efficient but simple.
    # Optimization: Use usecols.
    
    for sym in universe:
        f = Path(data_dir) / f"{sym}.csv"
        if not f.exists(): continue
        
        try:
            # Read minimal cols
            df = pd.read_csv(f, usecols=['date', 'close'])
            # Parse date
            if 'datetime' in df.columns: df = df.rename(columns={'datetime':'date'})
            
            # Fast parse: Assume YYYYMMDD...
            # We need to act on DATES.
            # String slice to YYYYMMDD
            df['day'] = df['date'].astype(str).str.slice(0, 8)
            
            # Group by day, get last close
            d_close = df.groupby('day')['close'].last()
            
            # Keep last N
            d_close = d_close.tail(days + 5) # Buffer
            
            daily_closes[sym] = d_close
        except Exception:
            continue
            
    return pd.DataFrame(daily_closes).sort_index()

def calculate_regime(daily_closes):
    """
    Calculate Regime Status.
    True = Bad Regime (Block Entries).
    False = Good Regime.
    """
    if daily_closes.empty:
        print("[Regime] WARN: No history loaded. Defaulting to GOOD (False).")
        return False
        
    print("[Regime] Calculating Hero Counts...")
    pct = daily_closes.pct_change()
    
    # Hero > 15%
    hero_counts = (pct > 0.15).sum(axis=1)
    
    # Rolling 3 day avg
    rolling = hero_counts.rolling(window=3).mean().fillna(0)
    
    print("[Regime] Recent Hero Counts:")
    print(rolling.tail(5))
    
    # Check LAST completed day
    # If today is T, we use T-1 data.
    if len(rolling) > 0:
        last_hero_score = rolling.iloc[-1]
        is_bad = last_hero_score < 3.0
        status_str = "BAD (Block Entries)" if is_bad else "GOOD (Allow Entries)"
        print(f"[Regime] Score: {last_hero_score:.2f} -> Status: {status_str}")
        return is_bad
    
    return False

def run_replay(date_str, config, data_dir, universe_file, log_dir, limit=None):
    print(f"[Replay] Starting for {date_str} (Limit: {limit})")
    
    # 1. Modules
    resampler = LiveResampler(interval_min=5)
    # Init Live Components
    # Force reset logs in Replay mode
    logger = LiveLogger(log_dir, reset=True)
    universe_loader = UniverseLoader(universe_file)
    signal_eng = SignalA2(config)
    order_eng = OrderMock(config)
    risk_eng = RiskManager(config)
    
    universe = universe_loader.load()
    if limit:
        universe = universe[:limit]
        print(f"[Replay] Universe limited to {len(universe)} symbols")
    
    # 2. Warmup
    target_date = pd.to_datetime(date_str)
    warmup_days = 2 # Need ~100 bars = 500 mins. 2 days is safe.
    
    print(f"[Replay] Warming up for {warmup_days} days...")
    for i in range(warmup_days, 0, -1):
        w_date = target_date - timedelta(days=i)
        w_str = w_date.strftime("%Y-%m-%d")
        w_events = load_day_events(data_dir, w_str, universe)
        
        for evt in w_events:
            resampler.push(evt['symbol'], evt)
            closed_bars = resampler.check_closure(evt['ts'])
            if closed_bars:
                signal_eng.on_bar_closed(closed_bars)
                
    print("[Replay] Warmup Done.")

    # 3. Main Loop
    all_events = load_day_events(data_dir, date_str, universe)
    
    current_ts = None
    market_snapshot = {} 
    
    start_time = target_date.replace(hour=9, minute=0, second=0)
    end_time = target_date.replace(hour=15, minute=30, second=0)
    
    pointer = 0
    total_events = len(all_events)
    closure_cnt = 0
    
    print(f"[Live] Log Directory: {Path(log_dir).absolute()}")
    print(f"[Live] Events Log: {logger.paths['events']}")
    
    print("[Replay] Starting Main Loop...")
    while start_time <= end_time:
        current_ts = start_time
        
        # 0. Check Risk (Global) - Moved to Start to prevent Signal Leakage
        # Use previous market snapshot (T-1) for equity calc
        current_equity = order_eng.get_equity(market_snapshot)
        global_risk = risk_eng.update_global(current_equity)
        
        if global_risk == "DAILY_KILL_HALT":
            logger.log_event('HALT_TRIGGER', {'reason': global_risk, 'pnl_pct': risk_eng.daily_pnl_pct}, ts=current_ts)
            print(f"[Risk] DAILY KILL HALT TRIGGERED! PnL: {risk_eng.daily_pnl_pct*100:.2f}%")
            
            # Force Liquidate All
            for sym, pos in list(order_eng.positions.items()):
                 print(f"[Risk] Force Liquidating {sym}")
                 ord_s = order_eng.send_order(current_ts, sym, 'SELL', pos['qty'], 'MARKET', halted=risk_eng.halt_triggered)
                 logger.log_order(ord_s, event="NEW")
                 
        elif global_risk == "DAILY_KILL_HALT_ACTIVE":
             pass 

        # 1. Collect bars for this minute (09:05)
        # Fix: Use floor('min') equality logic
        minute_bars = {}
        
        while pointer < total_events:
            evt = all_events[pointer]
            evt_ts_min = evt['ts'].floor('min')
            
            if evt_ts_min == current_ts:
                minute_bars[evt['symbol']] = evt
                resampler.push(evt['symbol'], evt) 
                market_snapshot[evt['symbol']] = evt 
                pointer += 1
            elif evt_ts_min < current_ts:
                pointer += 1 # Skip old
            else:
                break # Future event
            
        # 2. Process Fills (Orders from T-1 filled at T Open)
        # 2. Process Fills (Orders from T-1 filled at T Open)
        fills, status_updates = order_eng.process_fills(current_ts, minute_bars)
        
        # Log Fills
        for fill in fills:
            risk_eng.on_fill(fill)
            logger.log_fill(fill)
            
        # Log Order Updates (REJECTED, FILLED status changes)
        for ord_upd in status_updates:
            logger.log_order(ord_upd)
            
        # 3. Check Resampler (Did T close a 5m bar?)
        # Now that we Pushed T, we check if T is a closure minute.
        closed_bars = resampler.check_closure(current_ts)
        
        if closed_bars:
            logger.log_event("BAR_CLOSED", {"ts": str(current_ts), "n_syms": len(closed_bars)}, ts=current_ts)
            closure_cnt += 1
            if closure_cnt % 20 == 0:
                print(f"[Replay] closures={closure_cnt} @ {current_ts} syms={len(closed_bars)}")
                
            best_sym, debug = signal_eng.on_bar_closed(closed_bars)
            
            # Log Signal Always
            logger.log_signal(current_ts, debug)
            
            # Trading Halt Check
            if risk_eng.halt_triggered:
                # Do not process new signals
                pass
            elif best_sym:
                curr_pos_sym = list(order_eng.positions.keys())[0] if order_eng.positions else None
                
                # Price Estimation (Use Snapshot or Close of Bar)
                est_px = 0
                if best_sym in market_snapshot:
                    est_px = market_snapshot[best_sym]['close']
                elif best_sym in closed_bars:
                    est_px = closed_bars[best_sym]['close']
                    
                if est_px > 0:
                     if curr_pos_sym and curr_pos_sym != best_sym:
                        # Switch
                        qty_old = order_eng.positions[curr_pos_sym]['qty']
                        ord_s = order_eng.send_order(current_ts, curr_pos_sym, 'SELL', qty_old, halted=risk_eng.halt_triggered)
                        logger.log_order(ord_s, event="NEW")
                        
                        # Sizing with Buffer (Operational Safety)
                        slip = config['execution']['slippage_bps'] / 10000.0
                        fee = config['execution']['fee_bps'] / 10000.0
                        
                        est_cost_per_share = est_px * (1 + fee) # Slippage included in fill price realization, but for sizing we use est_px
                        # Apply Slippage Buffer to Price
                        est_px_buff = est_px * (1 + slip)
                        est_cost_buff = est_px_buff * (1 + fee)
                        
                        max_affordable_qty = (order_eng.cash * 0.98) / est_cost_buff
                        qty_new = max(0, int(max_affordable_qty))

                        ord_b = order_eng.send_order(current_ts, best_sym, 'BUY', qty_new, halted=risk_eng.halt_triggered)
                        logger.log_order(ord_b, event="NEW")
                        logger.log_event('SIGNAL_SWITCH', {'from': curr_pos_sym, 'to': best_sym}, ts=current_ts)
                        
                     elif not curr_pos_sym:
                        # Entry
                        # Sizing with Buffer (Operational Safety)
                        slip = config['execution']['slippage_bps'] / 10000.0
                        fee = config['execution']['fee_bps'] / 10000.0
                        
                        # Apply Slippage Buffer to Price
                        est_px_buff = est_px * (1 + slip)
                        est_cost_buff = est_px_buff * (1 + fee)
                        
                        max_affordable_qty = (order_eng.cash * 0.98) / est_cost_buff
                        qty_new = max(0, int(max_affordable_qty))
                        
                        target_amt = order_eng.cash * 0.98 
                        
                        logger.log_event("SIZING_DEBUG", {
                            "ts": str(current_ts),
                            "cash": float(order_eng.cash),
                            "target_size": 0.98,
                            "target_amt": float(target_amt),
                            "est_px": float(est_px),
                            "qty_new": float(qty_new),
                            "notional": float(qty_new * est_px),
                        }, ts=current_ts)
                        
                        
                        ord_b = order_eng.send_order(current_ts, best_sym, 'BUY', qty_new, halted=risk_eng.halt_triggered)
                        logger.log_order(ord_b, event="NEW")
                        logger.log_event('SIGNAL_ENTRY', {'symbol': best_sym}, ts=current_ts)

        # 4. Check Risk (Individual Position Stops)
        # Global Halt checked at start of loop
        
        # Individual Position checks
        for sym, pos in list(order_eng.positions.items()):
            if sym in market_snapshot:
                px = market_snapshot[sym]['close'] # Latest price
                
                # Check Risk (Equity passed but ignored for Global check inside, kept for signature)
                risk_status = risk_eng.check_risk(current_ts, sym, px, current_equity)
                
                if risk_status and risk_status != "DAILY_KILL_HALT_ACTIVE":
                    # Ensure we don't log DAILY_KILL for individual symbols
                    if "DAILY_KILL" in risk_status:
                        # Should not happen if risk_manager is fixed, but safety first
                        pass
                    else:
                        print(f"[Risk] {risk_status} Triggered for {sym}")
                        ord_s = order_eng.send_order(current_ts, sym, 'SELL', pos['qty'], 'MARKET', halted=risk_eng.halt_triggered)
                        logger.log_order(ord_s, event="NEW")
                        logger.log_event('RISK_TRIGGER', {'symbol': sym, 'reason': risk_status}, ts=current_ts)

        # Tick forward
        start_time += timedelta(minutes=1)

    print("[Replay] Done.")
    final_equity = order_eng.get_equity(market_snapshot)
    print(f"Final Equity: {int(final_equity):,} KRW")
    logger.log_event("BACKTEST_RESULT", {"final_equity": int(final_equity), "equity_unit": "KRW"}, ts=current_ts)

def calc_vol_accel_helper(signal_eng):
    """
    [Project AESTHETIC] Calculate Volatility Acceleration from Signal Engine History
    """
    if not signal_eng.history: return 1.0
    
    pcts = []
    for sym, df in signal_eng.history.items():
        if len(df) < 5: continue
        # Use last 2 closes to Approx 5m return? 
        # VolAccel usually uses Daily.
        # But here we have 5m bars. 
        # We can calc 5m Vol Accel.
        # Approx: Mean Abs Return of last bar across universe
        try:
            r = df['close'].pct_change().abs().replace([np.inf, -np.inf], np.nan)
            if not r.empty: pcts.append(r.iloc[-1])
        except: pass
        
    if not pcts: return 1.0
    
    # Current Vol (Mean Absolute Return across universe)
    curr_vol = np.nanmean(pcts)
    if curr_vol == 0: return 1.0
    
    # We ideally need history of this Metric.
    # But for now, we just compare to a baseline const? 
    # Or keep a rolling list of market vol?
    # Simple Heuristic: If > 0.3% (30bps) in 5m -> High Vol
    
    # Let's use a simplified logical switch based on raw mag
    # 0.001 (0.1%) per 5m is normal.
    # 0.003 (0.3%) is high.
    
    baseline = 0.0015
    accel = 1.0 + max(0, (curr_vol - baseline) / baseline)
    return min(accel, 3.0) # Cap at 3x


def run_live(config, universe_file, log_dir, data_dir):
    print(f"=== Starting Phase 30-1 Paper Live ({datetime.now()}) ===")
    print(f"Log Dir: {Path(log_dir).absolute()}")
    
    # [BOOT] Log Module Paths for Audit
    import pipeline.live.order_mock as m_mock
    import pipeline.live.risk_manager as m_risk
    print(f"[BOOT] order_mock: {m_mock.__file__}")
    print(f"[BOOT] risk_manager: {m_risk.__file__}")
    
    # 1. Init Modules
    logger = LiveLogger(log_dir) # No reset for live (append mode safety)
    universe_loader = UniverseLoader(universe_file)
    
    if config.get('use_neural_brain', False):
        try:
             from pipeline.live.signal_neural import SignalNeuralBrain
             signal_eng = SignalNeuralBrain(config)
             print("[Live] 🧠 Neural Brain Signal Engine Activated (OSS Unchained)")
        except ImportError as e:
             print(f"[Live] ⚠️ Failed to import SignalNeuralBrain: {e}. Falling back to SignalA2.")
             signal_eng = SignalA2(config)
    else:
        signal_eng = SignalA2(config)
    
    # [Order Adapter Selection]
    if config.get('is_real_money', False):
        logger.log_event("SYSTEM_WARNING", {"msg": "!!! RUNNING WITH REAL MONEY EXECUTION !!!"})
        order_eng = OrderReal(config)
    else:
        order_eng = OrderMock(config)
        
    risk_eng = RiskManager(config)
    held_scores = {} # [AESTHETIC] Score Cache
    resampler = LiveResampler(interval_min=5)
    
    universe = universe_loader.load()
    print(f"[Live] Universe loaded: {len(universe)} symbols")
    print(f"[Live] Capital: {order_eng.cash:,.0f} KRW")
    
    logger.log_event("SYSTEM_START", {'universe_size': len(universe), 'equity_unit': 'KRW', 'initial_capital': int(order_eng.cash)}, ts=datetime.now())
    
    # [Regime Filter] Initialize
    # Use data_dir passed from args
    is_bad_regime = False
    try:
        # Load history
        hist_df = load_recent_history(data_dir, universe, days=10)
        is_bad_regime = calculate_regime(hist_df)
        if is_bad_regime:
            logger.log_event("REGIME_STATUS", {"status": "BAD", "msg": "Entries BLOCKED"}, ts=datetime.now())
        else:
            logger.log_event("REGIME_STATUS", {"status": "GOOD", "msg": "Entries ALLOWED"}, ts=datetime.now())
            
    except Exception as e:
        print(f"[Regime] Error calculating regime: {e}")
        logger.log_event("REGIME_ERROR", {"err": str(e)}, ts=datetime.now())
    
    # [Phase 30-2] Realtime Integration 
    # Configurable Source (Default to feed_temp.jsonl for verification)
    live_source_path = config.get('live_source_path', "feed_temp.jsonl") 
    print(f"[Live] Listening on {live_source_path} ...")
    
    consumer = FileTailConsumer(live_source_path)
    # Allow config override for Proof Runs (default 3.0)
    wm_sec = config.get('watermark_sec', 3.0)
    processor = RealtimeProcessor(consumer, watermark_sec=wm_sec)
    adapter = RealtimeAdapter()
    
    try:
        current_bucket_min = None
        market_snapshot = {}
        
        last_params_mtime = 0
        active_params_path = Path("config/active_params.json")

        while True:
            # [Dynamic Config Reload]
            try:
                if active_params_path.exists():
                    mtime = active_params_path.stat().st_mtime
                    if mtime > last_params_mtime:
                        print(f"[Live] Loading new params from {active_params_path}...")
                        
                        # Data Safety: Robust Read with Retry
                        dconf = None
                        for _ in range(3):
                            try:
                                with open(active_params_path, 'r', encoding='utf-8') as f:
                                    dconf = json.load(f)
                                break
                            except Exception:
                                time.sleep(0.1)
                                
                        if not dconf:
                            print("[Live] Failed to read active_params.json after retries.")
                            continue

                        # Apply to Config (Runtime Overrides)
                        scen = dconf.get('scenario', 'UNKNOWN')
                        params = dconf.get('params', {})
                        
                        # 1. Update ATR Stops
                        if 'stop_loss_atr' in params:
                            config['risk']['initial_stop_atr'] = params['stop_loss_atr']
                            risk_eng.initial_stop_atr = params['stop_loss_atr']
                            
                        # 2. Update Exposure
                        if 'max_exposure' in params:
                            config['allocation']['target_gross_exposure'] = params['max_exposure']
                            
                        # 3. Update Positions Max
                        if 'max_positions' in params:
                            config['selection']['max_positions'] = params['max_positions']
                            
                         # 4. Entry Block
                        if 'is_entry_blocked' in params:
                             config['is_entry_blocked'] = params['is_entry_blocked']
                        
                        # 5. Stop Type (New)
                        if 'stop_type' in params:
                            config['risk']['stop_type'] = params['stop_type']
                            # RiskEng update if supported
                            if hasattr(risk_eng, 'stop_type'):
                                risk_eng.stop_type = params['stop_type']
                                
                        # 6. Pyramid Weights Override (Phase 4)
                        pyramid_weights = dconf.get('pyramid_weights', {})
                        config['allocation']['pyramid_weights'] = pyramid_weights
                        
                        last_params_mtime = mtime
                        logger.log_event("STRATEGY_UPDATE", {"scenario": scen, "params": params}, ts=datetime.now())
                        print(f"[Live] 🔄 Strategy Switched to {scen} (Stop: {params.get('stop_type','?')}). Params Updated.")
            
            except Exception as e:
                print(f"[Live] Config Reload Error: {e}")
                
            now = datetime.now()
            
                # [Phase 30-2] Realtime Loop Connection Point
            event = processor.poll(now)
            
            if not event:
                # Idle / Heartbeat
                if now.second % 10 == 0:
                     lag = processor.get_lag()
                     # Log stats for Proof
                     logger.log_event("RT_STATS", {"lag": lag, "stats": processor.stats}, ts=now)
                     # print(f"[Live] Heartbeat {now.strftime('%H:%M:%S')} - Lag: {lag} - Stats: {processor.stats}")
                     
                     if os.path.exists("STOP.flag"):
                         print("[Live] STOP.flag detected. Exiting.")
                         break
                time.sleep(0.1)
                continue
                
            # Fail-Open Event Handling Pattern (Phase 30-2 Ops Standard)
            handled_ok = False
            try:
                # [Proof] Log Stats Periodically (every 500 events) for Storm Proof Visibility
                # Stats are usually inexpensive to query.
                if processor.stats['in'] % 500 == 0 and processor.stats['in'] > 0:
                     # Log only once per threshold crossing (approximate if dedup/skipped, but good enough)
                     # Or just use a simple modulo check.
                     # We can't use 'processed_count' strictly if we restart, but processor.stats persists in memory.
                     # To avoid spam, we might want a simple global counter or just rely on modulo.
                     # But since poll() happens often, we should check if we already logged this milestone?
                     # Let's just log. 5000 / 500 = 10 logs. Acceptable.
                     logger.log_event("RT_STATS", {"lag": processor.get_lag(), "stats": processor.stats}, ts=now)

                # [Ops] Robust Event Processing Wrapper
                if event.event_type == EventType.TICK:
                    # [Phase 30-3] TICK Support (Tick -> 1m Bar Aggregation)
                    # Payload: {price, volume, cum_volume, ...}
                    # We need to construct a 1m Bar and push to standard logic IF minute flips.
                    
                    p = event.payload
                    sym = event.symbol
                    # Ensure numeric
                    price = float(p.get('price', 0))
                    vol = float(p.get('volume', 0))
                    
                    # Tick Time (Aware)
                    tick_ts = event.event_time
                    # FIX: event.event_time might be str or datetime. Convert to pd.Timestamp for .floor()
                    tick_ts = pd.Timestamp(tick_ts)
                        
                    tick_min = tick_ts.floor('min')
                    
                    # DEBUG
                    # print(f"DEBUG: TICK {sym} @ {tick_ts} -> Min {tick_min}")
                    
                    # Initialize Aggregator State if missing
                    if 'tick_agg' not in locals():
                        tick_agg = {} # {sym: {current_min, open, high, low, close, vol}}
                        
                    if sym not in tick_agg:
                        tick_agg[sym] = {
                            'min': tick_min, 
                            'open': price, 'high': price, 'low': price, 'close': price, 'volume': vol
                        }
                    else:
                        agg = tick_agg[sym]
                        if agg['min'] == tick_min:
                            # Update current minute
                            agg['high'] = max(agg['high'], price)
                            agg['low'] = min(agg['low'], price)
                            agg['close'] = price
                            agg['volume'] += vol
                        else:
                            # Minute Flip -> Close 1m Bar
                            # 1. Create 1m Bar Event (Synthetic)
                            closed_1m_bar = {
                                'ts': agg['min'], # Timestamp of the closed bar (start of min? or end? standard uses floor)
                                'symbol': sym,
                                'open': agg['open'],
                                'high': agg['high'],
                                'low': agg['low'],
                                'close': agg['close'],
                                'volume': agg['volume']
                            }
                            
                            # Log 1m Closure check
                            # logger.log_event("BAR_1M", closed_1m_bar, ts=tick_ts)

                            # 2. Push to Main Logic (Resampler + Signals) works on 1m bars
                            # We treat this synthetic bar exactly like an incoming BAR event
                            
                            # Market Snapshot Update
                            market_snapshot[sym] = closed_1m_bar
                            
                            # Push to 5m Resampler
                            resampler.push(sym, closed_1m_bar)
                            
                            # Check 5m Closure
                            closed_5m = resampler.check_closure(agg['min']) # using the closed bar's TS
                            
                            if closed_5m:
                                current_ts = agg['min']
                                logger.log_event("BAR_CLOSED", {"count": len(closed_5m), "ts": str(current_ts)}, ts=current_ts)
                                print(f"[Live] Processing BAR Closure @ {current_ts} ({len(closed_5m)} syms)")
                                
                                # --- ENGINE LOGIC COPY (Refactor target) ---
                                # 0. Global Halt Check
                                risk_eng.update_global(order_eng.get_equity(market_snapshot))
                                
                                # 1. Process Fills
                                minute_bars_for_fill = {sym: closed_1m_bar} # Use the 1m bar just closed for fills? 
                                # Actually fills processing usually happens at OPEN of NEXT bar using PREV bars. 
                                # Detailed fill simulation might need more care, but for now we run it.
                                fills, status_updates = order_eng.process_fills(current_ts, minute_bars_for_fill)
                                for fill in fills:
                                    logger.log_fill(fill)
                                    risk_eng.on_fill(fill)
                                for u in status_updates:
                                    logger.log_order(u)
                                    
                                # 2. Signal
                                # 2. Signal
                                vol_accel = calc_vol_accel_helper(signal_eng)
                                best_sym, debug = signal_eng.on_bar_closed(closed_5m, vol_accel=vol_accel)
                                
                                # [AESTHETIC] Churn Filter
                                # If switching, New Score must be > Old Score * 1.2
                                curr_pos_sym = list(order_eng.positions.keys())[0] if order_eng.positions else None
                                if best_sym and curr_pos_sym and best_sym != curr_pos_sym:
                                    old_score = held_scores.get(curr_pos_sym, 0)
                                    new_score = debug.get('score', 0)
                                    
                                    # Override if Score is None (e.g. fallback)
                                    if new_score > 0 and old_score > 0:
                                        if new_score < old_score * 1.2:
                                            print(f"[AESTHETIC] 🛡️ Churn Blocked: {best_sym}({new_score:.2f}) not > 1.2x {curr_pos_sym}({old_score:.2f})")
                                            logger.log_event("CHURN_BLOCK", {"target": best_sym, "held": curr_pos_sym, "ratio": new_score/old_score}, ts=current_ts)
                                            best_sym = None # Cancel Signal
                                
                                # Update Score Map
                                if best_sym: held_scores[best_sym] = debug.get('score', 0)
                                
                                # [Phase 4] Hero Override (Aggressive Scale)
                                pyramid_cols = config.get('allocation', {}).get('pyramid_weights', {})
                                hero_override_active = False
                                
                                # Check if best_sym is Hero OR we hold a Hero
                                target_hero = None
                                if best_sym and best_sym in pyramid_cols:
                                    target_hero = best_sym
                                else:
                                    # Periodic check: scan holdings
                                    pass

                                if target_hero:
                                    # [Pyramiding Logic: Phase 8.2 Scenario C Optimized]
                                    # Configurable Thresholds for faster scaling
                                    # Target: 0.30 -> 0.40 (Initial), 0.05/0.10 -> 0.03/0.07 (Thresholds)
                                    
                                    t_weight = 0.40 # Phase 8.2: Default Stage 1 (Scout 40%)
                                    stage_label = "1_SCOUT_OPT"
                                    
                                    # Check Existing Position PnL
                                    pos = order_eng.positions.get(target_hero)
                                    if pos:
                                        avg_p = pos.get('avg_px', 0)
                                        # Use current Close from snapshot
                                        cur_p = closed_5m[target_hero]['close']
                                        if avg_p > 0:
                                            pnl_pct = (cur_p - avg_p) / avg_p
                                            if pnl_pct > 0.07: # Phase 8.2: 7% Threshold
                                                t_weight = 0.70 # Stage 3 (All-In)
                                                stage_label = "3_ALLIN"
                                            elif pnl_pct > 0.03: # Phase 8.2: 3% Threshold
                                                t_weight = 0.50 # Stage 2 (Main)
                                                stage_label = "2_MAIN"
                                    
                                    # [Adaptive Shield: Ice Age]
                                    # scen variable is from outer loop config reload
                                    if 'scen' in locals() and scen == 'ICE_AGE':
                                        t_weight = min(t_weight, 0.10)
                                        stage_label += "_ICEAGE"
                                        
                                    print(f"[Hero] Logic Triggered: {target_hero} -> {stage_label} (Target: {t_weight*100}%)")
                                    
                                    eq_total = order_eng.get_equity(market_snapshot)
                                    target_amt = eq_total * t_weight
                                    
                                    # Check Current Size
                                    pos = order_eng.positions.get(target_hero, {})
                                    curr_qty = pos.get('qty', 0)
                                    px = closed_5m[target_hero]['close']
                                    target_qty = int(target_amt / px)
                                    
                                    if target_qty > curr_qty:
                                        cost = (target_qty - curr_qty) * px * 1.002
                                        if order_eng.cash < cost:
                                            print(f"[Hero] 🦸 Insufficient Cash for {target_hero}. Harvesting...")
                                            for h_sym, h_pos in list(order_eng.positions.items()):
                                                if h_sym != target_hero:
                                                    print(f"[Hero] 🔪 Harvesting {h_sym}...")
                                                    order_eng.send_order(current_ts, h_sym, 'SELL', h_pos['qty'], halted=False)
                                                    
                                        q_buy = target_qty - curr_qty
                                        if q_buy > 0:
                                            print(f"[Hero] 🚀 Executing HERO BUY {target_hero}: {q_buy} (Target: {t_weight*100}%)")
                                            ord_b = order_eng.send_order(current_ts, target_hero, 'BUY', q_buy, halted=risk_eng.halt_triggered)
                                            logger.log_order(ord_b)
                                            logger.log_event("HERO_ALLOC", {"symbol": target_hero, "qty": q_buy, "weight": t_weight}, ts=current_ts)
                                        
                                        hero_override_active = True
                                        best_sym = None 

                                # [Phase 1 Normalization] Fallback Logic
                                if not best_sym and not hero_override_active:
                                    holding_syms = list(order_eng.positions.keys())
                                    if len(holding_syms) < 5: 
                                        fb_sym, fb_debug = signal_eng.get_fallback_candidate(exclude_symbols=holding_syms)
                                        if fb_sym:
                                            best_sym = fb_sym
                                            debug = fb_debug
                                            logger.log_event("SIGNAL_FALLBACK", {"symbol": fb_sym, "score": fb_debug.get('score')}, ts=current_ts)
                                
                                logger.log_signal(current_ts, debug)
                                
                                # 3. Execution
                                if not risk_eng.halt_triggered and best_sym:
                                     # [Regime Filter] Block Entry
                                     if not curr_pos_sym and is_bad_regime:
                                         # Only Block New Entries. Switches (if logic allowed) might be tricky,
                                         # but StrategyA2 isn't designed to switch FROM cash if blocked.
                                         # A2 Switch logic: pos_sym -> best_sym.
                                         # If we are in position, we allow Switching (it's an Exit+Entry).
                                         # Or should we force Exit to Cash?
                                         # "No Hero = No Trade" usually implies "Go to Cash".
                                         # For now, simplest implementation: Block Entry from Cash.
                                         # Users can manually intervene to close existing.
                                         pass
                                     else:
                                         # (Strategy Logic placeholder - handled in BAR branch too)
                                         pass
                                # -------------------------------------------
                            
                            # Reset Aggregator for new minute
                            tick_agg[sym] = {
                                'min': tick_min, 
                                'open': price, 'high': price, 'low': price, 'close': price, 'volume': vol
                            }

                    handled_ok = True

                elif event.event_type == EventType.BAR:
                    # 1. Adapt to Minute Bar (Replay Schema)
                    replay_evt = adapter.to_replay_evt(event)
                    if not replay_evt:
                        # Log warning? For now just skip
                        handled_ok = True
                    else:
                        sym = replay_evt['symbol']
                        bar_ts = replay_evt['ts']
                        
                        # Update Market Snapshot
                        market_snapshot[sym] = replay_evt
                        
                        # Standard Live Loop Logic: Push -> Check Closure
                        resampler.push(sym, replay_evt)
                        closed_bars = resampler.check_closure(bar_ts) 
                        
                        # B. Logic Trigger (Only if bars closed)
                        if closed_bars:
                            current_ts = bar_ts 
                            
                            logger.log_event("BAR_CLOSED", {"count": len(closed_bars), "ts": str(current_ts)}, ts=current_ts)
                            print(f"[Live] Processing BAR Closure @ {current_ts} ({len(closed_bars)} syms)")
        
                            # 0. Global Halt Check (Pre-empt)
                            risk_eng.update_global(order_eng.get_equity(market_snapshot))
                             
                            # 1. Process Fills (Simulated against this new bar)
                            minute_bars_for_fill = {sym: replay_evt}
                            fills, status_updates = order_eng.process_fills(current_ts, minute_bars_for_fill)
                            
                            for fill in fills:
                                logger.log_fill(fill)
                                risk_eng.on_fill(fill)
                                
                            for order_update in status_updates:
                                logger.log_order(order_update)
                            
                            # 2. Signal
                            # 2. Signal
                            vol_accel = calc_vol_accel_helper(signal_eng)
                            best_sym, debug = signal_eng.on_bar_closed(closed_bars, vol_accel=vol_accel)
                            
                            # [AESTHETIC] Churn Filter
                            curr_pos_sym = list(order_eng.positions.keys())[0] if order_eng.positions else None
                            if best_sym and curr_pos_sym and best_sym != curr_pos_sym:
                                old_score = held_scores.get(curr_pos_sym, 0)
                                new_score = debug.get('score', 0)
                                
                                if new_score > 0 and old_score > 0:
                                    if new_score < old_score * 1.2:
                                        print(f"[AESTHETIC] Churn Blocked (BAR): {best_sym}({new_score:.2f}) not > 1.2x {curr_pos_sym}({old_score:.2f})")
                                        logger.log_event("CHURN_BLOCK", {"target": best_sym, "held": curr_pos_sym, "ratio": new_score/old_score}, ts=current_ts)
                                        best_sym = None 
                            
                            if best_sym: held_scores[best_sym] = debug.get('score', 0)
                            
                            # [Phase 1 Normalization] Fallback Logic (Top-up)
                            if not best_sym:
                                # Check Exposure: If we hold < 5 positions (approx), or have cash.
                                # Simple Heuristic: If we are not blocked by Global Risk, try fallback.
                                # Exclude current holdings.
                                holding_syms = list(order_eng.positions.keys())
                                # Assuming 5 slots max, if len < 5, try top-up
                                if len(holding_syms) < 5: 
                                    fb_sym, fb_debug = signal_eng.get_fallback_candidate(exclude_symbols=holding_syms)
                                    if fb_sym:
                                        best_sym = fb_sym
                                        debug = fb_debug
                                        logger.log_event("SIGNAL_FALLBACK", {"symbol": fb_sym, "score": fb_debug.get('score')}, ts=current_ts)

                            logger.log_signal(current_ts, debug)
                            
                            # 3. Execution Logic
                            if risk_eng.halt_triggered:
                                pass
                            elif best_sym:
                                # [Regime Filter] Block Entry
                                if not list(order_eng.positions.keys()) and is_bad_regime:
                                    # Block Entry
                                    logger.log_event('REGIME_BLOCK', {'symbol': best_sym, 'reason': 'BAD_MARKET'}, ts=current_ts)
                                else:
                                    # Existing Switch Logic Placeholder
                                    pass 
                        
                        # Mark as handled
                        print(f"[Live] Processing BAR {sym} @ {bar_ts}")
                        handled_ok = True
    
                elif event.event_type == EventType.ORDER_UPDATE:
                    # [Fix] Use log_event instead of log_order to avoid schema mismatch
                    # ORDER_UPDATE payload schema is variable from broker, log_order requires strict internal schema.
                    print(f"[Live] Received ORDER_UPDATE: {event.payload}")
                    logger.log_event("ORDER_UPDATE", event.payload, ts=now)
                    handled_ok = True
    
                elif event.event_type == EventType.HEARTBEAT:
                    handled_ok = True
                    
                else:
                    logger.log_event("EVENT_DROP", {"reason":"UNSUPPORTED_TYPE", "evt": str(event)}, ts=now)
                    handled_ok = True
                    
            except Exception as e:
                # [Ops] Catch-all for stability. Log Full Context.
                err_ctx = {
                    "err": str(e),
                    "event_type": str(event.event_type),
                    "event_id": getattr(event, "event_id", "N/A"),
                     # Safe dump of payload
                    "payload_keys": list(event.payload.keys()) if hasattr(event, "payload") and isinstance(event.payload, dict) else "N/A"
                }
                logger.log_event("EVENT_HANDLE_ERR", err_ctx, ts=now)
                print(f"[Live] CRITICAL ERROR handling event: {e}")
                
                # Policy: Fail-Open (Skip bad event to keep engine alive)
                handled_ok = True
            
            finally:
                if handled_ok:
                    processor.commit()

    except KeyboardInterrupt:
        print("\n[Live] User Interrupted.")
        
    print("[Live] Shutdown.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--mode", required=True, choices=['replay', 'paper', 'live'])
    parser.add_argument("--date", help="YYYYMMDD for replay")
    parser.add_argument("--limit", type=int, help="Limit universe size for replay-lite")
    parser.add_argument("--data_dir", default="GARAM_Data/history/minute")
    parser.add_argument("--universe_file", default="GARAM_Data/real_universe_400.csv")
    parser.add_argument("--log_dir", default="logs/phase30/paper")
    parser.add_argument("--real-money", action="store_true", help="Enable REAL EXECUTION (Use with Caution)")
    parser.add_argument("--brain", action="store_true", help="Activate OSS Neural Brain (OSS Unchained)")
    
    args = parser.parse_args()
    cfg = load_config(args.config)
    
    # [Config Injection]
    if hasattr(args, "real_money") and args.real_money:
        cfg['is_real_money'] = True
    else:
        cfg['is_real_money'] = False

    if args.brain:
        cfg['use_neural_brain'] = True
    
    if args.mode == 'replay':
        if not args.date:
            print("Date required for replay")
            return
        run_replay(args.date, cfg, args.data_dir, args.universe_file, args.log_dir, args.limit)
    elif args.mode in ['live', 'paper']:
        run_live(cfg, args.universe_file, args.log_dir, args.data_dir)
    else:
        print(f"Mode {args.mode} not supported")

if __name__ == "__main__":
    main()
