import argparse
import time
import yaml
import pandas as pd
import json
import uuid
import os
import traceback
import sys
import torch
import numpy as np
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
from pipeline.live.order_mock import OrderMock
from pipeline.live.order_real import OrderReal
from pipeline.live.realtime.file_consumer import FileTailConsumer
from pipeline.live.realtime.processor import RealtimeProcessor

# Import OSS Brain
from scripts.neural_brain import GaramNeuralBrain

# ==========================================
# PHASE 9: OSS BRAIN LOGGER
# ==========================================
class ShadowLogger:
    def __init__(self, log_dir, run_id, config_name="OSS-Brain"):
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
        today = self._kst_now().strftime("%Y-%m-%d")
        self.current_filename = self.log_dir / f"{today}.{self.run_id}.oss_brain.jsonl"

    def log(self, event_type, data, *, equity, dd, regime, active_pos):
        self.seq += 1
        now_kst = self._kst_now()
        now_utc = self._utc_now()
        
        today_fn = self.log_dir / f"{now_kst.strftime('%Y-%m-%d')}.{self.run_id}.oss_brain.jsonl"
        if today_fn != self.current_filename:
            self.current_filename = today_fn

        entry = {
            "seq": self.seq,
            "ts_utc": now_utc.isoformat().replace('+00:00', 'Z'),
            "ts_kst": now_kst.isoformat(),
            "run_id": self.run_id,
            "engine": "OSS_BRAIN_MOCK",
            "event": event_type,
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
# BRAIN ENGINE
# ==========================================
class BrainSignalEngine:
    def __init__(self, config, brain_path="core/active_config/neuro_brain_state.pth"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if self.device.type == 'cuda':
            # [OPTIMIZATION] Prevent OOM by limiting memory usage & allowing fragmentation
            torch.cuda.set_per_process_memory_fraction(0.80, 0)
            print(f"[BRAIN] GPU Memory Limit: 80%")
        # FIXED: Match Training Config (Input: 64, Mode: MAX -> 8192 Nodes)
        self.brain = GaramNeuralBrain(input_size=64, mode="MAX").to(self.device)
        self.brain_path = Path(brain_path)
        self.optimizer = torch.optim.Adam(self.brain.parameters(), lr=0.0001)
        self.memory = []
        self.batch_size = 1 # Immediate learning for live demo
        
        # Feature Cache
        self.history = {} # sym -> [closes]
        self.window_size = 60 # 1 hour lookback for features
        
        # Load Model
        if self.brain_path.exists():
            try:
                self.brain.load_state_dict(torch.load(self.brain_path, map_location=self.device))
                print(f"[BRAIN] Loaded model from {self.brain_path}")
                self.brain.eval() # Start in eval mode
                self.last_brain_mtime = self.brain_path.stat().st_mtime
            except Exception as e:
                print(f"[BRAIN] Failed to load model: {e}. Starting fresh.")
                self.last_brain_mtime = 0
        else:
             print(f"[BRAIN] No existing model found at {self.brain_path}. Starting fresh.")
             self.last_brain_mtime = 0
        
        # [MEMORY] 3D Warp Drive Initialization
        self.memory_tensor = None
        self.memory_outcomes = None
        self.PHI = 1.61803398875
        self.last_trade_time = datetime.now()
        
        mem_path = Path("core/active_config/oss_episodic_memory.json")
        if mem_path.exists():
            try:
                with open(mem_path, "r") as f:
                    mem_data = json.load(f)
                
                # Filter valid 3D contexts
                valid_mems = [m for m in mem_data if len(m['context']) == 3]
                if valid_mems:
                    ctxs = [m['context'] for m in valid_mems]
                    outs = [m['outcome'] for m in valid_mems]
                    
                    self.memory_tensor = torch.tensor(ctxs, dtype=torch.float32).to(self.device)
                    self.memory_outcomes = torch.tensor(outs, dtype=torch.float32).to(self.device)
                    print(f"[BRAIN] 🌌 3D Warp Drive Ready: {len(self.memory_tensor)} memories loaded.")
                    self.last_mem_mtime = mem_path.stat().st_mtime
            except Exception as e:
                print(f"[BRAIN] Memory Load Error: {e}")
                self.last_mem_mtime = 0
        else:
            self.last_mem_mtime = 0

    def check_hot_reload(self):
        """Check if Brain or Memory file has changed and reload if necessary (Infinite Loop)"""
        try:
            # 1. Check Brain Weights
            if self.brain_path.exists():
                curr_mtime = self.brain_path.stat().st_mtime
                if curr_mtime > self.last_brain_mtime:
                    print(f"[SYNC] 🔄 Detected external Brain evolution! Reloading...")
                    try:
                        self.brain.load_state_dict(torch.load(self.brain_path, map_location=self.device))
                        self.brain.eval()
                        self.last_brain_mtime = curr_mtime
                        print(f"[SYNC] ✅ Brain Reloaded (Timestamp: {datetime.fromtimestamp(curr_mtime)})")
                    except Exception as e:
                        print(f"[SYNC] ⚠️ Brain Reload Failed: {e}")

            # 2. Check Memory Bank
            mem_path = Path("core/active_config/oss_episodic_memory.json")
            if mem_path.exists():
                curr_mem_mtime = mem_path.stat().st_mtime
                if curr_mem_mtime > self.last_mem_mtime:
                     print(f"[SYNC] 📚 Detected new experiences! Reloading Memory...")
                     try:
                        with open(mem_path, "r") as f:
                            mem_data = json.load(f)
                        valid_mems = [m for m in mem_data if len(m['context']) == 3]
                        if valid_mems:
                            ctxs = [m['context'] for m in valid_mems]
                            outs = [m['outcome'] for m in valid_mems]
                            self.memory_tensor = torch.tensor(ctxs, dtype=torch.float32).to(self.device)
                            self.memory_outcomes = torch.tensor(outs, dtype=torch.float32).to(self.device)
                            self.last_mem_mtime = curr_mem_mtime
                            print(f"[SYNC] ✅ 3D Memory Reloaded: {len(self.memory_tensor)} episodes.")
                     except Exception as e:
                         print(f"[SYNC] ⚠️ Memory Reload Failed: {e}")
        except Exception as e:
            print(f"[SYNC] Hot Reload Check Error: {e}")

    def on_trade(self):
        """Call this when a trade is executed to sate hunger"""
        self.last_trade_time = datetime.now()

    def update_history(self, sym, price):
        if sym not in self.history: self.history[sym] = []
        self.history[sym].append(price)
        if len(self.history[sym]) > self.window_size:
            self.history[sym].pop(0)

    def extract_features(self, sym):
        # SIMPLIFIED FEATURE EXTRACTION FOR LIVE PROTOTYPE
        # Must produce [1, 64] tensor to match model
        if len(self.history.get(sym, [])) < 20: return None
        
        closes = np.array(self.history[sym])
        
        # 1. RSI-like
        deltas = np.diff(closes)
        up = deltas[deltas > 0].sum()
        down = -deltas[deltas < 0].sum()
        rsi = 50.0 
        if down > 0: rsi = 100 * up / (up + down)
        elif up > 0: rsi = 100.0
        
        # 2. Z-Score
        ma = np.mean(closes)
        std = np.std(closes) + 1e-9
        z_score = (closes[-1] - ma) / std
        
        # 3. Volatility
        vol = std / ma
        
        # Create Feature Vector (64 dim)
        feats = np.zeros(64)
        feats[0] = rsi / 100.0
        feats[1] = np.clip(z_score, -3, 3) / 3.0
        feats[2] = np.clip(vol * 100, 0, 1)
        # Fill remainder with weak noise to prevent dead neurons? 
        # Or just zeros. Zeros is safer for untrained slots.
        
        return torch.tensor(feats, dtype=torch.float32).unsqueeze(0).to(self.device)

    def get_signal(self, sym, price):
        self.update_history(sym, price)
        feats = self.extract_features(sym)
        
        if feats is None: return "HOLD", 0.0, None

        with torch.no_grad():
            # 1. Brain Score (Reason)
            brain_out = self.brain(feats)
            brain_score = torch.tanh(brain_out).item() * 0.15
            
            # 2. Memory Score (Instinct - 3D Warp)
            memory_impact = 0.0
            if self.memory_tensor is not None and len(self.memory_tensor) > 0:
                # Context: RSI(0-1), Vol(0-1), Z(normalized) - approximate from feats
                # Feats: [rsi, z, vol, ...]
                # Memory Context in JSON was: [vol_ratio, body_pct, range_pct] 
                # Converting feats to match memory context approx:
                # range_pct ~ vol * z? Let's use feats directly if possible or map them.
                # Mismatch: 100man uses [vol_ratio, body_pct, range_pct], Live uses [rsi, z, vol]
                # We will map Live Feats to Context:
                # vol_ratio ~ feats[2] (vol) * 10? 
                # body_pct ~ feats[1] (z) * 0.01?
                # range_pct ~ feats[0] (rsi)?
                # To avoid noise, let's use the raw feats as query vector against similar dimensions if possible.
                # BUT memory_tensor has specific meaning. 
                # For now, let's just use the First 3 Dimensions of Feats as the key.
                # Assuming memory was trained on similar features or we construct a new query.
                query = feats[0, :3].unsqueeze(0) # [1, 3]
                
                # We need to ensure dims match. If memory_tensor is 3d, query must be 3d.
                if self.memory_tensor.shape[1] == 3:
                     # Calculate Distance
                     dists = torch.cdist(query, self.memory_tensor) # [1, N]
                     topk = torch.topk(dists, k=min(10, len(self.memory_tensor)), largest=False)
                     
                     indices = topk.indices[0]
                     d_vals = topk.values[0]
                     
                     relevant_outs = self.memory_outcomes[indices]
                     weights = 1.0 / (d_vals + 1e-6)
                     expected_pnl = torch.sum(relevant_outs * weights) / torch.sum(weights)
                     
                     # [GOLDEN RATIO] 
                     memory_impact = torch.tanh(expected_pnl * 20.0).item() * self.PHI
            
            # 3. Hunger Logic (Survival)
            hunger_boost = 0.0
            if self.last_trade_time:
                idle_minutes = (datetime.now() - self.last_trade_time).total_seconds() / 60.0
                if idle_minutes > 60:
                    hunger_boost = min(2.0, (idle_minutes - 60) * 0.01)
            
            # Final Score
            score = brain_score + memory_impact + hunger_boost
        
        decision = "HOLD"
        # Adjusted Thresholds for Live
        if score > 0.003: decision = "BUY"
        elif score < -0.001: decision = "SELL" # Active exit signal
        
        return decision, score, feats

    def learn(self, exit_pnl, entry_feats):
        """Called on Trade Exit"""
        if entry_feats is None: return
        
        # Store experience
        # [SATIETY] Feast Rewards
        scaled_pnl = exit_pnl
        if exit_pnl > 0.20:
             scaled_pnl *= 5.0 # Gluttony
             print(f"🦖 [FEAST] Rewarding Brain x5.0 for {exit_pnl*100:.1f}% win!")
        elif exit_pnl > 0.10:
             scaled_pnl *= 3.0 # Dinner
             print(f"🦁 [DINNER] Rewarding Brain x3.0 for {exit_pnl*100:.1f}% win!")
        elif exit_pnl < -0.03:
             scaled_pnl *= 2.0 # Discipline
             
        target = torch.tensor([scaled_pnl], dtype=torch.float32).to(self.device)
        self.memory.append({'feat': entry_feats, 'target': target})
        
        # Immediate Learning
        self.train_batch()

    def train_batch(self):
        if not self.memory: return

        self.brain.train()
        try:
            feat_batch = torch.cat([m['feat'] for m in self.memory])
            target_batch = torch.stack([m['target'] for m in self.memory]).unsqueeze(1) # Fix shape
            
            self.optimizer.zero_grad()
            output = self.brain(feat_batch)
            pred_ret = torch.tanh(output) * 0.15 
            
            loss = torch.nn.functional.mse_loss(pred_ret, target_batch)
            loss.backward()
            self.optimizer.step()
            
            print(f"[BRAIN] Trained on {len(self.memory)} samples. Loss: {loss.item():.6f}")
            self.memory = [] # Clear memory
            torch.cuda.empty_cache() # [OPTIMIZATION] Force GC
            
            # Save Updated Brain
            torch.save(self.brain.state_dict(), self.brain_path)
            # print(f"[BRAIN] 🧠 Brain Saved to {self.brain_path}") # Reduce Spam
            
        except Exception as e:
            print(f"[BRAIN] Training Error: {e}")
            traceback.print_exc()
        finally:
            self.brain.eval() # Return to eval mode

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def normalize_market_event(event):
    # Reuse previous logic or simplified version
    raw = event.payload if hasattr(event, 'payload') else (event if isinstance(event, dict) else {})
    sym = raw.get('symbol') or raw.get('ticker')
    ts = raw.get('ts') or raw.get('event_time')
    close = raw.get('close') or raw.get('price')
    
    if not sym or not ts or close is None: return None
    try: ts_obj = pd.Timestamp(ts)
    except: ts_obj = datetime.now()
    return {"symbol": str(sym), "ts": ts_obj, "close": float(close)}

def run_live_oss(args):
    run_id = str(uuid.uuid4())
    print(f"=== Starting OSS Neuro Brain Mock Trading ===")
    print(f"Run ID: {run_id}")
    
    config = load_config(args.config)
    logger = ShadowLogger(args.log_dir, run_id)
    
    # 1. Initialize Engines
    brain_eng = BrainSignalEngine(config)
    order_eng = OrderMock(config)
    
    # 2. Feed Setup
    src_path = config.get('live_source_path', "GARAM_Data/feed_live.jsonl") # Corrected default
    print(f"[FEED] Connect to {src_path}")
    
    consumer = FileTailConsumer(src_path)
    processor = RealtimeProcessor(consumer)
    
    market_snapshot = {}
    positions_meta = {} # sym -> {entry_feats: tensor, entry_price: float}
    
    print(f"Waiting for Data from {src_path}...")
    
    while True:
        now = datetime.now()
        event = processor.poll(now)
        
        if not event:
            time.sleep(0.1)
            continue
            
        norm_evt = normalize_market_event(event)
        if not norm_evt: continue
        
        sym = norm_evt['symbol']
        price = norm_evt['close']
        ts = norm_evt['ts']
        
        # Update Market State
        market_snapshot[sym] = {'close': price, 'price': price, 'ts': ts}
        
        # [INFINITE LOOP] Check for Brain/Memory Updates
        brain_eng.check_hot_reload()
        
        # 1. Brain Signal
        decision, score, feats = brain_eng.get_signal(sym, price)
        
        # 2. Execution Logic
        # BUY
        if decision == "BUY" and sym not in order_eng.positions:
            qty = int(5000000 / price) # Fixed 500k KRW sizing for mock
            if qty > 0:
                print(f"[BUY] {sym} @ {price} (Score: {score:.4f})")
                order_eng.positions[sym] = {'qty': qty, 'entry_price': price, 'entry_ts': ts}
                positions_meta[sym] = {'entry_feats': feats, 'entry_price': price}
                logger.log("ENTRY", {"ticker": sym, "price": price, "score": score}, 
                           equity=order_eng.get_equity(market_snapshot), dd=0, regime="NORMAL", active_pos=sym)
                brain_eng.on_trade() # Reset Hunger
        
        # SELL / EXIT
        elif sym in order_eng.positions:
            pos = order_eng.positions[sym]
            pnl = (price / pos['entry_price']) - 1
            
            # Brain Exit or Hard Stop/TakeProfit
            exit_signal = False
            reason = ""
            
            if decision == "SELL": 
                exit_signal = True; reason = "BRAIN_EXIT"
            # Hard stops
            if pnl < -0.02: exit_signal = True; reason = "STOP_LOSS" 
            if pnl > 0.05: exit_signal = True; reason = "TAKE_PROFIT"
            
            if exit_signal:
                print(f"[SELL] {sym} @ {price} (PnL: {pnl*100:.2f}%) [{reason}]")
                # LEARN HERE
                meta = positions_meta.get(sym)
                if meta:
                    print(f"[LEARN] Transplanting Experience for {sym}...")
                    brain_eng.learn(pnl, meta['entry_feats'])
                
                del order_eng.positions[sym]
                if sym in positions_meta: del positions_meta[sym]
                
                logger.log("EXIT", {"ticker": sym, "price": price, "pnl": pnl, "reason": reason}, 
                           equity=order_eng.get_equity(market_snapshot), dd=0, regime="NORMAL", active_pos="")

        processor.commit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/profile_micro_live.yaml")
    parser.add_argument("--log_dir", default="logs/oss_mock")
    args = parser.parse_args()
    
    run_live_oss(args)
