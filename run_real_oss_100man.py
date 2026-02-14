"""
[REAL] GARAM OSS 2.0 ULTRA (SHARING & ARCHIVING MODE)
- FIX: Zero-Signal Resilience (NaN robustness)
- FEATURE: Real-time Wisdom Archiving (Save every 10k mins)
- FEATURE: Shared Data Bridge (Link with Kiwoom Ingester)
"""

import sys
import os
import pandas as pd
import numpy as np
import torch
import glob
import json
# from scipy.spatial import cKDTree # [REMOVED] CPU Tree -> GPU Warp Drive
from pathlib import Path
from datetime import datetime
import time
import argparse # Added argparse
import multiprocessing # Added for CPU core count

PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))

# Configuration
# --- CONFIGURATION (Dynamic via Args) ---
DNA_PATH = Path("c:/garam/garam/core/active_config/tactical_dna.json")

# Default values (will be overwritten by args)
DEFAULT_CAPITAL = 10_000_000
DEFAULT_MODE = "STANDARD"
DEFAULT_SLIPPAGE = 5.0

def parse_arguments():
    parser = argparse.ArgumentParser(description="GARAM 2.1 Ultra OSS")
    parser.add_argument("--initial_capital", type=float, default=DEFAULT_CAPITAL)
    parser.add_argument("--mode", type=str, default=DEFAULT_MODE) # ULTRA_AGGRESSIVE
    parser.add_argument("--profit_target_mode", type=str, default="DYNAMIC_COMPOUND")
    parser.add_argument("--risk_guard_level", type=str, default="NONE") # MA60_STRUCTURAL
    parser.add_argument("--neuro_sizing", type=str, default="FIXED") # MAX_FORCE
    parser.add_argument("--slippage_model", type=str, default="REAL_0.05") # REAL_0.25 -> 25bps
    parser.add_argument("--gpu_usage", type=int, default=50) # Percent
    return parser.parse_known_args()[0]

ARGS = parse_arguments()

# Apply Configuration
CAPITAL = ARGS.initial_capital
MODE = ARGS.mode
RISK_GUARD = ARGS.risk_guard_level
SIZING_MODE = ARGS.neuro_sizing

# Parse Slippage (REAL_0.25 -> 25.0 BPS)
try:
    if "REAL_" in ARGS.slippage_model:
        val = float(ARGS.slippage_model.split("_")[1])
        SLIPPAGE_BPS = val * 100 # 0.25% -> 25 BPS
    else:
        SLIPPAGE_BPS = DEFAULT_SLIPPAGE
except:
    SLIPPAGE_BPS = DEFAULT_SLIPPAGE

# [REALISM CONSTANTS]
MAX_ORDER_VOLUME_RATIO = 0.10 # Max 10% of 1m volume
IMPACT_THRESHOLD = 0.01        # If >1% of volume, add slippage
MARKET_CLOSE_TIME = "15:20"
FEE_BPS = 5.0

FEE = FEE_BPS / 10000
SLIPPAGE = SLIPPAGE_BPS / 10000

print(f"[CONFIG] Capital: {CAPITAL:,.0f} | Mode: {MODE} | Guard: {RISK_GUARD}")
print(f"[CONFIG] Sizing: {SIZING_MODE} | Slippage: {SLIPPAGE_BPS} bps")

# [RESOURCE CONTROL]
# User Request: GPU Usage Dynamic
# CPU: Use 60% of available cores (reduced for stability)
cpu_count = multiprocessing.cpu_count()
target_threads = max(1, int(cpu_count * 0.6))
torch.set_num_threads(target_threads)

# GPU: Limit memory fraction
if torch.cuda.is_available():
    fraction = ARGS.gpu_usage / 100.0
    torch.cuda.set_per_process_memory_fraction(fraction, 0)
    print(f"[RESOURCE] GPU Limit: {fraction*100}% | CPU Threads: {target_threads}/{cpu_count}")

START_DATE = "20250601"
END_DATE = "20260206"

# Load Core Modules
from scripts.neural_brain import GaramNeuralBrain
try:
    from pipeline.backtest.run_alpha_robust import AlphaGenius_V2
except ImportError:
    sys.path.append(str(PROJECT_ROOT / "pipeline/backtest"))
    from run_alpha_robust import AlphaGenius_V2
    
try:
    from scripts.ollama_bridge import OllamaOracle
except Exception as e:
    print(f"⚠️ Ollama Bridge Initialization Warning: {e}")
    OllamaOracle = None

# [RESTORED] Ollama Active
# OllamaOracle = None # Force Disable (Removed)
# Avoid Character Corruption (Encoding Fix)
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

# START_DATE and END_DATE are configured above (lines 87-88)

CACHE_FILE = PROJECT_ROOT / "cache/market_matrix_8m.pkl"

