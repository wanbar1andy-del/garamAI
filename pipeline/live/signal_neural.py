
import torch
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Neural Brain Import
try:
    from scripts.neural_brain import GaramNeuralBrain
except ImportError:
    # Backup import if running from different context
    sys.path.append(str(PROJECT_ROOT / "scripts"))
    from neural_brain import GaramNeuralBrain

class SignalNeuralBrain:
    def __init__(self, config):
        self.cfg = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load Brain
        # Matches train_oss_brain.py setup: input=64, mode=CUSTOM_45
        self.brain = GaramNeuralBrain(input_size=64, mode="CUSTOM_45").to(self.device)
        model_path = PROJECT_ROOT / "core/active_config/neuro_brain_state.pth"
        
        self.brain_loaded = False
        if model_path.exists():
            try:
                self.brain.load_state_dict(torch.load(model_path, map_location=self.device))
                self.brain.eval()
                print(f"[Brain] ✅ Loaded OSS Brain from {model_path}")
                self.brain_loaded = True
            except Exception as e:
                print(f"[Brain] ❌ Error loading weights: {e}")
        else:
            print("[Brain] ⚠️ WARN: No pre-trained weights found! Signals will be random/untrained.")

        self.history = {} # sym -> DataFrame
        self.lookback = 60 # Safe buffer

    def on_bar_closed(self, closed_bars, vol_accel=1.0):
        # Update History
        for sym, bar in closed_bars.items():
            if sym not in self.history:
                self.history[sym] = pd.DataFrame(columns=['open','high','low','close','volume'])
            
            # bar is specific dict structure: {'dt', 'open'...}
            # Convert to DataFrame row
            # If bar comes as a dict, wrap it.
            row_data = bar.copy()
            dt = row_data.pop('dt')
            new_row = pd.DataFrame([row_data], index=[dt])
            
            if self.history[sym].empty:
                self.history[sym] = new_row
            else:
                self.history[sym] = pd.concat([self.history[sym], new_row])
            
            # Trim
            if len(self.history[sym]) > self.lookback + 20:
                self.history[sym] = self.history[sym].iloc[-(self.lookback+20):]

        best_sym = None
        best_score = -999.0
        debug_info = {}

        if not self.brain_loaded:
            return None, {}

        for sym, df in self.history.items():
            if len(df) < 22: continue 
            
            try:
                # Features Calculation (Must match train_oss_brain.py EXACTLY)
                c = df['close'].astype(float)
                v = df['volume'].astype(float)
                
                # 1. RSI (14)
                delta = c.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / (loss + 1e-9)
                rsi = 100 - (100 / (1 + rs))
                rsi_val = rsi.iloc[-1]
                
                # 2. Volume Ratio
                v_ma = v.rolling(window=20).mean()
                vol_ratio = (v / (v_ma + 1e-9)).iloc[-1]
                
                # 3. MA Distance
                ma20 = c.rolling(window=20).mean()
                ma_dist = (c / (ma20 + 1e-9) - 1.0).iloc[-1]
                
                # 4. Whale
                whale = 1.0 if vol_ratio > 3.0 else 0.0
                
                # 5. Squeeze
                squeeze = 1.0 if (rsi_val < 30 and vol_ratio > 2.0) else 0.0
                
                # Normalization
                f1 = rsi_val / 100.0
                f2 = vol_ratio / 10.0
                f3 = ma_dist / 0.1
                f4 = whale
                f5 = squeeze
                
                # Tensor
                feats = torch.tensor([f1, f2, f3, f4, f5], dtype=torch.float32).unsqueeze(0).to(self.device)
                
                # Padding to 64
                pad = torch.zeros(1, 64-5).to(self.device)
                input_tensor = torch.cat([feats, pad], dim=1)
                
                # Inference
                with torch.no_grad():
                    out = self.brain(input_tensor)
                
                # Output[0] is Predicted Return (tanh * 0.15)
                pred_ret = torch.tanh(out[0, 0]) * 0.15
                score = pred_ret.item() * 100 # e.g. 0.01 -> 1.0
                
                if score > best_score:
                    best_score = score
                    best_sym = sym
                    debug_info = {
                        'symbol': sym,
                        'score': score,
                        'rsi': rsi_val,
                        'vol_ratio': vol_ratio,
                        'pred_return': f"{pred_ret.item()*100:.2f}%",
                        'passed': -1
                    }
                    
            except Exception:
                continue
        
        # OSS Unchained: Minimal Filter
        # Only check if predicted return is positive and significant (> 0.5%)
        # This keeps the "Autonomy" promise.
        if best_sym and best_score > 0.5:
             # Add passed count to debug for consistency
             debug_info['passed'] = 1 
             return best_sym, debug_info
            
        return None, {}

    def get_fallback_candidate(self, exclude_symbols=[]):
        # Neural Fallback: Just return best positive score even if small
        # Identical logic, just ignoring exclusion
        # Simplified: Reuse logic? 
        # For now, just return None. Autonomy means if Brain says "No", we don't force it.
        return None, {}
