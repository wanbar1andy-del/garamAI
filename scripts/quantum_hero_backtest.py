

# quantum_hero_backtest.py
# Phase Q-1: Quantum Hero Strategy (Research Backtest)
# - Superposition: maintain Top5 candidates by Score (probability mass proxy)
# - Observation (Collapse): enter only when measurement conditions met
# - Dynamic Transfer: switch when probability mass center shifts (score dominance)

from __future__ import annotations
import os, json
import glob
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Config
# -----------------------------
@dataclass
class Q1Config:
    name: str = "Base"
    start: str = "2025-10-01"
    end: str   = "2025-12-05"
    
    # Execution Mode
    execution_mode: str = "CLOSE"      # "CLOSE" (Theoretical) or "NEXT_OPEN" (Realistic)

    # thresholds
    entry_quantile: float = 0.0        # If > 0, calculates threshold dynamically (e.g. 0.7)
    entry_threshold: float = 0.0       # Fixed threshold (overridden if quantile > 0)
    
    # Switching gates
    switch_ratio: float = 1.20
    switch_abs_quantile: float = 0.0   # If > 0, calibrates AbsMin dynamically (e.g. 0.95)
    switch_abs_min: float = 0.0

    exit_rr: float = 0.95              # Exhausted if RR > ExitThreshold
    shake_limit: float = 4.0           # ShakeoutTexture < Limit for entry
    min_hold_days: int = 2             # churn budget gate (Increased to 2 for Inertia)

    topk: int = 5
    fee_bps: float = 2.0               # simple transaction cost (bps)
    slippage_bps: float = 1.0

    # regime policy
    ban_on: bool = False               # If True, enables Regime Logic (Peer Ban)
    ban_mode: str = "EXIT"             # EXIT (Hard Close) or SUPPRESS (No Entry/Switch)

# -----------------------------
# Data Loader
# -----------------------------
def load_data(path: str) -> pd.DataFrame:
    print(f"Loading data from {path}...")
    if os.path.isdir(path):
        files = glob.glob(os.path.join(path, "*.csv"))
        dfs = []
        for f in files:
            try:
                df = pd.read_csv(f)
                if 'ts' in df.columns: df.rename(columns={'ts':'date'}, inplace=True)
                elif 'datetime' in df.columns: df.rename(columns={'datetime':'date'}, inplace=True)
                
                needed = ['date','open','high','low','close','volume']
                if not all(c in df.columns for c in needed): continue
                
                ticker = os.path.splitext(os.path.basename(f))[0]
                df['date'] = pd.to_datetime(df['date'])
                
                df.set_index('date', inplace=True)
                daily = df.resample('D').agg({
                    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
                }).dropna().reset_index()
                daily['ticker'] = ticker
                dfs.append(daily)
            except: pass
        
        if not dfs: return pd.DataFrame()
        full_df = pd.concat(dfs, ignore_index=True)
        full_df = full_df.sort_values(["ticker", "date"]).reset_index(drop=True)
        return full_df
    else:
        df = pd.read_csv(path)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
        return df

# -----------------------------
# Feature Engineering
# -----------------------------
def calc_atr14(g: pd.DataFrame) -> pd.Series:
    high = g["high"].to_numpy()
    low = g["low"].to_numpy()
    close = g["close"].to_numpy()
    prev_close = np.r_[np.nan, close[:-1]]
    tr = np.nanmax(np.vstack([high - low, np.abs(high - prev_close), np.abs(low - prev_close)]), axis=0)
    atr = pd.Series(tr, index=g.index).rolling(14, min_periods=14).mean()
    return atr

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for tkr, g in df.groupby("ticker", sort=False):
        g = g.copy()
        g["ret5"] = g["close"].pct_change(5)
        g["ret20"] = g["close"].pct_change(20)
        
        g["vol_avg20"] = g["volume"].rolling(20, min_periods=20).mean()
        g["vol_spike"] = g["volume"] / (g["vol_avg20"] + 1e-12)
        
        # ShakeoutTexture
        r1 = g["close"].pct_change()
        abs_sum = r1.abs().rolling(5, min_periods=5).sum()
        net = g["close"].pct_change(5).abs()
        g["shake_texture"] = abs_sum / (net + 1e-12)
        
        out.append(g)
    return pd.concat(out, axis=0).sort_values(["date", "ticker"]).reset_index(drop=True)