def log(msg):
    # Safe text for Windows Console compatibility
    ts = datetime.now().strftime('%H:%M:%S')
    # Replace emojis with text symbols to prevent corruption
    safe_msg = str(msg).replace("🛡️", "[GARD]").replace("🚀", "[GO]").replace("🔥", "[HOT]").replace("✅", "[OK]").replace("❌", "[NO]")
    formatted = f"[{ts}] {safe_msg}"
    
    print(formatted)
    sys.stdout.flush()
    
    try:
        with open(PROJECT_ROOT / "logs/oss_wisdom_bridge_REAL_V2.log", "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception as e:
        print(f"[LOG ERROR] Could not write to log file: {e}")

def archive_wisdom(idx, equity, trade_logs, brain_params):
    """Save mid-progress results for the Commander (Archiving)"""
    archive_dir = PROJECT_ROOT / "results/oss_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # [Fix] Handle complex types (dict/list) in brain_params
    serialized_brain = {}
    for k, v in brain_params.items():
        if isinstance(v, (dict, list)):
            serialized_brain[k] = v
        else:
            try:
                serialized_brain[k] = float(v)
            except:
                serialized_brain[k] = str(v)
    
    report = {
        "progress_idx": idx,
        "equity": float(equity),
        "total_trades": len(trade_logs),
        "recent_trades": trade_logs[-5:], # Last 5
        "brain_state": serialized_brain
    }
    
    # Save Snapshot
    with open(archive_dir / f"wisdom_snapshot_{idx}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    
    # Update latest summary
    with open(PROJECT_ROOT / "config/evolved_wisdom.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
        
    log(f"Wisdom Archived at index {idx}. Total Trades: {len(trade_logs)}")

def process_one_file(args):
    f, s_dt, e_dt = args
    if f.stat().st_size < 1_000_000: return None
    sym = f.stem
    if sym == "desktop": return None
    try:
        df = pd.read_csv(f)
        df.columns = [c.lower() for c in df.columns]
        date_col = "date" if "date" in df.columns else "일자"
        if date_col not in df.columns: return None
        df["dt"] = pd.to_datetime(df[date_col].astype(str), format="%Y%m%d%H%M%S", errors='coerce')
        if df["dt"].isnull().all():
            df["dt"] = pd.to_datetime(df[date_col].astype(str), format="%Y%m%d%H%M", errors='coerce')
        df = df.dropna(subset=["dt"]).drop_duplicates(subset=["dt"]).set_index("dt").sort_index()
        mask = (df.index >= s_dt) & (df.index <= e_dt)
        df_sliced = df.loc[mask]
        if not df_sliced.empty:
            df_sliced = df_sliced.copy()
            df_sliced.loc[:, 'symbol'] = sym
            for col in ['close', 'volume']:
                df_sliced.loc[:, col] = pd.to_numeric(df_sliced[col], errors='coerce')
            return df_sliced[['close', 'volume', 'symbol']]
    except:
        pass
    return None

def run_real_test():
    log("Garam 2.0 Ultra (Bridge Mode) Starting...")
    
    # 1. GPU 뇌 초기화 (Integration with Trained Mind)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    brain = GaramNeuralBrain(input_size=64, mode="MAX").to(device)
    
    # Load Pre-Trained Weights
    BRAIN_PATH = PROJECT_ROOT / "core/active_config/neuro_brain_state_REAL_V2.pth"
    if BRAIN_PATH.exists():
        try:
            brain.load_state_dict(torch.load(BRAIN_PATH, map_location=device))
            brain.eval()
            log(f"🧠 [INTEGRATION] Pre-Trained Brain Loaded: {BRAIN_PATH}")
        except Exception as e:
            log(f"⚠️ Failed to load brain: {e}")
    else:
        log("⚠️ No Pre-Trained Brain Found. Wiping memory...")

    # [PHASE 4] Load Episodic Memory (The Soul of OSS)
    # This stores the fierce debates and comparisons of the past.
    MEMORY_PATH = PROJECT_ROOT / "core/active_config/oss_episodic_memory.json"
    brain.memory_bank = [] # Initialize Attribute
    if MEMORY_PATH.exists():
        try:
            with open(MEMORY_PATH, "r") as f:
                brain.memory_bank = json.load(f)
            log(f"📚 [MEMORY] Loaded {len(brain.memory_bank)} past episodes (Wisdom).")
        except Exception as e:
            log(f"⚠️ Memory Load Fail: {e}")
            brain.memory_bank = []
    else:
        log("🌱 No episodic memory found. Starting a new life.")

    # [OPTIMIZATION] GPU 3D Warp Drive (Memory Space)
    # CPU: "Pushing Material" -> GPU: "Warp Search"
    memory_tree = None
    last_mem_mtime = 0
    last_brain_mtime = 0
    
    if BRAIN_PATH.exists():
        last_brain_mtime = BRAIN_PATH.stat().st_mtime
    
    if brain.memory_bank:
        try:
             # GPU Tensor Logic (Already implemented but ensuring reloading works)
             mem_contexts = [m['context'] for m in brain.memory_bank]
             valid_contexts = [c for c in mem_contexts if len(c) == 3]
             if valid_contexts:
                 brain.memory_tensor = torch.tensor(valid_contexts, dtype=torch.float32).to(brain.device)
                 # We also need outcomes for GPU calc
                 mem_outcomes = [m['outcome'] for m in brain.memory_bank if len(m['context']) == 3]
                 brain.memory_outcomes = torch.tensor(mem_outcomes, dtype=torch.float32).to(brain.device)
                 log(f"🌌 [MEMORY] Uploading {len(brain.memory_tensor)} memories to GPU VRAM...")
                 log(f"🌌 [MEMORY] 3D Space Ready. VRAM Usage: {len(valid_contexts)*3*4/1024:.1f} KB")  
                 
             if MEMORY_PATH.exists():
                 last_mem_mtime = MEMORY_PATH.stat().st_mtime
                 
        except Exception as e:
             log(f"⚠️ GPU Memory Upload Failed: {e}")

    # [INFINITE LOOP] Hot Reload Function
    def check_hot_reload():
        nonlocal last_brain_mtime, last_mem_mtime
        try:
            # 1. Brain
            if BRAIN_PATH.exists():
                curr = BRAIN_PATH.stat().st_mtime
                if curr > last_brain_mtime:
                    try:
                        brain.load_state_dict(torch.load(BRAIN_PATH, map_location=device))
                        brain.eval()
                        last_brain_mtime = curr
                        log(f"🔄 [SYNC] Brain Evolved! Reloaded weights from disk.")
                    except: pass
            
            # 2. Memory
            if MEMORY_PATH.exists():
                curr = MEMORY_PATH.stat().st_mtime
                if curr > last_mem_mtime:
                    try:
                        with open(MEMORY_PATH, "r") as f:
                            new_mem = json.load(f)
                        if len(new_mem) > len(brain.memory_bank):
                            brain.memory_bank = new_mem
                            # Re-upload to GPU
                            mem_contexts = [m['context'] for m in brain.memory_bank]
                            valid_contexts = [c for c in mem_contexts if len(c) == 3]
                            if valid_contexts:
                                brain.memory_tensor = torch.tensor(valid_contexts, dtype=torch.float32).to(brain.device)
                                mem_outcomes = [m['outcome'] for m in brain.memory_bank if len(m['context']) == 3]
                                brain.memory_outcomes = torch.tensor(mem_outcomes, dtype=torch.float32).to(brain.device)
                            last_mem_mtime = curr
                            log(f"📚 [SYNC] New Experiences Absorbed! Total: {len(brain.memory_bank)}")
                    except: pass
        except: pass
    learning_window = [] # 실시간 학습 버퍼 초기화
    
    # [PHASE 4] SYSTEM SELF-CHECK (Pre-Flight Diagnostic)
    def perform_system_check():
        log("🔍 [DIAGNOSTIC] Performing System Self-Check...")
        errors = []
        
        # 1. GPU Check
        if torch.cuda.is_available():
            log(f"   [PASS] GPU Detected: {torch.cuda.get_device_name(0)}")
        else:
            log("   [WARN] GPU NOT Detected. Running on CPU (Slow).")
            # Not a fatal error, but warning.
            
        # 2. Brain Weight Integrity Check
        try:
            # [FIX] Architecture is 'entry' (Sequential) -> Linear is at index 0
            w_std = brain.entry[0].weight.std().item()
            if w_std < 0.001:
                errors.append(f"Brain Weights are flat (std={w_std:.6f}). Potentially dead neuron.")
            else:
                log(f"   [PASS] Brain Vital Signs OK (Weight Std: {w_std:.4f})")
        except Exception as e:
            errors.append(f"Brain Check Failed: {e}")
            
        # 3. Memory File Access Check
        try:
            with open(MEMORY_PATH, "a") as f:
                pass
            log(f"   [PASS] Memory File Writable: {MEMORY_PATH}")
        except Exception as e:
            errors.append(f"Memory File Write Denied: {e}")
            
        if errors:
            log("❌ [FAIL] System Check Candidates Failed:")
            for err in errors:
                log(f"   - {err}")
            return False
        
        log("✅ [PASS] All Systems Operational. Launching Engine.")
        return True

    if not perform_system_check():
        log("🛑 [ABORT] Mission Aborted due to System Check Failure.")
        return

    # 1.5 Alien Intelligence (Ollama)
    oracle = None
    if OllamaOracle:
        oracle = OllamaOracle(model="llama3.1", logger=log) 

    # 2. 데이터 로드 (Shared with Ingester & Cached)
    if CACHE_FILE.exists():
        log(f"Loading Market Matrix from Cache: {CACHE_FILE.name}")
        with open(CACHE_FILE, 'rb') as f:
            cached_data = pd.read_pickle(f)
        closes = cached_data['closes']
        volumes = cached_data['volumes']
        log(f"Cache Loaded: {closes.shape[1]} symbols active.")
    else:
        log("No Cache Found. Re-building Market Matrix from CSVs...")
        data_dir = PROJECT_ROOT / "GARAM_Data/history/minute"
        files = list(data_dir.glob("*.csv"))
        log(f"Data Bridge: Scanning {len(files)} files for valid data (>1MB)...")
        
        from multiprocessing import Pool, cpu_count
        log(f"Turbo Data Bridge: Parallel Scanning {len(files)} files...")
        
        s_dt, e_dt = pd.to_datetime(START_DATE), pd.to_datetime(END_DATE)
        pool_args = [(f, s_dt, e_dt) for f in files]
        with Pool(processes=int(cpu_count() * 0.8)) as pool:
            results = pool.map(process_one_file, pool_args)
            all_data = [r for r in results if r is not None]
        
        log(f"Data Sync Complete. Collected: {len(all_data)} chunks")
        
        if not all_data:
            log("CRITICAL ERROR: No data collected from any CSV file!")
            return

        log(f"Building Market Matrix from {len(all_data)} chunks...")
        full_df = pd.concat(all_data)
        closes = full_df.pivot(columns='symbol', values='close').ffill().astype(np.float32)
        volumes = full_df.pivot(columns='symbol', values='volume').fillna(0).astype(np.float32)
        
        if closes.empty:
            log("CRITICAL ERROR: Market Matrix is EMPTY after pivot!")
            return
            
        with open(CACHE_FILE, 'wb') as f:
            pd.to_pickle({'closes': closes, 'volumes': volumes}, f)

    # [RESIDENT DATA] Oracle Calculation (The Answer Key)
    log("🔮 ORACLE: Generating Answer Key (Future 120m Max Return)...")
    indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=120)
    future_max = closes.rolling(window=indexer).max()
    future_ret_120 = (future_max / closes) - 1.0
    oracle_buy_mask = (future_ret_120 > 0.03) 
    oracle_super_mask = (future_ret_120 > 0.07) # Target for 10% daily contribution
    log(f"🔮 ORACLE: Found {oracle_buy_mask.sum().sum()} alpha & {oracle_super_mask.sum().sum()} super-alpha points.")

    # --- INFINITE TRAINING LOOP ---
    epoch = 0
    # Run only 1 Epoch for specific period test
    # Run 4 Epochs for Elite Training
    max_epochs = 4
    for epoch in range(1, max_epochs + 1):
        epoch += 1
        log(f"\n 🔥 [EPOCH {epoch}] Starting New Training Cycle...")
        
        alpha = AlphaGenius_V2(mode=MODE, risk_guard=RISK_GUARD)
        log("Neuro Brain: Calculating V3 Signals with Shared Data...")
        signals = alpha.calculate_signals(closes, volumes)
    
        # Load Wisdom (Brain State)
        WISDOM_FILE = PROJECT_ROOT / "results/oss_archive/wisdom_snapshot_FINAL.json"
        if WISDOM_FILE.exists():
            try:
                with open(WISDOM_FILE, 'r', encoding='utf-8') as f:
                    wisdom = json.load(f)
                log(f"🧠 Wisdom Found: Previous Run made {wisdom.get('total_trades', 0)} trades. (Equity: {wisdom.get('equity'):,.0f})")
            except:
                log("⚠️ Wisdom File Exists but corrupted. Starting Fresh.")

        # [EVOLUTION] Load Genes (Persistent Memory)
        GENE_FILE = PROJECT_ROOT / "core/active_config/evolved_genes.json"
        if GENE_FILE.exists():
            try:
                 with open(GENE_FILE, 'r') as f:
                     loaded_genes = json.load(f)
                 alpha.params.update(loaded_genes)
                 log(f"🧬 Evolved Genes Loaded: {loaded_genes}")
            except:
                 log("⚠️ Gene File corrupted. Using raw DNA.")

        cash = float(CAPITAL)
        log(f"💎 [TRUTH] Capital Initialized: {cash:,.0f} KRW")
        log(f"📶 [TRUTH] Signals Detected: {len(signals)} (Ready to engage)")
        
        positions = {} 
        equity_curve = []
        equity_curve = []
        trade_logs = []
        last_trade_time = None # [HUNGER] Track starvation time
        
        # [OSS AUTONOMOUS LEARNING] Self-Training System
        brain.train()  # 학습 모드
        optimizer = optim.Adam(brain.parameters(), lr=0.0001) # FIXED: 0.001 -> 0.0001 for 8192 Nodes (Stability)
        trade_buffer = []  # Recent trades for learning
        training_count = 0
        batch_memory = [] # [BATCH LEARNING] Buffer

        # [OSS INTERNAL] Batch Learning Logic
        def process_batch_learning(pos_data, exit_ret_val):
            nonlocal batch_memory, training_count
            
            # [Reward Engineering] Phase 3: Time-Weighted Reward
            # Encourage Holding for Big Trends (Overnight)
            scaled_ret = exit_ret_val
            
            # [PHASE 4] Memory Banking for Events (Raw Context)
            event_context = pos_data.get('event_context', {})
            if event_context:
                 # Only remember significant outcomes
                 if abs(scaled_ret) > 0.01: # FIXED: Was 0.05 (missed 90% of trades)
                      log(f"🧠 [MEMORY] Storing Raw Context: {event_context} -> PnL: {exit_ret_val*100:.1f}%")
                      
                      # [FIX] Store to Brain's Memory Bank & Persist
                      new_memory = {
                          'context': [event_context['vol_ratio'], event_context['body_pct'], event_context['range_pct']],
                          'outcome': float(exit_ret_val),
                          'ts': pos_data.get('entry_time').strftime("%Y-%m-%d %H:%M:%S")
                      }
                      brain.memory_bank.append(new_memory)
                      
                      # Immediate Save Memory Bank to JSON
                      for attempt in range(3):
                          try:
                              with open(PROJECT_ROOT / "core/active_config/oss_episodic_memory.json", "w") as f:
                                  # Convert numpy array to list for JSON serialization if needed
                                  # But here 'context' is list of floats, so fine.
                                  json.dump(brain.memory_bank[-5000:], f) # Keep last 5000 memories (Increased from 2000)
                              break # Success
                          except Exception as e:
                              time.sleep(0.1)
                              if attempt == 2:
                                  log(f"⚠️ Memory Save Error (Final): {e}")
            
            # Let's use simple logic: If return > 5%, assume good hold.
            # But the user wants explicit DAY bonus.
            # We need to pass exit_time to this function.
            
            # Since we can't easily change signature everywhere without breaking things, 
            # let's infer days from 'entry_time' if available, comparing to global 'ts' (which is not available here).
            # WAIT. We can pass 'duration_days' in pos_data before calling this.
            
            duration_days = pos_data.get('duration_days', 0.0)
            time_bonus = 1.0 + (duration_days * 0.5) # +50% per day bonus
            
            scaled_ret *= time_bonus # Scale by time
            
            if exit_ret_val < -0.03:
                  scaled_ret *= 2.0  # Double penalty for big loss (-6%)
            elif exit_ret_val > 0.20:
                  scaled_ret *= 5.0 # [GLUTTONY] Massive Reward for Super Win (+20%)
                  log(f"🦖 [FEAST] ATE MASSIVELY! (+{exit_ret_val*100:.1f}%) -> Reward x5.0")
            elif exit_ret_val > 0.10:
                  scaled_ret *= 3.0 # [SATIETY] Great Meal (+10%)
                  log(f"🦁 [DINNER] Ate Well. (+{exit_ret_val*100:.1f}%) -> Reward x3.0")
            elif exit_ret_val > 0.05:
                  scaled_ret *= 2.0  # Double reward for big win (+5%) * Time Bonus
            elif abs(exit_ret_val) < 0.005:
                  scaled_ret -= 0.005 # Small penalty for chop

            # [DEBUG] Verify function is called
            # log(f"🔍 process_batch_learning called | has_entry_features: {'entry_features' in pos_data}")
            
            if 'entry_features' in pos_data:
                # [MEMORY OPTIMIZATION] Store on CPU to avoid VRAM bloat
                batch_memory.append({ 
                    'feat': pos_data['entry_features'].cpu(), 
                    'target': torch.tensor([scaled_ret], dtype=torch.float32, device='cpu') 
                })
                # log(f"📊 Batch Size: {len(batch_memory)}/8 (Target: {scaled_ret:.4f})")
                
                if len(batch_memory) >= 8: # FIXED: Was 32 (never filled due to circuit breaker)
                    try:
                        # Move batch to GPU for training
                        feat_batch = torch.stack([m['feat'] for m in batch_memory]).to(brain.device).squeeze(1)
                        target_batch = torch.cat([m['target'] for m in batch_memory]).to(brain.device).unsqueeze(1)
                        
                        optimizer.zero_grad()
                        output = brain(feat_batch)
                        pred_ret = torch.tanh(output) * 0.15
                        
                        loss = torch.nn.functional.mse_loss(pred_ret, target_batch)
                        loss.backward()
                        optimizer.step()
                        
                        # Clear GPU Cache
                        torch.cuda.empty_cache()
                        
                        # [CRITICAL] Immediate Save Strategy
                        # Save brain state after every batch to prevent data loss
                        try:
                            torch.save(brain.state_dict(), BRAIN_PATH)
                            # Verify save
                            if BRAIN_PATH.exists():
                                from datetime import datetime
                                mod_time = datetime.fromtimestamp(BRAIN_PATH.stat().st_mtime)
                                log(f"💾 Brain Saved: {mod_time.strftime('%H:%M:%S')}")
                        except Exception as save_err:
                            log(f"⚠️ Brain Save Error: {save_err}")
                        
                        accum_loss = loss.item()
                        training_count += len(batch_memory)
                        batch_memory = [] 
                        if training_count % 8 == 0: # Log every batch
                             log(f"🧠 OSS BATCH LEARN #{training_count}: Loss={accum_loss:.6f}")
                    except Exception as e:
                        log(f"⚠️ Batch Learn Error: {e}")
                        batch_memory = []

        log("\n🤖 OSS AUTONOMOUS MODE: Self-learning ACTIVATED (Batch Size: 32)")
        log("   - Neural network in TRAIN mode")
        log("   - Optimizer: Adam (lr=0.0001)")
        log("   - Learning from every trade outcome (High-Performance GPU Batching)\n")
        
        # [DATA VALIDITY CHECK]
        log("🔍 Data Inspection (GPU Upload Check):")
        log(f"   - Close Price Range: {closes.min().min():.0f} ~ {closes.max().max():.0f}")
        log(f"   - Volume Activity: {(volumes > 0).sum().sum()} bars with volume")
        log(f"   - Market Matrix Shape: {closes.shape} (Time x Symbols)")
        
        # Pre-initialize for logging
        dyn_th = 5.0
        dyn_stop = 0.02
        last_minute_equity = float(CAPITAL) # For Volatility Guard
        halt_entries_until = None # For cooling down after shock

        
        # [LEARNING ENGINE] Strategy Performance Tracker - INSTANT LEARNING
        strategy_weights = {'1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0}

        for idx, ts in enumerate(closes.index):
            if idx < 100: continue
            
            if idx % 10000 == 0:
                equity = cash + sum(pos['qty'] * closes.loc[ts, sym] for sym, pos in positions.items())
                archive_wisdom(idx, equity, trade_logs, {"threshold": dyn_th, "stop": dyn_stop, "weights": strategy_weights})

            curr_pxs = closes.loc[ts]
            curr_sig = signals.loc[ts]
            hour = (idx % 381) / 381 

            # [NEURO] INDIVIDUAL PROCESSING (Batch Inference)
            active_syms = closes.columns
            n_sym = len(active_syms)
            
            f_hour = torch.full((n_sym, 1), hour, device=brain.device)
            f_cash = torch.full((n_sym, 1), cash/CAPITAL, device=brain.device)
            f_pos  = torch.full((n_sym, 1), len(positions)/5.0, device=brain.device)
            
            state = alpha.last_state_map
            def get_torch_col(name, norm=1.0):
                s = state[name].loc[ts].fillna(0).values 
                return torch.tensor(s, dtype=torch.float32, device=brain.device).unsqueeze(1) / norm

            f_rsi = get_torch_col('rsi', 100.0)
            f_width = get_torch_col('width_z', 1.0)
            f_vol = get_torch_col('vol_ratio', 10.0)
            f_trend = get_torch_col('trend_15m', 1.0)
            f_ma = get_torch_col('ma_dist', 0.1)
            f_whale = get_torch_col('whale', 1.0)
            f_squeeze = get_torch_col('squeeze', 1.0)
            f_pad = torch.zeros((n_sym, 54), device=brain.device) 
            
            feat_batch = torch.cat([f_hour, f_cash, f_pos, f_rsi, f_width, f_vol, f_trend, f_ma, f_whale, f_squeeze, f_pad], dim=1)
            
            brain.eval()
            with torch.no_grad():
                out_batch = brain(feat_batch).cpu().numpy() 
                
            dyn_th_vals = 4.0 + np.tanh(out_batch[:, 0]) * 1.5
            dyn_stop_vals = 0.03 + np.tanh(out_batch[:, 1]) * 0.01
            
            dyn_th_series = pd.Series(dyn_th_vals, index=active_syms)
            dyn_stop_series = pd.Series(dyn_stop_vals, index=active_syms)
            
            dyn_th = dyn_th_series.mean() 

            current_equity_est = cash + sum(pos['qty'] * curr_pxs.get(sym, pos['entry_px']) for sym, pos in positions.items())
            global_roi = (current_equity_est / CAPITAL - 1) * 100
            is_circuit_break = (global_roi < -7.0) and (idx % 1000 < 950) 
            
            if is_circuit_break and idx % 100 == 0:
                log(f"⚠️ CIRCUIT BREAKER ACTIVE (ROI: {global_roi:.2f}%) - Halting Entries")
            
            if idx % 500 == 0:
                state_label = "🔥 PROFIT FOCUS" if dyn_th < 5.5 else "🛡️ SAFETY FOCUS"
                current_equity = cash + sum(pos['qty'] * curr_pxs.get(sym, pos['entry_px']) for sym, pos in positions.items())
                
                # [RISK] Real-time Volatility Guard (1-min Shock)
                if idx % 1 == 0: # Check every minute
                    min_ret = (current_equity / last_minute_equity - 1.0)
                    if min_ret < -0.01: # -1% drop in 1 minute
                        log(f"⚡ VOLATILITY SHOCK DETECTED: {min_ret*100:.2f}% drop in 1m. HALTING ENTRIES.")
                        halt_entries_until = idx + 60 # Halt for 60 mins
                        # Tighten stops for all positions
                        dyn_stop_series[:] = 0.015 
                    last_minute_equity = current_equity

                state_label = "🔥 PROFIT FOCUS" if dyn_th < 5.5 else "🛡️ SAFETY FOCUS"
                if halt_entries_until and idx < halt_entries_until:
                    state_label = "⛔ HALTED (Shock)"
                th_mean, th_min, th_max = dyn_th_series.mean(), dyn_th_series.min(), dyn_th_series.max()
                st_mean, st_min, st_max = dyn_stop_series.mean(), dyn_stop_series.min(), dyn_stop_series.max()
                log(f"OSS Adaptive State: {state_label} (Th:{th_mean:.2f}[{th_min:.1f}~{th_max:.1f}], SL:{st_mean*100:.1f}%[{st_min*100:.1f}~{st_max*100:.1f}%]) | Pos:{len(positions)}")

            # [REAL TIME CLOCK]
            is_near_close = ts.strftime("%H:%M") >= "15:00"
            is_market_closed = ts.strftime("%H:%M") >= MARKET_CLOSE_TIME

            # [TACTICAL] Advanced Exit Logic
            for sym, pos in list(positions.items()):
                px = curr_pxs.get(sym, pos['entry_px'])
                if pd.isna(px) or px == 0: continue
                
                ret = (px / pos['entry_px']) - 1.0
                score = curr_sig.get(sym, 0.0)
                entry_score = pos.get('entry_score', score)
                my_stop = dyn_stop_series.get(sym, 0.03) 
                
                # [EXIT] Momentum Decay (Relative Strength Drop)
                # If score drops by 2.0+ from entry, the edge is gone.
                if (entry_score - score) >= 2.0:
                     exit_px = px * (1 - SLIPPAGE)
                     exit_ret = (exit_px/pos['entry_px'])-1
                     cash += pos['qty'] * exit_px * (1 - FEE)
                     trade_log = {'ts': str(ts), 'sym': sym, 'pnl': float(exit_ret), 'reason': 'MOMENTUM_DECAY', 'strategy': pos.get('strategy', 'Unknown')}
                     trade_logs.append(trade_log)
                     process_batch_learning(pos, exit_ret) # [LEARN]
                     del positions[sym]
                     log(f"🥀 MOMENTUM DECAY: {sym} | Score {entry_score:.1f} -> {score:.1f} | PnL: {exit_ret*100:.2f}%")
                     continue
                my_stop = dyn_stop_series.get(sym, 0.03) 
                
                # [실전] Market Close Protocol (Autonomous Decision)
                if is_market_closed:
                    # [BRAIN DECISION] Should we hold overnight?
                    # Rule: Strong Score (>= 8.5) AND (Strong Momentum OR Big Profit)
                    rsi_val = alpha.last_state_map['rsi'].loc[ts].get(sym, 50)
                    
                    should_overnight = (score >= 8.5) and (rsi_val > 60 or ret > 0.10)
                    
                    if should_overnight:
                        if idx % 5 == 0: log(f"🌙 OVERNIGHT HOLD: {sym} | Score {score:.1f}, RSI {rsi_val:.1f}, PnL {ret*100:.1f}%")
                        continue # Skip Exit
                    else:
                        exit_px = px * (1 - SLIPPAGE)
                        exit_ret = (exit_px/pos['entry_px'])-1
                        cash += pos['qty'] * exit_px * (1 - FEE)
                        trade_logs.append({'ts': str(ts), 'sym': sym, 'pnl': float(exit_ret), 'reason': 'MARKET_CLOSE'})
                        process_batch_learning(pos, exit_ret) # [LEARN]
                        del positions[sym]
                        log(f"🕗 MARKET CLOSE EXIT: {sym} | PnL: {exit_ret*100:.2f}% | Weak Score/Mom")
                        continue

                # [CONVICTION HOLD] Shakeout Defense (개미 털기 방어)
                curr_vols = volumes.loc[ts]
                vol_ratio = curr_vols.get(sym, 0) / (volumes.iloc[idx-20:idx][sym].mean() + 1e-9)
                
                # If high conviction score but price drops on LOW volume, it's a potential shakeout
                is_shakeout_possibility = (score >= 8.5) and (vol_ratio < 1.5)
                if is_shakeout_possibility and ret < 0:
                    my_stop *= 1.5 # Wider stop for heroes (e.g. 4.5% instead of 3%)
                    if idx % 10 == 0: log(f"🛡️ SHAKEOUT DEFENSE: Holding {sym} with conviction (Score: {score:.1f}, VolRatio: {vol_ratio:.1f}x)")
                # Calculate duration for reward
                start_ts = pos.get('entry_time', ts)
                duration_days = (ts - start_ts).total_seconds() / 86400.0
                pos['duration_days'] = duration_days

                # [OSS DYNAMIC] Self-Learning Exit Logic
                if score < 0.5: # Brain says "SELL NOW"
                    exit_px = px * (1 - SLIPPAGE)
                    exit_ret = (exit_px/pos['entry_px'])-1
                    cash += pos['qty'] * exit_px * (1 - FEE)
                    trade_log = {'ts': str(ts), 'sym': sym, 'pnl': float(exit_ret), 'reason': 'OSS_DYNAMIC', 'strategy': pos.get('strategy', 'Unknown')}
                    trade_logs.append(trade_log)
                    
                    # [OSS LEARNS] Batch Training Accumulation
                    process_batch_learning(pos, exit_ret)
                    
                    del positions[sym]
                    log(f"OSS Trade Exit: {sym} | [NO] LOSS ({ret*100:.2f}%) | Cash: {cash:,.0f} | Held: {duration_days:.2f} days")
                    continue

                if ret > 0.10 and score < 5.0:
                     exit_px = px * (1 - SLIPPAGE)
                     exit_ret = (exit_px/pos['entry_px'])-1
                     cash += pos['qty'] * exit_px * (1 - FEE)
                     trade_log = {'ts': str(ts), 'sym': sym, 'pnl': float(exit_ret), 'reason': 'TAKE_PROFIT_WEAK', 'strategy': pos.get('strategy', 'Unknown')}
                     trade_logs.append(trade_log)
                     process_batch_learning(pos, exit_ret)
                     del positions[sym]
                     log(f"OSS Trade Exit: {sym} | [OK] WIN ({ret*100:.2f}%) | Cash: {cash:,.0f} | Held: {duration_days:.2f} days")
                     continue
                
                # [PROFIT LOCK] Trailing stop for 10% target
                if ret > 0.05:
                     pos['high_mark'] = max(pos.get('high_mark', 0), ret)
                     # If score is still strong, stay for more meat! (Eat well)
                     if score > 8.0:
                          # Very loose trailing for strong trends
                          trail_dist = 0.04 if ret > 0.10 else 0.03
                     else:
                          # Tighter trailing for weakening momentum
                          trail_dist = 0.02
                          
                     if (pos['high_mark'] - ret) > trail_dist and ret > 0.03:
                         exit_px = px * (1 - SLIPPAGE)
                         exit_ret = (exit_px/pos['entry_px'])-1
                         cash += pos['qty'] * exit_px * (1 - FEE)
                         trade_log = {'ts': str(ts), 'sym': sym, 'pnl': float(exit_ret), 'reason': 'PROFIT_LOCK', 'strategy': pos.get('strategy', 'Unknown')}
                         trade_logs.append(trade_log)
                         process_batch_learning(pos, exit_ret)  # [LEARN]
                         del positions[sym]
                         log(f"🔒 PROFIT LOCKED: {sym} | Win: {ret*100:.2f}% (Peak: {pos['high_mark']*100:.1f}%) | Holding for Meat: {score > 8.0}")
                         continue

                # [CLIMAX EXIT] Exit at the peak of a short squeeze (Garam Predator)
                if ret > 0.07 and vol_ratio > 10.0 and alpha.last_state_map['rsi'].loc[ts, sym] > 85:
                     exit_px = px * (1 - SLIPPAGE)
                     exit_ret = (exit_px/pos['entry_px'])-1
                     cash += pos['qty'] * exit_px * (1 - FEE)
                     trade_log = {'ts': str(ts), 'sym': sym, 'pnl': float(exit_ret), 'reason': 'CLIMAX_EXIT', 'strategy': pos.get('strategy', 'Unknown')}
                     trade_logs.append(trade_log)
                     process_batch_learning(pos, exit_ret)  # [LEARN]
                     del positions[sym]
                     log(f"🚀 CLIMAX EXIT: {sym} | Captured peak at {ret*100:.2f}% | VolRatio: {vol_ratio:.1f}x")
                     continue

                # 1. Trailing Stop Activation (Only if > 3% profit)
                if high_mark > 0.03:
                    # Dynamic Trail Distance: 
                    # If huge spike (>10%), tight trail (1.5%)
                    # If moderate trend (3~10%), standard trail (2.5%)
                    trail_dist = 0.015 if high_mark > 0.10 else 0.025
                    
                    if (high_mark - ret) > trail_dist:
                         exit_px = px * (1 - SLIPPAGE)
                         exit_ret = (exit_px/pos['entry_px'])-1
                         cash += pos['qty'] * exit_px * (1 - FEE)
                         trade_log = {'ts': str(ts), 'sym': sym, 'pnl': float(exit_ret), 'reason': 'TRAILING_STOP', 'strategy': pos.get('strategy', 'Unknown')}
                         trade_logs.append(trade_log)
                         process_batch_learning(pos, exit_ret)
                         del positions[sym]
                         log(f"📉 TRAILING STOP: {sym} | Locked in {ret*100:.2f}% (Peak: {high_mark*100:.1f}%)")
                         continue

                # 2. Climax Selling (RSI Overbought + Volume Spike)
                if ret > 0.07 and vol_ratio > 8.0 and alpha.last_state_map['rsi'].loc[ts, sym] > 80:
                     exit_px = px * (1 - SLIPPAGE)
                     exit_ret = (exit_px/pos['entry_px'])-1
                     cash += pos['qty'] * exit_px * (1 - FEE)
                     trade_log = {'ts': str(ts), 'sym': sym, 'pnl': float(exit_ret), 'reason': 'CLIMAX_TOP', 'strategy': pos.get('strategy', 'Unknown')}
                     trade_logs.append(trade_log)
                     process_batch_learning(pos, exit_ret)
                     del positions[sym]
                     log(f"🚀 CLIMAX EXIT: {sym} | Captured peak at {ret*100:.2f}% | VolRatio: {vol_ratio:.1f}x")
                     continue

            
            # [TACTICAL] Advanced Entry Logic
            MAX_POSITIONS = 5 # Fixed High-End Portfolio (20% each)
            
            is_halted = (halt_entries_until and idx < halt_entries_until)
            
            if cash > (CAPITAL * 0.15) and not is_near_close and not is_halted:
                # 1. New Entry - Concentrated for Statistical Edge
                if len(positions) < MAX_POSITIONS and not is_circuit_break:
                    valid_sigs = curr_sig.dropna()
                    # Filter: Pre-Explosion (Score High but not Overheated)
                    # Score >= 8.5 AND RSI < 75
                    current_rsi = alpha.last_state_map['rsi'].loc[ts]
                    current_vol = alpha.last_state_map['vol_ratio'].loc[ts]
                    
                    candidates = valid_sigs[valid_sigs >= 7.0].sort_values(ascending=False) # Lower base threshold to filter later
                    curr_vols = volumes.loc[ts]

                    for sym in candidates.index:
                        if len(positions) >= MAX_POSITIONS: break
                        
                        # [AUTONOMY] No Hard filters. Trust the Brain.
                        score = candidates[sym]
                        rsi_val = current_rsi.get(sym, 50)
                        vol_val = current_vol.get(sym, 1.0)
                        
                        # [PHASE 4: LIVING MEMORY - Active Comparison]
                        # 1. Capture Raw Context
                        px = closes.loc[ts, sym]
                        op = closes.iloc[closes.index.get_loc(ts)-1][sym] if closes.index.get_loc(ts) > 0 else px
                        body_pct = (px - op) / op if op != 0 else 0.0
                        
                        hi = high_prices.loc[ts, sym] if 'high_prices' in locals() else px
                        lo = low_prices.loc[ts, sym] if 'low_prices' in locals() else px
                        range_pct = (hi - lo) / lo if lo > 0 else 0.0
                        
                        curr_context = np.array([float(vol_val), float(body_pct), float(range_pct)])
                        
                        # 2. Recall & Compare (The Fierce Debate)
                        # Scan memory bank for similar contexts
                        memory_score = 0.0
                        
                        # 2. Recall & Compare (The Fierce Debate)
                        # Scan memory bank for similar contexts
                        memory_score = 0.0
                        
                        # [GPU 3D WARP CHANGE]
                        if brain.memory_tensor is not None:
                            try:
                                # [CPU] Push Material: Prepare Query
                                query_vec = torch.tensor([curr_context], dtype=torch.float32, device=brain.device)
                                
                                # [GPU] Warp Search: Calculate Distances in Parallel
                                # cdist(1x3, Nx3) -> 1xN
                                dists = torch.cdist(query_vec, brain.memory_tensor)
                                
                                # [GPU] Find Nearest 10
                                # topk returns (values, indices)
                                top_d, top_i = torch.topk(dists, k=10, largest=False)
                                
                                # [GPU -> CPU] Retrieve Information to Stack
                                top_i = top_i.cpu().squeeze().tolist()
                                top_d = top_d.cpu().squeeze().tolist()
                                
                                if not isinstance(top_i, list): top_i = [top_i]
                                if not isinstance(top_d, list): top_d = [top_d]

                                # Filter logic (similar to before)
                                valid_indices = [i for i, d in zip(top_i, top_d) if d < 1000]
                                dists_clean = [d for d in top_d if d < 1000]
                                
                                if valid_indices:
                                    # Retrieve Outcomes (Directly from GPU tensor if possible, but list index is fast on CPU for metadata)
                                    # Actually we stored outcomes on GPU too: bubble.memory_outcomes
                                    relevant_outcomes = brain.memory_outcomes[valid_indices] # GPU Indexing
                                    
                                    # Weighted Average on GPU
                                    weights = 1.0 / (torch.tensor(dists_clean, device=brain.device) + 1e-6)
                                    expected_pnl = torch.sum(relevant_outcomes * weights) / torch.sum(weights)
                                    
                                    # [GPU] Activation (Adrenal Response)
                                    # [GOLDEN RATIO] 1.618 Balance between Reason (Brain) and Instinct (Memory)
                                    PHI = 1.61803398875
                                    mem_impact_t = torch.tanh(expected_pnl * 20.0) * PHI
                                    
                                    # [CPU] Stack Result
                                    memory_impact = mem_impact_t.item()
                                    score += memory_impact
                                    
                            except Exception as e:
                                pass # Search Fail
                        
                        elif len(brain.memory_bank) > 10:
                             # Fallback logic (omitted for brevity, assume GPU works)
                             pass
                        
                        # [ELDRITCH PRECOGNITION] DISABLED - Pure Memory Mode
                        # try:
                        #     future_idx = idx + 5
                        #     if future_idx < len(closes.index):
                        #         future_px = closes.iloc[future_idx].get(sym, px)
                        #         glimpse_ret = (future_px / px) - 1.0
                        #         precog_nudge = np.tanh(glimpse_ret * 100.0) * 1.0
                        #         score += precog_nudge
                        #         if abs(precog_nudge) > 0.3:
                        #             log(f"🔮 [PRECOG] {sym} Whisper: {precog_nudge:+.2f}")
                        # except:
                        #     pass

                        # [UNCHAINED] Dynamic Thresh check
                        # [HUNGER] Survival Instinct: If we haven't eaten (traded) in a while, get aggressive.
                        # "To not trade is to slowly die."
                        hunger_boost = 0.0
                        if last_trade_time:
                            idle_steps = (ts - last_trade_time).total_seconds() / 60.0 # Minutes
                            if len(positions) == 0 and idle_steps > 60: # 1 Hour without food
                                hunger_boost = min(2.0, (idle_steps - 60) * 0.01) # Scales up to +2.0 over time
                                score += hunger_boost
                                # if hunger_boost > 0.5: log(f"🦁 [HUNGER] Starving for {idle_steps:.0f}m -> Boost: +{hunger_boost:.1f}")
                        else:
                            # Initial state: Treat as if we just ate, or maybe slightly hungry?
                            pass

                        if score < dyn_th: continue
                        
                        event_context = {
                            'vol_ratio': float(vol_val),
                            'body_pct': float(body_pct),
                            'range_pct': float(range_pct)
                        }
                        
                        # [FIX] Define Price/Vol for Execution Logic
                        px = closes.loc[ts, sym]
                        bar_vol = curr_vols.get(sym, 0)
                        
                        # [FIX] Generate Brain Features for Learning
                        # Use Raw Swings instead of binary flags (No more 'vol > 3.0')
                        try:
                            f1 = rsi_val / 100.0
                            f2 = vol_val / 5.0 # Scaled raw
                            trend_val = alpha.last_state_map.get('trend_15m', pd.Series()).get(ts, {}).get(sym, 0.0)
                            f3 = float(trend_val) / 0.1 if trend_val is not None else 0.0
                            f4 = body_pct / 0.05 # Scaled raw body
                            f5 = range_pct / 0.05 # Scaled raw range
                            
                            ef = torch.tensor([f1, f2, f3, f4, f5], dtype=torch.float32, device=brain.device)
                            pad = torch.zeros(64-5, dtype=torch.float32, device=brain.device)
                            entry_feat = torch.cat([ef, pad])
                        except Exception:
                            entry_feat = torch.zeros(64, dtype=torch.float32, device=brain.device)

                        # [PYRAMIDING CHECK] (Only on Pullback)
                        is_pyramid = False
                        if sym in positions:
                            pos = positions[sym]
                            py_cnt = pos.get('pyramid_count', 0)
                            if score >= 8.5 and vol_val < 2.0 and py_cnt < 2: 
                                is_pyramid = True
                            else:
                                continue  # Skip duplicate entry

                        alloc_ratio = 0.20 # Equal Weight (20%)
                        mode_label = "EQUAL_WEIGHT"
                        
                        # [REJECT] Late Entry (Redundant Check Removed, strict filter above handles it)
                        # if score > 8.0 and rsi_val > 80 and vol_val > 5.0: continue 
                            
                        inv = CAPITAL * alloc_ratio # Fixed amount based on initial capital
                        if inv > cash: inv = cash
                        
                        # [LIQUIDITY GUARD] Real-world check
                        target_qty = int(inv / px)
                        max_qty = int(bar_vol * MAX_ORDER_VOLUME_RATIO)
                        final_qty = min(target_qty, max_qty)
                        
                        if final_qty <= 0: continue
                        
                        # [IMPACT COST MODEL]
                        order_impact = final_qty / (bar_vol + 1e-9)
                        effective_slippage = SLIPPAGE
                        if order_impact > IMPACT_THRESHOLD:
                            # Add impact penalty (0.1 ratio -> +0.5% slippage)
                            effective_slippage += (order_impact * 0.05) 
                        
                        qty = final_qty
                        cost = qty * px * (1 + effective_slippage + FEE)
                        if cost <= cash:
                             cash -= cost
                             strat_code = "Unknown"
                             if alpha.last_reasons is not None:
                                 strat_code = alpha.last_reasons.loc[ts, sym]
                                 if not strat_code: strat_code = "Unknown"
                                 
                             if is_pyramid:
                                 old_qty = positions[sym]['qty']
                                 old_entry = positions[sym]['entry_px']
                                 new_qty = old_qty + qty
                                 new_entry = (old_qty * old_entry + qty * px) / new_qty
                                 positions[sym]['qty'] = new_qty
                                 positions[sym]['entry_px'] = new_entry
                                 positions[sym]['pyramid_count'] = py_cnt + 1
                                 positions[sym]['entry_features'] = entry_feat.clone()  # Update features for learning
                                 log(f"🔥 PYRAMID! {sym} (Qty:+{qty}, Avg:{new_entry:,.0f}, Impact:{order_impact*100:.1f}%)")
                             else:
                                 positions[sym] = {'qty': qty, 'entry_px': px, 'strategy': strat_code, 'pyramid_count': 0, 'entry_score': score, 'entry_features': entry_feat.clone(), 'entry_time': ts, 'event_context': event_context}
                                 last_trade_time = ts # [HUNGER] Sated. Reset starvation timer.
                                 log(f"⚔️ ENTRY [{mode_label}]: {sym} (Score: {score:.1f}, RSI: {rsi_val:.1f}, Hunger: {hunger_boost:.1f})")
                                 
                                 if score >= 8.5:
                                     # [ALIEN] Oracle Consultation
                                     if oracle and oracle.active:
                                          ctx = {
                                              'rsi': alpha.last_state_map['rsi'].loc[ts, sym],
                                              'vol_ratio': alpha.last_state_map['vol_ratio'].loc[ts, sym],
                                              'width_z': alpha.last_state_map['width_z'].loc[ts, sym],
                                              'trend_15m': alpha.last_state_map['trend_15m'].loc[ts, sym],
                                              'whale': alpha.last_state_map['whale'].loc[ts, sym],
                                              'squeeze': alpha.last_state_map['squeeze'].loc[ts, sym]
                                          }
                                          alien_score = oracle.consult(sym, ctx)
                                          log(f"👽 Oracle Verdict on {sym}: {alien_score:.1f}/10 (Human Score: {score:.1f})")
                                          
                                          if alien_score < 6.0:
                                              log(f"⚠️ Oracle REJECTED Hero! Downgrading.")
                                              old_qty = positions[sym]['qty']
                                              new_qty = int(old_qty * 0.2)
                                              positions[sym]['qty'] = new_qty
                                              refund_cash = (old_qty - new_qty) * px * (1 + effective_slippage + FEE)
                                              cash += refund_cash
                                              mode_label = "SCOUT(Downgraded)"
                                     
                                     log(f"🚨 HERO FORCE ATTACK! {sym} (Impact: {order_impact*100:.1f}%)")
                                 else:
                                     log(f"⚔️ ENTRY [{mode_label}]: {sym} (Score: {score:.1f}, Impact: {order_impact*100:.1f}%)")

            if idx % 10 == 0:
                eq = cash + sum(pos['qty'] * curr_pxs.get(sym, pos['entry_px']) for sym, pos in positions.items())
                equity_curve.append(eq)
                
            if idx % 500 == 0: # Auto-save trace
                pd.DataFrame({'equity': equity_curve}).to_csv(PROJECT_ROOT / "results/GARAM_OSS_SHARE_RESULT.csv")

            # [GPU COOLING] Force Sleep in Loop to prevent 100% Load
            if idx % 10 == 0:
                time.sleep(0.005) # 5ms rest every 10 ticks

        log("Simulation COMPLETE. Final Archiving...")
        archive_wisdom("FINAL", eq, trade_logs, {"threshold": dyn_th, "stop": dyn_stop})
        
        # Save Final Trace
        pd.DataFrame({'equity': equity_curve}).to_csv(PROJECT_ROOT / "results/GARAM_OSS_SHARE_RESULT.csv")

        # [EVOLUTION] Self-Correction
        df_trades = pd.DataFrame(trade_logs)
        if not df_trades.empty and 'strategy' in df_trades.columns:
            df_trades['strategy'] = df_trades['strategy'].fillna('Unknown')
            valid_strats = df_trades[df_trades['strategy'].astype(str).str.startswith('S')]
            if not valid_strats.empty:
                stats = valid_strats.groupby('strategy')['pnl'].agg(['count', 'mean', lambda x: (x>0).mean()])
                stats.columns = ['count', 'avg_pnl', 'win_rate']
                log("\n[EVOLUTION] Strategy Performance Report:")
                log(stats.to_string())
                
                for strat, row in stats.iterrows():
                    if row['win_rate'] < 0.40 and row['count'] > 3:
                         log(f"📉 Strategy {strat} is failing (WR: {row['win_rate']:.2f}). Evolving...")
                         alpha.evolve({'strategy': strat, 'success': False})
                    elif row['win_rate'] > 0.70 and row['count'] > 3:
                         log(f"🚀 Strategy {strat} is crushing it! Keeping genes.")
                
                with open(PROJECT_ROOT / "core/active_config/evolved_genes.json", "w") as f:
                    json.dump(alpha.params, f, indent=4)
                log("🧬 OSS Genes mutated and saved.")
            
        log(f"💤 Cooling down before next Epoch...")
        time.sleep(3)

        # [GPU COOLING] Force Sleep in Loop to prevent 100% Load
        if idx % 10 == 0:
            time.sleep(0.005) # 5ms rest every 10 ticks

if __name__ == "__main__":
    run_real_test()
