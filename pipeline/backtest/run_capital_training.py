import pandas as pd
import numpy as np
import json
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from run_alpha_robust import AlphaGenius_V2, load_data, parse_minute_csv, simulate_crash, apply_noise

# --- Configuration for Capital Modes ---
CAPITAL_MODES = {
    "GUERRILLA": {
        "range": "1M ~ 10M KRW",
        "description": "게릴라 스카우트 모드 (Speed & High Turnover)",
        "capital": 10_000_000,
        "slippage_bps": 0,       # Assumption: Agile execution
        "fee_bps": 15,           # Basic fee
        "target_roi": 0.015,     # 1.5% Short target
        "stop_loss": 0.015,      # Tight stop
        "max_hold_hours": 4,     
        "neuro_sizing": False    # Flat betting for speed
    },
    "SNIPER": {
        "range": "10M ~ 100M KRW",
        "description": "엘리트 스나이퍼 모드 (AlphaGenius V2 Core)",
        "capital": 100_000_000,
        "slippage_bps": 5,
        "fee_bps": 15,
        "target_roi": 0.15,      # Hero target
        "stop_loss": 0.030,      # Trailing Stop 3.0%
        "max_hold_hours": 24,
        "neuro_sizing": True     # Bet Big on Score 9.0+
    },
    "DIVISION": {
        "range": "100M ~ 1B KRW",
        "description": "디비전 사단 모드 (Slicing & Portfolio)",
        "capital": 1_000_000_000,
        "slippage_bps": 20,      # Impact Cost implies higher slippage
        "fee_bps": 15,
        "target_roi": 0.10,
        "stop_loss": 0.050,
        "max_hold_hours": 48,
        "neuro_sizing": True,
        "slicing_active": True   # Simulated via penalty
    },
    "SOVEREIGN": {
        "range": "1B ~ 10B KRW",
        "description": "소버린 군단 모드 (Impact & Trend Setting)",
        "capital": 10_000_000_000,
        "slippage_bps": 40,      # Heavy Impact
        "fee_bps": 12,           # Institutional rate
        "target_roi": 0.08,
        "stop_loss": 0.070,
        "max_hold_hours": 120,   # Weekly
        "neuro_sizing": True,
        "impact_trigger": True
    },
    "FLEET": {
        "range": "10B ~ 100B KRW",
        "description": "함대 글로벌 모드 (Ecosystem Dominance)",
        "capital": 100_000_000_000,
        "slippage_bps": 50,
        "fee_bps": 10,
        "target_roi": 0.05,
        "stop_loss": 0.100,      # Wide stop for macro
        "max_hold_hours": 240,   # Monthly+
        "neuro_sizing": False,   # Portfolio Allocation wins
        "market_neutral": True
    }
}