# -----------------------------
# Metrics
# -----------------------------
def compute_metrics(row):
    price = row['close']
    ret20 = max(row['ret20'], 0) if np.isfinite(row['ret20']) else 0
    ret5 = max(row['ret5'], 0) if np.isfinite(row['ret5']) else 0
    vol = min(row['vol_spike'], 3.0) if np.isfinite(row['vol_spike']) else 0
    
    erc = price * (1.0 + ret20 + ret5 * vol)
    rr = price / (erc + 1e-12)
    score = (ret5 * vol) * (1.0 - abs(rr - 0.5))
    
    return erc, rr, score

def compute_score_vec(close, ret5, ret20, vol_spike):
    # Ensure inputs are float arrays and handle NaNs (Scalar parity)
    close = np.asarray(close, dtype=float)
    ret5 = np.nan_to_num(np.asarray(ret5, dtype=float), nan=0.0)
    ret20 = np.nan_to_num(np.asarray(ret20, dtype=float), nan=0.0)
    vol_spike = np.nan_to_num(np.asarray(vol_spike, dtype=float), nan=0.0)

    r5 = np.maximum(ret5, 0.0)
    r20 = np.maximum(ret20, 0.0)
    vol = np.minimum(vol_spike, 3.0)

    erc = close * (1.0 + r20 + r5 * vol)
    rr  = close / (erc + 1e-12)
    score = (r5 * vol) * (1.0 - np.abs(rr - 0.5))
    return erc, rr, score

# -----------------------------
# Regime Manager (X-6c Simplified)
# -----------------------------
class RegimeManager:
    def __init__(self, ban_on: bool):
        self.ban_on = ban_on
        self.state = "NORMAL" # NORMAL, BAN, RECOVERY
        self.peak_eq = 1.0
        self.dd = 0.0
        self.ban_days = 0
        
    def update(self, equity: float):
        if not self.ban_on: return False
        
        if equity > self.peak_eq: self.peak_eq = equity
        self.dd = (equity - self.peak_eq) / self.peak_eq
        
        is_ban = False
        
        if self.state == "NORMAL":
            if self.dd <= -0.05: # Bear Trigger
                self.state = "BAN"
                self.ban_days = 0
                is_ban = True
        elif self.state == "BAN":
            self.ban_days += 1
            is_ban = True
            # Simple Unban: Min 5 days AND Recovery > -2% (or simple bounce)
            # Proxy: If we recovered half the DD or DD > -0.03
            if self.ban_days >= 5 and self.dd > -0.03: 
                self.state = "NORMAL" # Skip recovery stage for simple backtest
                is_ban = False
                
        return is_ban

# -----------------------------
# Backtest Engine
# -----------------------------
@dataclass
class Position:
    ticker: str
    entry_date: pd.Timestamp
    entry_price: float
    erc: float
    hold_days: int = 0
    mark_price: float = 0.0 # for mark-to-market tracking

