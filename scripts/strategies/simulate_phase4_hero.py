
import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import argparse

# Setup
PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))
DATA_DIR = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"
OUT_DIR = PROJECT_ROOT / "logs/phase4_sweep"
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', 
                    handlers=[logging.StreamHandler(sys.stdout)])

class Phase4Engine:
    def __init__(self, mode='FIXED', max_weight=0.7, aesthetic=False, penalty_multiplier=1.0, 
                 initial_weight=0.3, pyramid_thresholds=(0.05, 0.10)):
        self.mode = mode 
        self.max_weight = max_weight
        self.aesthetic = aesthetic
        self.penalty_multiplier = penalty_multiplier
        self.initial_weight = initial_weight  # Phase 8: 초기 진입 비중 (기본 30%)
        self.pyramid_thresholds = pyramid_thresholds  # Phase 8: (1차 증액 임계값, 2차 증액 임계값)
        self.universe = {} 
        self.cash = 100_000_000
        self.positions = {} 
        self.equity_curve = []
        self.trade_log = []
        self.market_breadth = pd.Series(dtype=float)
        self.market_vol_accel = pd.Series(dtype=float)
        self.hero_counts = 0

        # [Phase 6] Load Failure Patterns
        self.failure_patterns = []
        pats_file = PROJECT_ROOT / "config/failure_patterns.json"
        if pats_file.exists():
            import json
            try:
                with open(pats_file) as f:
                    self.failure_patterns = json.load(f).get('patterns', [])
                print(f"[Sim] Loaded {len(self.failure_patterns)} Failure Patterns for Intelligent Filtering.")
            except: pass

    def load_data(self):
        # Load Clean Universe if available
        clean_univ_path = PROJECT_ROOT / "config/clean_universe.csv"
        valid_tickers = None
        if clean_univ_path.exists():
            try:
                valid_tickers = set(pd.read_csv(clean_univ_path)['ticker'].astype(str))
                print(f"[Sim] Loaded {len(valid_tickers)} clean tickers.")
            except Exception as e:
                print(f"[Sim] warning: could not read clean universe: {e}")

        files = list(DATA_DIR.glob("*.csv"))
        for f in files:
            if 'K' in f.name: continue
            if valid_tickers is not None and f.stem not in valid_tickers: continue
            try:
                df = pd.read_csv(f)
                cols = {c.lower(): c for c in df.columns}
                rename = {}
                for k, v in cols.items():
                    if 'date' in k or 'ts' in k: rename[v] = 'date'
                    elif 'close' in k: rename[v] = 'close'
                    elif 'open' in k: rename[v] = 'open'
                    elif 'high' in k: rename[v] = 'high'
                    elif 'low' in k: rename[v] = 'low'
                    elif 'vol' in k: rename[v] = 'volume'
                    
                df.rename(columns=rename, inplace=True)
                if 'date' not in df.columns: continue
                
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                d = df.resample('1D').agg({
                    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
                }).dropna()
                
                if d.empty: continue
                d['turnover'] = d['close'] * d['volume']
                d['ma20'] = d['close'].rolling(20).mean()
                d['pct_chg'] = d['close'].pct_change()
                self.universe[f.stem] = d
                
            except Exception:
                pass
                
        # Breadth
        if not self.universe: return
        closes = pd.DataFrame({t: d['close'] for t, d in self.universe.items()})
        ma20 = closes.rolling(20).mean()
        above = (closes > ma20).sum(axis=1) / closes.notnull().sum(axis=1)
        self.market_breadth = above.fillna(0.5)
        pcts = closes.pct_change().abs().mean(axis=1)
        vol_ma = pcts.rolling(20).mean()
        self.market_vol_accel = (pcts / vol_ma).fillna(1.0)

    def apply_intelligent_filter_sim(self, symbol, score, vol_accel):
        """
        [Phase 6] Intelligent Filter (Simulation Version)
        """
        if not self.failure_patterns: return score
        
        penalty = 0
        for p in self.failure_patterns:
            # Check Condition: vol_accel_high
            if 'vol_accel' in p.get('condition', ''):
                threshold = p.get('threshold', 999)
                if vol_accel > threshold:
                    # Apply Penalty
                    penalty += p.get('penalty_score', 0)
                    
        if penalty > 0:
            final_penalty = penalty * self.penalty_multiplier
            return score - final_penalty
        return score

    def determine_scenario(self, date):
        breadth = self.market_breadth.get(date, 0.5)
        vol_accel = self.market_vol_accel.get(date, 1.0)
        
        scenario = "FOGGY"
        slots = 10
        if breadth > 0.60 and vol_accel < 1.2:
            scenario = "GOLD_RUSH"
            slots = 3
        elif breadth < 0.30:
            scenario = "ICE_AGE"
            slots = 20 
        elif vol_accel > 2.0:
            scenario = "CLIMAX"
            slots = 0 
        return scenario, slots

    def run(self):
        dates = sorted(list(self.market_breadth.index))
        dates = [d for d in dates if d >= pd.Timestamp("2025-10-01")]
        
        import random
        random.seed(42) 
        
        for today in dates:
            scen, max_slots = self.determine_scenario(today)
            vol_accel = self.market_vol_accel.get(today, 1.0)
            
            # Dynamic Threshold
            # Base 85. If aesthetic, add VolAccel impact.
            # User: "85% + (Vol_Accel * 5%)"
            # Assuming VolAccel ~1.0 -> 90%.
            base_threshold = 85.0
            if self.aesthetic:
                base_threshold = 85.0 + (vol_accel * 5.0)
            
            # [Phase 6] Intelligent Filter
            # If we didn't use 'Aesthetic' hardcoded rule above, we would use this.
            # But the user asked for BOTH "Aesthetic" and "Intelligent Filter".
            # The filter applies penalties to the SCORE.
            
            # 1. Valuation
            eq = self.cash
            for t, p in self.positions.items():
                curr_px = self.universe[t].loc[today, 'close'] if today in self.universe[t].index else p['last_px']
                eq += p['qty'] * curr_px
            
            self.equity_curve.append({'date': today, 'equity': eq})
            
            # 2. Exits
            kill = []
            current_holdings = list(self.positions.keys())
            for t in current_holdings:
                if t not in self.positions: continue
                p = self.positions[t]
                if today not in self.universe[t].index: continue
                row = self.universe[t].loc[today]
                
                # Stop Loss
                if row['close'] < p['highest'] * 0.95:
                    self.cash += p['qty'] * row['close']
                    kill.append(t)
                    self.trade_log.append({'date':today, 'ticker':t, 'side':'SELL', 'reason':'TrailStop', 'pnl': (row['close']-p['avg'])*p['qty']})
                    continue
                    
                p['highest'] = max(p['highest'], row['high'])
                p['last_px'] = row['close']
                
                # --- PYRAMIDING SCALE UP (Phase 8: Configurable Thresholds) ---
                if self.mode == 'PYRAMID' and p.get('is_hero'):
                    curr_pnl_pct = (row['close'] - p['avg']) / p['avg']
                    
                    # Phase 8: 가변 임계값 사용
                    thresh1, thresh2 = self.pyramid_thresholds
                    target_scale = 0.0
                    if curr_pnl_pct > thresh2: target_scale = self.max_weight  # 2차 증액 -> 최대 비중
                    elif curr_pnl_pct > thresh1: target_scale = 0.50  # 1차 증액 -> 50%
                    
                    curr_val = p['qty'] * row['close']
                    curr_w = curr_val / eq
                    
                    if target_scale > curr_w + 0.05:
                         needed = (target_scale - curr_w) * eq
                         if self.cash < needed:
                             # Harvest (ScaleUp is Always Priority - Feed the Winner)
                             hv_needed = needed - self.cash
                             other_keys = [k for k in self.positions if k != t]
                             for ok in other_keys:
                                 if hv_needed <= 0: break
                                 op = self.positions[ok]
                                 val = op['qty'] * op['last_px']
                                 self.cash += val
                                 hv_needed -= val
                                 del self.positions[ok]
                                 self.trade_log.append({'date':today, 'ticker':ok, 'side':'SELL', 'reason':'ScaleHarvest', 'pnl':0})

                         buy_amt = min(self.cash, needed)
                         q = int(buy_amt / row['close'])
                         if q > 0:
                             self.cash -= q * row['close']
                             old_qty = p['qty']
                             old_avg = p['avg']
                             new_avg = ((old_qty * old_avg) + (q * row['close'])) / (old_qty + q)
                             self.positions[t]['qty'] += q
                             self.positions[t]['avg'] = new_avg
                             self.trade_log.append({'date':today, 'ticker':t, 'side':'BUY', 'reason':f'ScaleUp_P{curr_pnl_pct*100:.0f}', 'price':row['close']})
                
            for k in kill: del self.positions[k]
            
            # 3. Entries
            if scen == "ICE_AGE" or scen == "CLIMAX": continue
            
            candidates = []
            score_map = {} # For Churn check
            
            for t, df in self.universe.items():
                if today not in df.index: continue
                row = df.loc[today]
                if row['turnover'] < 10_000_000_000: continue
                score = 0
                if row['pct_chg'] > 0.05 and row['close'] > row['ma20']:
                    # Simple Random Score Model
                    score = random.uniform(80, 99)
                
                # [Phase 6] Intelligent Filter
                score = self.apply_intelligent_filter_sim(t, score, vol_accel)
                
                candidates.append({'ticker': t, 'score': score, 'close': row['close']})
                score_map[t] = score
                
            candidates.sort(key=lambda x: x['score'], reverse=True)
            if not candidates: continue
            
            top = candidates[0]
            # Use Dynamic Threshold
            is_hero = top['score'] >= base_threshold
            
            tkr = top['ticker']
            if tkr not in self.positions:
                can_enter = len(self.positions) < max_slots
                if is_hero: can_enter = True 
                
                if can_enter:
                    if self.mode == 'PYRAMID' and is_hero:
                        init_w = self.initial_weight  # Phase 8: 가변 초기 비중
                    elif self.mode == 'FIXED' and is_hero:
                        init_w = self.max_weight 
                    else:
                        init_w = 0.10 
                        
                    amt = eq * init_w
                    
                    if is_hero and self.cash < amt:
                        # Harvest
                        needed = amt - self.cash
                        keys = [k for k in self.positions]
                        for other in keys:
                            if needed <= 0: break
                            
                            # [Churn Filter]
                            if self.aesthetic:
                                # Only sell 'other' if New Score > Old Score * 1.2
                                other_score = score_map.get(other, 0)
                                if top['score'] < other_score * 1.2:
                                    # New Hero is not dominant enough. Skip Harvest.
                                    # "Preserve existing"
                                    continue
                            
                            p = self.positions[other]
                            val = p['qty'] * p['last_px']
                            self.cash += val
                            del self.positions[other]
                            needed -= val
                            # Log 0 PnL for Harvest? Or calc?
                            harvest_pnl = (p['last_px'] - p['avg']) * p['qty']
                            self.trade_log.append({'date':today, 'ticker':other, 'side':'SELL', 'reason':'SwitchHarvest', 'pnl':harvest_pnl})
                            
                    qty = int(min(self.cash, amt) / top['close'])
                    if qty > 0:
                        self.cash -= qty * top['close']
                        self.positions[tkr] = {
                            'qty': qty, 'avg': top['close'], 'highest': top['close'], 
                            'last_px': top['close'], 'is_hero': is_hero
                        }
                        if is_hero: self.hero_counts += 1
                        self.trade_log.append({'date':today, 'ticker':tkr, 'side':'BUY', 'reason':'InitialEntry', 'price':top['close']})

        # Save
        suffix = f"{self.mode}_{self.max_weight}"
        if self.aesthetic: suffix += "_AESTHETIC"
        if self.failure_patterns:
            suffix += "_INTELLIGENT"
            if self.penalty_multiplier != 1.0:
                suffix += f"_PM{self.penalty_multiplier:.1f}"
        # Phase 8: 파라미터 표시
        if self.initial_weight != 0.3:
            suffix += f"_I{int(self.initial_weight*100)}"
        if self.pyramid_thresholds != (0.05, 0.10):
            t1, t2 = self.pyramid_thresholds
            suffix += f"_T{int(t1*100)}-{int(t2*100)}"
        
        pd.DataFrame(self.equity_curve).to_csv(OUT_DIR / f"equity_{suffix}.csv", index=False)
        pd.DataFrame(self.trade_log).to_csv(OUT_DIR / f"trades_{suffix}.csv", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="FIXED")
    parser.add_argument("--weight", type=float, default=0.7)
    parser.add_argument("--aesthetic", action="store_true")
    parser.add_argument("--penalty_multiplier", type=float, default=1.0)
    # Phase 8: 피라미딩 파라미터
    parser.add_argument("--initial_weight", type=float, default=0.3, help="초기 진입 비중 (기본 30%)")
    parser.add_argument("--thresh1", type=float, default=0.05, help="1차 증액 PnL 임계값 (기본 5%)")
    parser.add_argument("--thresh2", type=float, default=0.10, help="2차 증액 PnL 임계값 (기본 10%)")
    args = parser.parse_args()
    
    # Phase 8: 가변 파라미터 적용
    eng = Phase4Engine(
        mode=args.mode, 
        max_weight=args.weight, 
        aesthetic=args.aesthetic, 
        penalty_multiplier=args.penalty_multiplier,
        initial_weight=args.initial_weight,
        pyramid_thresholds=(args.thresh1, args.thresh2)
    )
    eng.load_data()
    eng.run()
