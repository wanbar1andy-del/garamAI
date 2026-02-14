import argparse
import time
import yaml
import pandas as pd
import json
import uuid
import os
import traceback
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Fix Import Path for Pipeline
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ZoneInfo Handling
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

# Import Core Pipeline Components
from pipeline.live.universe_loader import UniverseLoader
from pipeline.live.signal_a2 import SignalA2
from pipeline.live.order_mock import OrderMock
from pipeline.live.order_real import OrderReal
from pipeline.live.risk_manager import RiskManager
from pipeline.live.realtime.envelope import EventType
from pipeline.live.realtime.file_consumer import FileTailConsumer
from pipeline.live.realtime.processor import RealtimeProcessor

# ==========================================
# PHASE 9: SHADOW LOGGER (Strict JSONL & KST)
# ==========================================
class ShadowLogger:
    def __init__(self, log_dir, run_id, config_name="X-6d"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.config_name = config_name
        self.engine_git = os.environ.get("GIT_SHA", "unknown")
        self.seq = 0
        self.current_filename = None
        self._update_filename()

    def _kst_now(self):
        return datetime.now(tz=KST)

    def _utc_now(self):
        return datetime.now(tz=timezone.utc)


    def _update_filename(self):
        # Rotate by KST Date and include run_id to avoid collision
        today = self._kst_now().strftime("%Y-%m-%d")
        self.current_filename = self.log_dir / f"{today}.{self.run_id}.engine.jsonl"

    def log(self, event_type, data, *, equity, dd, regime, active_pos):
        self.seq += 1
        
        now_kst = self._kst_now()
        now_utc = self._utc_now()
        
        # Check rotation
        today_fn = self.log_dir / f"{now_kst.strftime('%Y-%m-%d')}.{self.run_id}.engine.jsonl"
        if today_fn != self.current_filename:
            self.current_filename = today_fn

        entry = {
            "seq": self.seq,
            "ts_utc": now_utc.isoformat().replace('+00:00', 'Z'),
            "ts_kst": now_kst.isoformat(),
            "run_id": self.run_id,
            "engine": "X6D_PAPER",
            "engine_git": self.engine_git,
            "config_name": self.config_name,
            "event": event_type,
            "event_type": event_type, # Backward Compatibility (P0)
            "equity": round(float(equity), 6),
            "dd": round(float(dd), 6),
            "regime_state": regime,
            "active_pos": active_pos or ""
        }
        entry.update(data)

        with open(self.current_filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
        print(f"[{now_kst.strftime('%H:%M:%S')}] {event_type} | Eq:{equity:.4f} | {data.get('ticker') or data.get('msg') or ''}")



# ==========================================
# PHASE X-6d PARAMETERS
# ==========================================
X6D_PARAMS = {
    "bear_dd_trigger": -0.05, 
    "min_ban_days": 5,
    "shadow_unban_minutes": 15, 
    "unban_lookback": 3,
    "unban_min_days": 2,
    "recovery_cap": 0.20,
    "bear_cap": 0.50,
    "min_hold_mins": 5,
    "hard_exit_pnl": -0.007,        
    "reclaim_loss_bars": 2,
    "switch_threshold_pnl": -0.003, 
    "min_score_edge": 0.10,
    "hero_score_abs": 3.0,
    "hero_override_per_day": 1,
    "hero_target_frac": 0.60
}

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def _fg(obj, key, default=None):
    """Safe getter for dict or object"""
    if isinstance(obj, dict): return obj.get(key, default)
    return getattr(obj, key, default)

def _to_int(x, default=0):
    """Safe int caster"""
    try: return int(float(x))
    except: return default

def normalize_fill(fill):
    """
    Standardize Fill Object for Logging (Robust Version).
    """
    ticker = _fg(fill, "symbol") or _fg(fill, "ticker") or _fg(fill, "code") or "UNKNOWN"
    qty = _fg(fill, "qty", 0) or _fg(fill, "filled_qty", 0) or 0
    side = _fg(fill, "side") or _fg(fill, "action") or "UNKNOWN"
    px = _fg(fill, "fill_px") or _fg(fill, "price") or _fg(fill, "price_fill") or 0.0
    fee = _fg(fill, "fee") or _fg(fill, "commission") or _fg(fill, "fee_paid") or 0.0
    oid = _fg(fill, "order_id") or _fg(fill, "id") or _fg(fill, "broker_order_id") or "UNKNOWN"

    return {
        "broker_order_id": str(oid),
        "ticker": str(ticker),
        "qty": _to_int(qty),
        "price_fill": float(px),
        "fee_paid": float(fee),
        "side": str(side)
    }

def normalize_market_event(event):
    """
    Standardize TICK/BAR events into a common structure for Phase 9 verification.
    Handles nested payloads and varying key names.
    Robust version for flat/nested/mixed events.
    """
    raw = {}
    if hasattr(event, 'payload') and event.payload:
        raw = event.payload
    elif isinstance(event, dict): 
        raw = event
    
    # 1. Symbol Extraction
    sym = raw.get('symbol') or raw.get('ticker') or getattr(event, 'symbol', None)
    
    # 2. Timestamp Extraction
    ts = raw.get('ts') or raw.get('event_time') or raw.get('datetime') or getattr(event, 'event_time', None)
        
    # 3. Price Extraction (Close)
    close = raw.get('close')
    if close is None:
        # Check for nested payload (e.g. from some feed formats)
        if isinstance(raw.get('payload'), dict):
            close = raw['payload'].get('close') or raw['payload'].get('price')
        if close is None:
            close = raw.get('price') or getattr(event, 'price', None)
            
    if not sym or not ts or close is None:
        return None

    try:
        ts_obj = pd.Timestamp(ts)
    except:
        ts_obj = datetime.now() # Fallback if string parse fails

    return {"symbol": str(sym), "ts": ts_obj, "close": float(close)}

def run_live_x6d(config, universe_file, log_dir, data_dir):
    run_id = str(uuid.uuid4())
    print(f"=== Starting Phase 9 Shadow Mode (Strict X-6d + Norm v2) ===")
    print(f"Run ID: {run_id}")
    
    logger = ShadowLogger(log_dir, run_id)
    universe_loader = UniverseLoader(universe_file)
    signal_eng = SignalA2(config) 
    
    is_real_money = config.get('is_real_money', False)
    if is_real_money:
        order_eng = OrderReal(config)
    else:
        order_eng = OrderMock(config)
        
    # [SHADOW TEST MODE] Configurable Injection
    shadow_test_mode = config.get("shadow_test_mode", False)
    if shadow_test_mode:
        test_sym = "005930"
        print(f"[SHADOW CHECK] Injecting TEST position for {test_sym} (Entry: 100,000)")
        from zoneinfo import ZoneInfo
        kst = ZoneInfo("Asia/Seoul")
        order_eng.positions[test_sym] = {
            'qty': 10,
            'entry_price': 100000.0,
            'entry_ts': datetime.now(kst) - timedelta(hours=1),
            'mkt_value': 1000000.0
        }
    
    universe = universe_loader.load()
    
    # State Initialization
    regime_state = {
        'status': 'NORMAL', 
        'ban_start': None,
        'peak_equity': order_eng.get_equity({}) 
    }
    
    # Live Loop
    src_path = config.get('live_source_path', "feed_temp.jsonl")
    src_path_abs = os.path.abspath(src_path)
    
    consumer = FileTailConsumer(src_path)
    processor = RealtimeProcessor(consumer)
    
    last_heartbeat = datetime.now()
    market_snapshot = {}
    
    # Initial Log
    active_pos_str = ",".join(order_eng.positions.keys())
    eq = order_eng.get_equity({})
    
    # 1. BOOT LOG 
    logger.log("BOOT", {
        "msg": "Boot Config",
        "live_source_path": src_path,
        "live_source_path_abs": src_path_abs,
        "live_source_exists": os.path.exists(src_path_abs),
        "cwd": os.getcwd(),
        "pid": os.getpid(),
        "test_mode": shadow_test_mode
    }, equity=eq, dd=0.0, regime='NORMAL', active_pos=active_pos_str)
    
    logger.log("HEARTBEAT", {"msg": "Engine Started", "cash": order_eng.cash}, 
               equity=eq, dd=0.0, regime='NORMAL', active_pos=active_pos_str)
    
    # 2. HEARTBEAT COUNTERS 
    rx_total = 0
    norm_ok = 0
    norm_fail = 0

    try:
        while True:
            now = datetime.now()
            
            # 1. State Calculation
            current_equity = order_eng.get_equity(market_snapshot)
            if current_equity > regime_state['peak_equity']:
                regime_state['peak_equity'] = current_equity
            
            dd = (current_equity - regime_state['peak_equity']) / regime_state['peak_equity']
            active_pos_str = ",".join(order_eng.positions.keys())
            
            # 2. HEARTBEAT (1 min)
            if (now - last_heartbeat).total_seconds() > 60:
                logger.log("HEARTBEAT", {
                    "msg": "Alive",
                    "rx_total": rx_total,
                    "norm_ok": norm_ok,
                    "norm_fail": norm_fail
                }, equity=current_equity, dd=dd, regime=regime_state['status'], active_pos=active_pos_str)
                last_heartbeat = now
            
            event = processor.poll(now)
            if not event:
                time.sleep(0.1)
                continue
            
            rx_total += 1
            
            # 3. RAW EVENT LOGGING (First 5)
            if rx_total <= 5:
                payload = getattr(event, "payload", {})
                logger.log("EVENT_RX", {
                    "raw_event_type": str(getattr(event, "event_type", "")),
                    "payload_type": str(type(payload)),
                    "payload_keys": list(payload.keys()) if isinstance(payload, dict) else None,
                    "has_symbol_attr": hasattr(event, "symbol"),
                    "has_event_time_attr": hasattr(event, "event_time"),
                }, equity=current_equity, dd=dd, regime=regime_state['status'], active_pos=active_pos_str)

            # NORMALIZE
            norm_evt = normalize_market_event(event)
            
            if norm_evt:
                norm_ok += 1
                sym = norm_evt['symbol']
                ts = norm_evt['ts']
                close = norm_evt['close']
                
                # Update Snapshot (OrderMock requires 'open' for fill execution)
                if sym not in market_snapshot: market_snapshot[sym] = {}
                market_snapshot[sym]['close'] = close
                market_snapshot[sym]['open'] = close    # Proxy for Immediate Execution
                market_snapshot[sym]['high'] = close
                market_snapshot[sym]['low'] = close
                market_snapshot[sym]['price'] = close   # Fallback
                market_snapshot[sym]['ts'] = ts

                # PROOF OF DATA: Log MARKET event
                should_log_market = False
                if norm_ok <= 20: should_log_market = True
                elif (logger.seq % 200) == 0: should_log_market = True
                
                if should_log_market:
                    etype = getattr(event, "event_type", "UNKNOWN")
                    if hasattr(etype, "value"): etype = etype.value
                    
                    logger.log("MARKET", {
                        "ticker": sym,
                        "close": close,
                        "src": str(etype),
                    }, equity=current_equity, dd=dd, regime=regime_state['status'], active_pos=active_pos_str)
                
                # Update Equity
                current_equity = order_eng.get_equity(market_snapshot)
                dd = (current_equity - regime_state['peak_equity']) / regime_state['peak_equity']
                
                # --- REGIME LOGIC ---
                if regime_state['status'] == 'NORMAL':
                    if dd <= X6D_PARAMS['bear_dd_trigger']:
                        regime_state['status'] = 'BAN'
                        regime_state['ban_start'] = now
                        logger.log("REGIME_UPDATE", {"action": "TRIGGER_BAN", "peak": regime_state['peak_equity']}, 
                                   equity=current_equity, dd=dd, regime='BAN', active_pos=active_pos_str)
                        
                        # LIQUIDATE ALL
                        for pos_sym, pos in list(order_eng.positions.items()):
                            reason = "BAN_EXIT"
                            logger.log("SIGNAL", {"signal_type": "BAN_EXIT", "ticker_from": pos_sym, "reason": reason},
                                       equity=current_equity, dd=dd, regime='BAN', active_pos=active_pos_str)
                            
                            logger.log("ORDER_SUBMIT", {"side": "SELL", "ticker": pos_sym, "qty": pos['qty'], "reason": reason},
                                       equity=current_equity, dd=dd, regime='BAN', active_pos=active_pos_str)
                                       
                            order = order_eng.send_order(ts, pos_sym, 'SELL', pos['qty'], 'MARKET')
                            
                            # Execute Check (Mock Only)
                            if not is_real_money and order:
                                fills, _ = order_eng.process_fills(ts, market_snapshot)
                                for fill in fills:
                                    f_log = normalize_fill(fill)
                                    # RECONCILIATION
                                    current_equity = order_eng.get_equity(market_snapshot) 
                                    if current_equity > regime_state['peak_equity']: regime_state['peak_equity'] = current_equity
                                    dd = (current_equity - regime_state['peak_equity']) / regime_state['peak_equity']
                                    active_pos_str = ",".join(order_eng.positions.keys())
                                    
                                    logger.log("ORDER_FILL", f_log, equity=current_equity, dd=dd, regime='BAN', active_pos=active_pos_str)
                                    
                                    logger.log("POSITION_SNAPSHOT", {"active_pos": active_pos_str}, equity=current_equity, dd=dd, regime='BAN', active_pos=active_pos_str)

                elif regime_state['status'] == 'BAN':
                    ban_duration = (now - regime_state['ban_start']).total_seconds() / 60.0 
                    threshold_mins = X6D_PARAMS.get('shadow_unban_minutes', 60*24*5) 
                    
                    if ban_duration >= threshold_mins and dd > -0.03:
                        regime_state['status'] = 'NORMAL'
                        logger.log("REGIME_UPDATE", {"action": "UNBAN", "duration_mins": ban_duration},
                                   equity=current_equity, dd=dd, regime='NORMAL', active_pos=active_pos_str)

                # --- FAIL-FAST & EXECUTION ---
                if regime_state['status'] == 'NORMAL':
                    for pos_sym, pos in list(order_eng.positions.items()):
                        if pos_sym == sym: 
                            pnl = (close / pos['entry_price'] - 1)
                            
                            # --- FAIL-FAST: TZ-safe held time ---
                            entry_ts = pos.get("entry_ts", None)
                            held_mins = 0.0
                            
                            try:
                                ts_evt = pd.Timestamp(ts)
                                entry_ts_evt = pd.Timestamp(entry_ts)
                            
                                # Align timezone if one is naive and the other is aware
                                if ts_evt.tzinfo is not None and entry_ts_evt.tzinfo is None:
                                    entry_ts_evt = entry_ts_evt.tz_localize(ts_evt.tzinfo)
                                elif ts_evt.tzinfo is None and entry_ts_evt.tzinfo is not None:
                                    ts_evt = ts_evt.tz_localize(entry_ts_evt.tzinfo)
                            
                                held_mins = (ts_evt - entry_ts_evt).total_seconds() / 60.0
                            except Exception:
                                held_mins = 0.0 # Fallback: do not crash
                            
                            if held_mins >= X6D_PARAMS['min_hold_mins'] and pnl <= X6D_PARAMS['hard_exit_pnl']:
                                reason = f"FAIL_FAST({pnl*100:.2f}%)"
                                logger.log("RISK", {"type": "FAIL_FAST", "symbol": pos_sym, "pnl": pnl, "reason": reason}, 
                                           equity=current_equity, dd=dd, regime='NORMAL', active_pos=active_pos_str)
                                
                                logger.log("ORDER_SUBMIT", {"side": "SELL", "ticker": pos_sym, "qty": pos['qty'], "reason": reason},
                                           equity=current_equity, dd=dd, regime='NORMAL', active_pos=active_pos_str)
                                           
                                order = order_eng.send_order(ts, pos_sym, 'SELL', pos['qty'], 'MARKET')
                                
                                # Execute Check (Mock Only)
                                if not is_real_money and order:
                                    fills, _ = order_eng.process_fills(ts, market_snapshot)
                                    
                                    if fills:
                                        for fill in fills:
                                            f_log = normalize_fill(fill)
                                            # Recalculate State
                                            current_equity = order_eng.get_equity(market_snapshot)
                                            if current_equity > regime_state['peak_equity']: regime_state['peak_equity'] = current_equity
                                            dd = (current_equity - regime_state['peak_equity']) / regime_state['peak_equity']
                                            active_pos_str = ",".join(order_eng.positions.keys())
                                            
                                            logger.log("ORDER_FILL", f_log, equity=current_equity, dd=dd, regime='NORMAL', active_pos=active_pos_str)
                                    else:
                                        # Optional: fills가 비는 경우를 운영에서 바로 보이게
                                        current_equity = order_eng.get_equity(market_snapshot)
                                        if current_equity > regime_state['peak_equity']: regime_state['peak_equity'] = current_equity
                                        dd = (current_equity - regime_state['peak_equity']) / regime_state['peak_equity']
                                        active_pos_str = ",".join(order_eng.positions.keys())
                                        
                                        logger.log("ORDER_FILL", {
                                            "broker_order_id": "NO_FILL",
                                            "ticker": pos_sym,
                                            "qty": pos.get("qty", 0),
                                            "price_fill": 0.0,
                                            "fee_paid": 0.0,
                                            "side": "SELL",
                                            "msg": "process_fills returned empty"
                                        }, equity=current_equity, dd=dd, regime='NORMAL', active_pos=active_pos_str)

                                    # Snapshot은 최종 상태 1회
                                    active_pos_str = ",".join(order_eng.positions.keys())
                                    logger.log("POSITION_SNAPSHOT", {"active_pos": active_pos_str}, equity=current_equity, dd=dd, regime='NORMAL', active_pos=active_pos_str)
            else:
                norm_fail += 1
            
            processor.commit()
            
    except Exception as e:
        # P0-3: ERROR Logging
        msg = f"{str(e)} | {traceback.format_exc()}"
        logger.log("ERROR", {"msg": msg, "where": "main_loop"}, 
                   equity=current_equity, dd=dd, regime=regime_state['status'], active_pos=active_pos_str)
        print(f"[FATAL] {msg}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--universe_file", default="GARAM_Data/real_universe_400.csv")
    parser.add_argument("--log_dir", default="logs/shadow")
    parser.add_argument("--data_dir", default="GARAM_Data/history/minute")
    args = parser.parse_args()
    
    cfg = load_config(args.config)
    run_live_x6d(cfg, args.universe_file, args.log_dir, args.data_dir)