class BacktestEngine:
    def __init__(self, df: pd.DataFrame, cfg: Q1Config):
        self.df = df
        self.cfg = cfg
        self.regime = RegimeManager(cfg.ban_on)
        self.pos: Optional[Position] = None
        self.state = "CANDIDATE"
        self.equity = 1.0
        self.logs = []
        self.trades = []
        self.equity_curve = []
        self.pending = [] # Pending orders for NEXT_OPEN
        
        # Auto-Calibration
        if cfg.entry_quantile > 0:
            self.calibrate_threshold()
        if cfg.switch_abs_quantile > 0:
            self.calibrate_switch_abs(cfg.switch_abs_quantile)
        elif getattr(cfg, 'switch_abs_min', 0.0) == float('inf'):
            print(f"[{cfg.name}] Switching DISABLED (Abs=INF)")
            
    def calibrate_threshold(self):
        print(f"[{self.cfg.name}] Calibrating Entry Threshold (Q{self.cfg.entry_quantile})...")
        tmp = self.df.copy()
        tmp['erc'], tmp['rr'], tmp['score'] = compute_score_vec(
            tmp['close'].to_numpy(),
            tmp['ret5'].to_numpy(),
            tmp['ret20'].to_numpy(),
            tmp['vol_spike'].to_numpy()
        )
        
        daily_max = tmp.groupby('date')['score'].max().dropna()
        self.cfg.entry_threshold = daily_max.quantile(self.cfg.entry_quantile)
        print(f"[{self.cfg.name}] EntryThreshold set to {self.cfg.entry_threshold:.4f}")

    def calibrate_switch_abs(self, q=0.95):
        print(f"[{self.cfg.name}] Calibrating Switch Abs Gate DOMINANCE (Q{q})...")
        tmp = self.df.copy()
        tmp['erc'], tmp['rr'], tmp['score'] = compute_score_vec(
            tmp['close'].to_numpy(),
            tmp['ret5'].to_numpy(),
            tmp['ret20'].to_numpy(),
            tmp['vol_spike'].to_numpy()
        )

        v = tmp.dropna(subset=['score']).sort_values(['date','score'], ascending=[True,False])
        
        # Group by date, take TopK (or less if not available)
        topk = v.groupby('date').head(self.cfg.topk)
        
        def dom_gap(g):
            if len(g) < 2: return np.nan
            top1 = float(g.iloc[0]['score'])
            bottom = float(g.iloc[-1]['score']) # Worst of Available TopK
            return top1 - bottom
            
        gaps = topk.groupby('date').apply(dom_gap).dropna()
        
        if len(gaps) == 0:
            self.cfg.switch_abs_min = float('inf')
            print(f"[{self.cfg.name}] WARNING: No gap samples. SwitchAbsMin=INF (Switching OFF)")
        else:
            self.cfg.switch_abs_min = float(gaps.quantile(q))
            print(f"[{self.cfg.name}] SwitchAbsMin set to {self.cfg.switch_abs_min:.4f} (dominance)")

    def apply_cost(self):
        cost = (self.cfg.fee_bps + self.cfg.slippage_bps) / 10000.0
        self.equity *= (1.0 - cost)

    def run(self):
        dates = sorted(self.df["date"].unique())
        dates = [d for d in dates if d >= pd.Timestamp(self.cfg.start) and d <= pd.Timestamp(self.cfg.end)]
        
        print(f"[{self.cfg.name}] Running Simulation ({len(dates)} days)...")
        
        for d in dates:
            day_data = self.df[self.df["date"] == d].copy()
            
            # -----------------------------------------------------
            # 1. EXECUTE PENDING @ OPEN (NEXT_OPEN Execution Mode)
            # -----------------------------------------------------
            if self.cfg.execution_mode == "NEXT_OPEN" and self.pending:
                open_map = day_data.set_index('ticker')['open'].to_dict()
                
                # Filter valid orders
                valid_orders = []
                for od in self.pending:
                    if od['ticker'] in open_map and np.isfinite(open_map[od['ticker']]):
                         valid_orders.append(od)
                
                # Execute Orders (SELLs first)
                valid_orders.sort(key=lambda x: 0 if x['type']=='SELL' else 1)
                
                for od in valid_orders:
                    tkr = od['ticker']
                    px_open = float(open_map[tkr])
                    
                    if od['type'] == 'SELL':
                        if self.pos and self.pos.ticker == tkr:
                            # Overnight Gap (Close -> Open)
                            # Update Equity from MarkPrice(Close) to ExecutionPrice(Open)
                            gap_ret = (px_open / (self.pos.mark_price + 1e-12))
                            self.equity *= gap_ret
                            
                            self.trades.append({'date': d, 'type': 'SELL', 'ticker': tkr, 'px': px_open, 'reason': od['reason']})
                            self.apply_cost()
                            self.pos = None
                            self.state = "CANDIDATE"
                            
                    elif od['type'] == 'BUY':
                        if self.pos is None:
                            # New Position
                            self.pos = Position(ticker=tkr, entry_date=d, entry_price=px_open, erc=od.get('erc',0.0), hold_days=0, mark_price=px_open)
                            self.trades.append({'date': d, 'type': 'BUY', 'ticker': tkr, 'px': px_open, 'reason': od['reason']})
                            self.apply_cost()
                            self.state = "ACTIVE"
                            
                self.pending = []

            # -----------------------------------------------------
            # 2. MARK-TO-MARKET @ CLOSE
            # -----------------------------------------------------
            if self.pos:
                row = day_data[day_data['ticker'] == self.pos.ticker]
                if not row.empty:
                    px_close = float(row.iloc[0]['close'])
                    # MTM from Last Mark (Entry or Prev Close)
                    self.equity *= (px_close / (self.pos.mark_price + 1e-12))
                    self.pos.mark_price = px_close
                else:
                    # Missing data check can be here, or handled next day
                    pass
            
            # -----------------------------------------------------
            # 3. Decision Logic (Signal Generation)
            # -----------------------------------------------------
            is_ban = self.regime.update(self.equity)
            
            candidates = []
            for _, r in day_data.iterrows():
                erc, rr, score = compute_metrics(r)
                if score > 0:
                    candidates.append({
                        'ticker': r['ticker'], 'price': r['close'], 'erc': erc, 'rr': rr, 'score': score, 
                        'shake': r['shake_texture']
                    })
            
            candidates.sort(key=lambda x: x['score'], reverse=True)
            top5 = candidates[:5]
            top1 = top5[0] if top5 else None
            
            action = "HOLD"
            reason = ""
            suppress_entry = False
            force_exit = False
            
            if is_ban:
                if self.cfg.ban_mode == "EXIT": force_exit = True
                elif self.cfg.ban_mode == "SUPPRESS": suppress_entry = True
            
            # Signal Generation Helper
            def send_order(type_, ticker, px, reason, erc=0.0):
                if self.cfg.execution_mode == "NEXT_OPEN":
                    self.pending.append({'type': type_, 'ticker': ticker, 'reason': reason, 'erc': erc})
                    return "SIGNAL_" + type_
                else:
                    # CLOSE Execution (Theoretical)
                    if type_ == 'SELL':
                        self.trades.append({'date': d, 'type': 'SELL', 'ticker': ticker, 'px': px, 'reason': reason})
                        self.apply_cost()
                    elif type_ == 'BUY':
                        self.trades.append({'date': d, 'type': 'BUY', 'ticker': ticker, 'px': px, 'reason': reason})
                        self.apply_cost()
                    return type_

            if force_exit and self.pos:
                # Exit on BAN (Hard Close)
                # Use current ticker price for Close exec
                cur_row = day_data[day_data['ticker'] == self.pos.ticker]
                px_exit = float(cur_row.iloc[0]['close']) if not cur_row.empty else 0.0
                
                res = send_order('SELL', self.pos.ticker, px_exit, 'BAN_EXIT')
                if self.cfg.execution_mode == "CLOSE":
                    self.pos = None; self.state = "CANDIDATE"
                action = "EXIT_BAN"
            else:
                if not self.pos:
                    # ENTRY Check
                    if not suppress_entry and top1 and top1['score'] >= self.cfg.entry_threshold and top1['shake'] < self.cfg.shake_limit:
                        # Should check if we are already pending a buy? Assuming pending list cleared
                        res = send_order('BUY', top1['ticker'], top1['price'], 'ENTRY', top1['erc'])
                        if self.cfg.execution_mode == "CLOSE":
                             self.pos = Position(ticker=top1['ticker'], entry_date=d, entry_price=top1['price'], erc=top1['erc'], mark_price=top1['price'])
                             self.state = "ACTIVE"
                        action = "ENTRY"
                        reason = f"Score {top1['score']:.2f} > {self.cfg.entry_threshold:.2f}"
                
                elif self.pos:
                    self.pos.hold_days += 1
                    # Update current stats
                    cur_cand = next((c for c in candidates if c['ticker'] == self.pos.ticker), None)
                    
                    if not cur_cand: # Data missing
                         res = send_order('SELL', self.pos.ticker, 0.0, 'DATA_MISS') 
                         if self.cfg.execution_mode == "CLOSE": self.pos = None; self.state = "CANDIDATE"
                         action = "EXIT_MISSING"
                    else:
                        # EXIT Check (Exhaustion or Score Break)
                        if cur_cand['rr'] > self.cfg.exit_rr or cur_cand['score'] <= 0:
                            res = send_order('SELL', self.pos.ticker, cur_cand['price'], 'EXIT_RULE')
                            if self.cfg.execution_mode == "CLOSE": self.pos = None; self.state = "CANDIDATE"
                            action = "EXIT"
                            reason = "Exhausted/Broken"
                        else:
                            # SWITCH Check
                            if not suppress_entry and top1 and top1['ticker'] != self.pos.ticker and self.pos.hold_days >= self.cfg.min_hold_days:
                                # Gate 1: Ratio
                                ratio_pass = top1['score'] > cur_cand['score'] * self.cfg.switch_ratio
                                # Gate 2: Abs Diff
                                abs_pass = (top1['score'] - cur_cand['score']) > self.cfg.switch_abs_min
                                
                                if ratio_pass and abs_pass:
                                    # EXECUTE SWITCH
                                    send_order('SELL', self.pos.ticker, cur_cand['price'], 'SWITCH_OUT')
                                    send_order('BUY', top1['ticker'], top1['price'], 'SWITCH_IN', top1['erc'])
                                    
                                    if self.cfg.execution_mode == "CLOSE":
                                        self.pos = Position(ticker=top1['ticker'], entry_date=d, entry_price=top1['price'], erc=top1['erc'], mark_price=top1['price'])
                                    
                                    action = "SWITCH"
                                    reason = f"Diff {top1['score']-cur_cand['score']:.2f}"
            
            self.equity_curve.append({'date': d, 'equity': self.equity, 'config': self.cfg.name})
            self.logs.append({'date': d, 'equity': self.equity, 'state': self.state, 'active': self.pos.ticker if self.pos else '', 'action': action, 'reason': reason})

        return self.equity_curve, self.trades