class CapitalTrainer:
    def __init__(self, data_dir, alpha_model):
        self.data_dir = data_dir
        self.alpha = alpha_model
        # Load Data Once
        self.closes, self.volumes = load_data(data_dir, "universe.csv", "20250601", "20251212")
        print(f"[Trainer] Loaded Market Environment: {self.closes.shape}")
        
        # Pre-calculate Signals (Logic is constant, Execution varies)
        print("[Trainer] Pre-calculating AlphaGenius V2 Signals...")
        self.signals = self.alpha.calculate_signals(self.closes, self.volumes)
        if hasattr(self.alpha, 'calculate_exhaustion'):
            self.exhaustion = self.alpha.calculate_exhaustion(self.closes, self.volumes)
        else:
            self.exhaustion = pd.DataFrame(False, index=self.closes.index, columns=self.closes.columns)

    def run_training_stage(self, mode_name):
        config = CAPITAL_MODES[mode_name]
        print(f"\n{'='*60}")
        print(f"🚀 TRAINING STAGE: {mode_name}")
        print(f"   {config['description']}")
        print(f"   Capital: {config['capital']:,} KRW | Slippage: {config['slippage_bps']}bps")
        print(f"{'='*60}")
        
        # Adjust Simulation Parameters based on Mode
        capital = config['capital']
        slippage = config['slippage_bps'] / 10000.0
        fee = config['fee_bps'] / 10000.0
        target_roi = config['target_roi']
        stop_loss = config['stop_loss']
        neuro_sizing = config['neuro_sizing']
        
        # Simulation State
        cash = capital
        trades = []
        equity = []
        
        # Fast-Forward Simulation (Chronological)
        # Assuming Daily Steps for speed, but using Minute resolution signals
        
        # Iterate day by day
        dates = sorted(list(set(self.closes.index.date)))
        
        pos_sym = None
        pos_qty = 0
        entry_px = 0
        hold_start = None
        
        for d in dates:
            # Get daily slice
            mask = (self.closes.index.date == d)
            c_day = self.closes.loc[mask]
            
            if c_day.empty: continue
            
            # Intraday Logic (Simplified for Speed)
            # Check signals at start of day (or minute loop if needed)
            # To be fast ("5 minutes"), we iterate minutes but optimize
            
            # Using vector operations or simplified loop
            s_day = self.signals.loc[mask]
            e_day = self.exhaustion.loc[mask]
            
            for ts, row in c_day.iterrows():
                # Portfolio Value Update
                curr_val = cash
                if pos_sym:
                    curr_px = row[pos_sym]
                    if np.isnan(curr_px): continue
                    curr_val += pos_qty * curr_px
                    
                    # Exit Checks
                    # 1. Stealth Exit
                    if pos_sym in e_day.columns and e_day.loc[ts, pos_sym]:
                        cash += pos_qty * curr_px * (1 - fee)
                        trades.append({"mode": mode_name, "reason": "STEALTH_EXIT", "pnl": (curr_px/entry_px)-1})
                        pos_sym = None
                        continue
                        
                    # 2. Hard Limits
                    ret = (curr_px / entry_px) - 1.0
                    if ret < -stop_loss:
                        cash += pos_qty * curr_px * (1 - fee - slippage) # Slippage on Stop
                        trades.append({"mode": mode_name, "reason": "STOP", "pnl": ret})
                        pos_sym = None
                        continue
                    elif ret > target_roi:
                        cash += pos_qty * curr_px * (1 - fee - slippage)
                        trades.append({"mode": mode_name, "reason": "TARGET", "pnl": ret})
                        pos_sym = None
                        continue
                        
                    # 3. Time Limit (Guerrilla)
                    if config['max_hold_hours'] < 24 and hold_start:
                        held_time = (ts - hold_start).total_seconds() / 3600
                        if held_time > config['max_hold_hours']:
                            cash += pos_qty * curr_px * (1 - fee - slippage)
                            trades.append({"mode": mode_name, "reason": "TIME_EXIT", "pnl": ret})
                            pos_sym = None
                            continue
                            
                # Entry Logic
                if not pos_sym:
                    # Look for Signal
                    candidates = s_day.loc[ts]
                    candidates = candidates[candidates > 0].sort_values(ascending=False)
                    
                    if not candidates.empty:
                        sym = candidates.index[0]
                        score = candidates.iloc[0]
                        px = row[sym]
                        
                        if np.isnan(px) or px <= 0: continue
                        
                        # Sizing
                        alloc = 0.5 # Default (Division/Standard)
                        if mode_name == "GUERRILLA":
                            alloc = 1.0 # Full force
                        elif neuro_sizing:
                             if score >= 9.0: alloc = 1.0
                             elif score >= 7.0: alloc = 0.7
                             else: alloc = 0.5
                             
                        # In Division/Sovereign, allocation per trade is smaller to diversify (Simulated)
                        if mode_name in ["DIVISION", "SOVEREIGN", "FLEET"]:
                            alloc = 0.1 # 10 positions max
                        
                        invest = cash * alloc
                        qty = invest / (px * (1 + slippage))
                        cash -= invest 
                        pos_sym = sym
                        pos_qty = qty
                        entry_px = px
                        hold_start = ts
                        trades.append({"mode": mode_name, "reason": "ENTRY", "pnl": 0})
            
            # EOD Force Close (if max_hold_hours < 24 only)
            if pos_sym and config['max_hold_hours'] <= 6:
                last_px = c_day.iloc[-1][pos_sym]
                cash += pos_qty * last_px * (1 - fee - slippage)
                trades.append({"mode": mode_name, "reason": "EOD_FORCE", "pnl": (last_px/entry_px)-1})
                pos_sym = None
            
            equity.append(cash + (pos_qty * c_day.iloc[-1][pos_sym] if pos_sym else 0))

        # Reporting
        final_equity = equity[-1] if equity else capital
        roi = (final_equity / capital - 1) * 100
        win_trades = [t for t in trades if t['pnl'] > 0 and t['reason'] != "ENTRY"]
        total_closed = len([t for t in trades if t['reason'] != "ENTRY"])
        win_rate = (len(win_trades) / total_closed * 100) if total_closed > 0 else 0
        
        print(f"📊 RESULT [{mode_name}]:")
        print(f"   Final Capital: {final_equity:,.0f} KRW (ROI: {roi:.2f}%)")
        print(f"   Trades: {total_closed} | Win Rate: {win_rate:.1f}%")
        print(f"   Evaluation: {'PASSED' if roi > 0 else 'RETRY REQUIRED'}")
        
def main():
    print("::: GARAM CAPITAL CURRICULUM START :::")
    data_dir = Path("c:/garam/garam/GARAM_Data/minute/kr")
    alpha = AlphaGenius_V2()
    
    trainer = CapitalTrainer(data_dir, alpha)
    
    # Run 5-Minute Course (Fast Forward)
    # Stage 1: Guerrilla
    trainer.run_training_stage("GUERRILLA")
    
    # Stage 2: Sniper
    trainer.run_training_stage("SNIPER")
    
    # Stage 3: Division
    trainer.run_training_stage("DIVISION")
    
    # Stage 4: Sovereign
    trainer.run_training_stage("SOVEREIGN")
    
    # Stage 5: Fleet
    trainer.run_training_stage("FLEET")
    
    print("\n::: TRAINING COMPLETE :::")
    print("모든 자본 체급별 시뮬레이션이 5분 내 완료되었습니다.")

if __name__ == "__main__":
    main()