# -----------------------------
# Main & Forensic
# -----------------------------
def analyze_true_switches(trades, name):
    if not trades:
        print(f"[{name}] No trades.")
        return
    df = pd.DataFrame(trades)
    df['date'] = pd.to_datetime(df['date'])
    
    sw_out = df[df['reason'].str.contains('SWITCH_OUT', na=False)].set_index('date')
    sw_in = df[df['reason'].str.contains('SWITCH_IN', na=False)].set_index('date')
    
    # Merge on date to see the pair
    if not sw_out.empty and not sw_in.empty:
        merged = sw_out.join(sw_in, lsuffix='_out', rsuffix='_in')
        print(f"\n[{name}] === SWITCH LOG Analysis ===")
        for dt, row in merged.iterrows():
            print(f"  {dt.strftime('%Y-%m-%d')}: Abandoned {row['ticker_out']} (${row['px_out']:.2f}) -> Chased {row['ticker_in']} (${row['px_in']:.2f})")
    
    # If Hold Strategy (Few trades), print all for analysis
    if len(df) <= 10:
        print(f"\n[{name}] === FULL TRADE LOG (Hold Focus) ===")
        for _, row in df.iterrows():
             print(f"  {row['date'].strftime('%Y-%m-%d')} {row['type']} {row['ticker']} @ {row['px']:.2f} ({row['reason']})")

    n_days = df[df['reason'].str.contains('SWITCH_IN', na=False)]['date'].nunique()
    print(f"[{name}] Summary: Trades {len(df)} | SwitchEvents {n_days}")

def main():
    data_path = os.environ.get("Q1_DATA_PATH", "GARAM_Data/60day_replay_kst")
    df = load_data(data_path)
    df = add_features(df)
    
    # 3-Way Experiment
    configs = [
        # 1. HOLD (Swiching OFF)
        Q1Config(name="Opt_F_Hold", execution_mode="NEXT_OPEN", entry_quantile=0.70, switch_abs_min=float('inf'), min_hold_days=2),
        
        # 2. SWITCH_HIGH (Q0.95 Dominance)
        # Q1Config(name="Opt_G_SwitchHigh", execution_mode="NEXT_OPEN", entry_quantile=0.70, switch_abs_quantile=0.95, min_hold_days=2),
        
        # 3. SWITCH_MID (Q0.90 Dominance) - Check Chop Tax
        # Q1Config(name="Opt_H_SwitchMid", execution_mode="NEXT_OPEN", entry_quantile=0.70, switch_abs_quantile=0.90, min_hold_days=2),
    ]
    
    all_results = []
    
    plt.figure(figsize=(12, 6))
    
    for cfg in configs:
        engine = BacktestEngine(df, cfg)
        eq_curve, trades = engine.run()
        
        analyze_true_switches(trades, cfg.name)
        
        # Plot
        dates = [x['date'] for x in eq_curve]
        eqs = [x['equity'] for x in eq_curve]
        plt.plot(dates, eqs, label=f"{cfg.name} (Ret: {(eqs[-1]-1)*100:.1f}%)")
        
        all_results.append({
            'name': cfg.name,
            'return': (eqs[-1]-1),
            'trades': len(trades)
        })
        
    plt.title("Phase Q-1 Final: Switching Value Verification")
    plt.xlabel("Date")
    plt.ylabel("Equity (Normalized)")
    plt.legend()
    plt.grid(True)
    plt.savefig("out_q1/q1_final_switch.png")
    
    print("\nVerification Complete. Results:")
    for res in all_results:
        print(f"{res['name']}: Return {res['return']*100:.2f}%, Trades {res['trades']}")

if __name__ == "__main__":
    main()
