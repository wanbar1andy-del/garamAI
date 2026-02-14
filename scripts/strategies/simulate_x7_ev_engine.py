"""
[GARAM] X-7i Hero-Turbo EV Engine (Entry Quality Optimization)
- X-7g Baseline (No partials)
- P1: Liquidity Filter (Min 3B KRW)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, time, timedelta
import sys
import logging
from collections import defaultdict, deque

PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))
from scripts.core.antigravity_x7_core import (
    EngineConfig, Stage, Position, Candidate, ScoreCalibration,
    SwitchDecision, ExitReason, SignalType, ExitDecision, StrategyMode,
    should_switch_ev_guarded, should_exit, can_reenter, 
    candidate_gate, build_switch_ledger_row, classify_stage, should_pyramid,
    TopSignalMemory, StructBreakCounter, RegimeGate,
    apply_fill_add, pnl_from_avg, mfe_from_signal, is_elite_signal,
    EngineConfig, Stage, Position, Candidate, ScoreCalibration,
    SwitchDecision, ExitReason, SignalType, ExitDecision, StrategyMode,
    should_switch_ev_guarded, should_exit, can_reenter, 
    candidate_gate, build_switch_ledger_row, classify_stage, should_pyramid,
    TopSignalMemory, StructBreakCounter, RegimeGate,
    apply_fill_add, pnl_from_avg, mfe_from_signal, is_elite_signal,
    should_exit_trend, should_enter_trend
)

DATA_DIR = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M")
OUT_DIR = PROJECT_ROOT / f"logs/x8/sim_{RUN_ID}"
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', 
                    handlers=[logging.FileHandler(OUT_DIR/"run.log"), logging.StreamHandler(sys.stdout)])

# Config
CFG = EngineConfig()
CALIB = ScoreCalibration()
INITIAL_CAPITAL = 100_000_000
SLOTS = 5
FEE = 0.0003


def net_liq(cash: float, slots: list) -> float:
    """NetLiq sizing (X-7f: 초기자본 기반 금지)"""
    v = cash
    for p in slots:
        if p is not None:
            v += p.qty * p.last_px
    return v


class X7fSimulator:
    def __init__(self):
        self.cash = INITIAL_CAPITAL
        self.slots = [None] * SLOTS  # List[Optional[Position]]
        self.equity_curve = []
        self.trades = []
        self.daily_files = None
        
        # Memory Engines
        self.sigmem = TopSignalMemory(window=CFG.persist_window)
        self.sbc = StructBreakCounter()
        
        # Regime Gate (X-7f)
        self.regime_gate = None
        
        # Lifecycle / Re-entry Memory
        self.lifecycle_mem = {}
        
        # Audit
        self.audit_coverage = []
        self.audit_switches = []

    def _get_lifecycle(self, tkr):
        if tkr not in self.lifecycle_mem:
            self.lifecycle_mem[tkr] = {'last_exit_ts': None, 'roundtrips_today': 0}
        return self.lifecycle_mem[tkr]

    def load_daily_universe(self):
        logging.info("Scanning Daily Universe (Extracting all dates)...")
        files = list(DATA_DIR.glob("*.csv"))
        file_map = [] 
        all_dates = set()
        for f in files:
            if '329180' in f.name: continue
            try:
                df = pd.read_csv(f)
                cols = df.columns
                if 'ts' in cols: df.rename(columns={'ts':'date'}, inplace=True)
                elif 'Date' in cols: df.rename(columns={'Date':'date'}, inplace=True)
                if 'close' not in df.columns or df.empty: continue
                df['date'] = pd.to_datetime(df['date'])
                unique_dates = df['date'].dt.date.unique()
                all_dates.update(unique_dates)
                for d in unique_dates:
                    file_map.append({'date': d, 'ticker': f.stem, 'path': str(f)})
            except Exception as e:
                pass
        self.daily_files = pd.DataFrame(file_map)
        logging.info(f"Universe Scanned. Found {len(all_dates)} days.")
        return sorted(list(all_dates))

    def get_minute_snapshot(self, date_obj):
        day_universe = {}
        relevant = self.daily_files[self.daily_files['date'] == date_obj]
        for _, row in relevant.iterrows():
            try:
                df = pd.read_csv(row['path'], low_memory=False)
                col_map = {'ts':'date','Date':'date'}
                df.rename(columns=col_map, inplace=True)
                df['date'] = pd.to_datetime(df['date'])
                day_df = df[df['date'].dt.date == date_obj].copy()
                if not day_df.empty:
                    day_df.set_index('date', inplace=True)
                    day_universe[row['ticker']] = day_df
            except: pass
        return day_universe

    def run(self):
        dates = self.load_daily_universe()
        # [X-7i] Turnover Memory for Liquidity Filter
        self.turnover_history = defaultdict(lambda: deque(maxlen=5)) # {tkr: deque([daily_to, ...])}
        # [X-7j] Volatility Memory (Daily Range %)
        self.volatility_history = defaultdict(lambda: deque(maxlen=5))

        # [X-8] Overnight State
        self.held_positions: list = [None] * SLOTS
        self.market_ma_20 = deque(maxlen=20)
        self.market_ma_60 = deque(maxlen=60)

        # [X-7h] Full 60-day stress test
        for d in dates:
            self.cur_date = d
            self.lifecycle_mem = {} 
            self.regime_gate = RegimeGate()  # Reset per day
            day_data = self.get_minute_snapshot(d)
            if not day_data: continue
            
            all_times = sorted(list(set().union(*[df.index for df in day_data.values()])))
            # [X-8] Regime Detection (Universe Avg Price MA)
            # Simple Proxy: Avg Close of Universe
            univ_avg_close = 0.0
            valid_closes = 0
            for df in day_data.values():
                 if not df.empty:
                     univ_avg_close += df['close'].mean()
                     valid_closes += 1
            
            if valid_closes > 0:
                avg_px = univ_avg_close / valid_closes
                self.market_ma_20.append(avg_px)
                self.market_ma_60.append(avg_px)
            
            # Decide Mode
            # Decide Mode (Shortened for Sim: MA5 vs MA20)
            # Pre-fill Logic (Hack for Sim start)
            if len(self.market_ma_60) == 1:
                # Fill deque to avoid waiting 60 days
                val = self.market_ma_60[0]
                for _ in range(59): self.market_ma_60.append(val)
                for _ in range(19): self.market_ma_20.append(val)
            
            # Use MA5 vs MA20 for faster reaction in this 3-month sim
            # Real logic should be MA20 vs MA60, but we lack history.
            # let's use the deque values we have.
            
            ma_fast = sum(list(self.market_ma_20)[-5:]) / 5
            ma_slow = sum(list(self.market_ma_20)[-20:]) / 20
            
            # Ramp-up protection
            if len(dates) < 5: 
                CFG.mode = StrategyMode.SCALP
            elif ma_fast > ma_slow * 1.005: # 0.5% buffer
                CFG.mode = StrategyMode.SWING
                logging.info(f"[Regime Gate] {d} Mode: BULL (SWING) MA5={ma_fast:.0f} > MA20={ma_slow:.0f}")
            else:
                CFG.mode = StrategyMode.SCALP
                logging.info(f"[Regime Gate] {d} Mode: BEAR (SCALP) MA5={ma_fast:.0f} < MA20={ma_slow:.0f}")

            # [X-8] Rollover Held Positions
            self.slots = [None] * SLOTS
            for idx, held_pos in enumerate(self.held_positions):
                if held_pos:
                    # Re-verify if we should keep holding (e.g. gap down check)
                    # For now, just restore.
                    self.slots[idx] = held_pos
                    # Update close price to yesterday's close (mark-to-market was done)
                    # Entry TS remains original.
            
            # Clear held positions for next day accumulation
            self.held_positions = [None] * SLOTS

            valid_times = [t for t in all_times if t.time() >= time(9,0) and t.time() <= time(15,20)]
            
            hist_c = {tkr: [] for tkr in day_data}
            hist_v = {tkr: [] for tkr in day_data}
            
            # [X-7f] Day State for Struct Break (VWAP/EMA20)
            typical_pv = {tkr: 0.0 for tkr in day_data}
            typical_v = {tkr: 0.0 for tkr in day_data}
            ema20 = {tkr: None for tkr in day_data}

            for t in valid_times:
                current_cands = []
                candidates_map = {} 

                for tkr, df in day_data.items():
                    # [X-7j] Volatility Filter (Check 5-day avg daily range)
                    if tkr in self.volatility_history and len(self.volatility_history[tkr]) > 0:
                        obs_vol = list(self.volatility_history[tkr])
                        avg_vol = sum(obs_vol) / len(obs_vol)
                        if avg_vol < CFG.min_daily_volatility:
                            continue

                    # [X-7i] Liquidity Filter (Check 5-day avg turnover)
                    # Warmup: Pass if no history yet
                    if tkr in self.turnover_history and len(self.turnover_history[tkr]) > 0:
                        obs = list(self.turnover_history[tkr])
                        avg_to = sum(obs) / len(obs)
                        if avg_to < CFG.min_daily_turnover:
                            continue

                    if t in df.index:
                        row = df.loc[t]
                        c, v = float(row['close']), float(row['volume'])
                        hist_c[tkr].append(c); hist_v[tkr].append(v)
                        if len(hist_c[tkr])>20: hist_c[tkr].pop(0); hist_v[tkr].pop(0)
                        
                        score = 0.0
                        if len(hist_c[tkr])>=5:
                            c_now = hist_c[tkr][-1]; c_prev5 = hist_c[tkr][-5]
                            ret5 = (c_now - c_prev5)/c_prev5
                            v_now = hist_v[tkr][-1]; v_avg = np.mean(hist_v[tkr])
                            v_spike = v_now / (v_avg + 1e-9) if v_avg>0 else 1.0
                            v_spike = min(v_spike, 3.0)
                            score = ret5 * v_spike * 100
                        
                        # [X-7f] Real Struct Break Calculation
                        typical_pv[tkr] += c * v
                        typical_v[tkr] += v
                        vwap = typical_pv[tkr] / (typical_v[tkr] + 1e-12)
                        
                        if ema20[tkr] is None:
                            ema20[tkr] = c
                        else:
                            alpha = 2.0 / 21.0
                            ema20[tkr] = alpha * c + (1 - alpha) * ema20[tkr]
                            
                        cand_vwap = (c >= vwap)
                        cand_ema20 = (c >= ema20[tkr])
                        
                        cand = Candidate(
                            ticker=tkr, ts=t, px=c, score=score,
                            above_vwap=cand_vwap, above_ema20=cand_ema20
                        )
                        
                        self.sigmem.update(tkr, score)
                        broken_now = (not cand.above_vwap) and (not cand.above_ema20)
                        self.sbc.update(tkr, broken_now)
                        
                        current_cands.append(cand)
                        candidates_map[tkr] = cand
                
                # Sort TopK
                current_cands.sort(key=lambda x: x.score, reverse=True)
                topk = [c for c in current_cands if c.score >= CFG.min_entry_score][:20]
                topk_10 = [c for c in topk if c.score >= CFG.regime_hero_score]
                hero_present = (len(topk_10) > 0)
                
                # [X-7f] Regime Gate Update (09:00-09:30)
                if t.time() < time(9,30):
                    self.regime_gate.update(hero_present)
                elif t.time() == time(9,30) and not self.regime_gate.finalized:
                    mode = self.regime_gate.finalize()
                    logging.info(f"[Regime Gate] {d} Mode: {mode}")
                
                regime_ok = self.regime_gate.is_regime_ok()
                
                # Audit: Coverage
                held_tickers = [p.ticker for p in self.slots if p]
                held_hero = any(tkr in held_tickers for tkr in [c.ticker for c in topk_10])
                self.audit_coverage.append({
                    'time': t, 'hero_present': hero_present, 'held_hero': held_hero,
                    'top1_score': topk[0].score if topk else 0,
                    'regime_mode': self.regime_gate.mode
                })

                # Manage Portfolio
                incumbent_indices = {}
                for i in range(SLOTS):
                    pos = self.slots[i]
                    if not pos: continue
                    incumbent_indices[pos.ticker] = i
                    
                    # [Fix] Fetch now_cand even if not in TopK (candidates_map)
                    now_cand = candidates_map.get(pos.ticker)
                    if not now_cand:
                        # Construct from raw data if available
                        if pos.ticker in day_data:
                            df_tkr = day_data[pos.ticker]
                            if t in df_tkr.index:
                                row = df_tkr.loc[t]
                                now_cand = Candidate(
                                    ts=t,
                                    ticker=pos.ticker,
                                    px=float(row['close']),
                                    open_px=float(row['open']),
                                    high_px=float(row['high']),
                                    low_px=float(row['low']),
                                    volume=float(row['volume']),
                                    score=0.0, # Not needed for exit
                                    turnover=float(row['close']) * float(row['volume']),
                                    impulse=0.0,
                                    z_score=0.0,
                                    above_vwap=False, # Dummy
                                    above_ema20=False # Dummy
                                )
                    
                    if not now_cand: continue
                    
                    # [X-7f] Update signal_high_px (stage anchor)
                    pos.last_ts = t
                    pos.last_px = now_cand.px
                    pos.signal_high_px = max(pos.signal_high_px, now_cand.px)
                    pos.low_px = min(pos.low_px, now_cand.px)
                    
                    # Update Stage
                    prev_stage = pos.stage
                    pos.stage = classify_stage(pos, now_cand, CFG)
                    if pos.stage != prev_stage:
                        pos.last_stage_change_ts = t
                    
                    # Pyramiding (regime-aware)
                    if self.regime_gate.mode != "FLAT":
                        should_pyr, next_w, reason_pyr = should_pyramid(pos, now_cand, t, CFG, CALIB, regime_ok)
                        if should_pyr:
                            self._adjust_size(i, next_w, now_cand.px, t)
                    
                    if CFG.mode == StrategyMode.SWING and pos.signal_type == SignalType.X8_TREND:
                        # Trend Exit Logic
                        ed = should_exit_trend(pos, now_cand, CFG)
                    else:
                        # Scalp Exit Logic
                        ed = should_exit(pos, now_cand, CFG, self.sigmem, self.sbc)
                    
                    if ed.exit:
                        # Full Exit
                        self._close(i, now_cand.px, t, ed.reason.value)
                        
                # Switching & Entry (regime-aware)
                if self.regime_gate.mode == "FLAT":
                     continue

                # [X-8] SWING Mode Entry
                if CFG.mode == StrategyMode.SWING:
                    # We need history df for trend check
                    # Approximation: Use day_data[tkr] which contains full day so far
                    # AND we need previous day close for accurate MA. 
                    # For sim speed, we'll approximate with current day so far.
                    # Ideally we maintain a separate daily history buffer.
                    
                    # NOTE: We construct a temporary history DF from the day_data snippet
                    # In a real engine, this would be `self.daily_history_buffer[tkr]`
                    # Here we rely on `day_data[tkr]` having enough rows is false because it's intraday.
                    # We will use `self.volatility_history` logic or just simple check.
                    # Actually, we need to load daily history.
                    # Fallback: Just check intraday alignment for now or skip if too complex for this script.
                    
                    # Correction: We loaded `dates`. We can assume we have access to daily data?
                    # No, we only load one day at a time.
                    # We will reuse `self.market_ma_*` logic styles but per ticker? No too memory heavy.
                    # FAST PATH: Logic inside `should_enter_trend` expects a DF.
                    # Let's mock it using the day_data slice up to now. 
                    # It won't have 60 days.
                    # CRITICAL FIX: We cannot implement full MA60 check without loading 60 days history.
                    # SIMPLIFICATION for SIM: We will use a "Mock Trend" logic based on 
                    # intraday VWAP alignment + simple gap check.
                    # OR we just rely on `min_daily_turnover` and `volatility` and `intraday_trend`.
                    
                    # For X-8 Sim purpose: We will use `score` as proxy for trend strength 
                    # but relax the threshold.
                    
                    # Wait/Retry: Actually we can just check if Current Px > Open > Prev Close
                    # and Volume is high.
                    
                    pass 
                
                # Scalp Mode Entry (Original X-7 logic + X-8 Fallback)
                # ...
                
                # RE-DESIGN: To properly test X-8, we need 60-day history.
                # Since we can't easily rewriting the data loader, we will use a "HeuristicX8"
                # IF Mode == SWING:
                #    Enter if Score > 5.0 (Lower threshold) AND Turnover > 100B 
                #    (Assume high score + high liquidity = trend)
                
                # We need `d_open` for the heuristic. Let's get it from `day_data` for the current ticker.
                # This needs to be inside the `for cand in topk` loop to get `now_cand`.
                # Let's move the heuristic inside the loop.

                for cand in topk:
                    # Get d_open for the current candidate
                    d_open = float(day_data[cand.ticker].iloc[0]['open']) if not day_data[cand.ticker].empty else 0.0
                    
                    if CFG.mode == StrategyMode.SWING:
                         # Heuristic X-8 Entry
                         # 1. High Liquidity (Blue Chip)
                         # Approximation: Use current day's accumulated typical_pv as turnover proxy
                         current_turnover = typical_pv.get(cand.ticker, 0.0)
                         if current_turnover > 30_000_000_000: # 30B KRW
                             # 2. Positive Price Action
                             if d_open > 0 and cand.px > d_open * 1.02: # Up 2% today
                                 # 3. Entry Signal (using score as proxy for trend strength)
                                 if cand.score >= CFG.min_entry_score_trend: # Use a specific config for trend entry score
                                     empty_idx = next((i for i,p in enumerate(self.slots) if p is None), -1)
                                     if empty_idx != -1:
                                         self._open(empty_idx, cand, t, SignalType.X8_TREND)
                                         lc = self._get_lifecycle(cand.ticker)
                                         lc['roundtrips_today'] += 1
                                         continue # Move to next candidate if entered
                                     else:
                                         # Attempt switch for trend entry
                                         best_diff = 0.0
                                         target_idx = -1
                                         audit_row = None
                                         
                                         for i, pos in enumerate(self.slots):
                                             if not pos: continue
                                             inc_now = candidates_map.get(pos.ticker)
                                             if not inc_now: continue
                                             
                                             # Use a trend-aware switch logic if available, otherwise default
                                             sd = should_switch_ev_guarded(pos, inc_now, cand, self.sigmem, CALIB, CFG)
                                             if sd.decision == "SWITCH":
                                                 if sd.ev_diff > best_diff:
                                                     best_diff = sd.ev_diff
                                                     target_idx = i
                                                     audit_row = build_switch_ledger_row(t, pos, inc_now, cand, sd)
                                         
                                         if target_idx != -1:
                                             loser = self.slots[target_idx]
                                             self._close(target_idx, loser.last_px, t, "EV_SWITCH")
                                             lc_loser = self._get_lifecycle(loser.ticker)
                                             lc_loser['last_exit_ts'] = t

                                             self._open(target_idx, cand, t, SignalType.X8_TREND)
                                             lc = self._get_lifecycle(cand.ticker)
                                             lc['roundtrips_today'] += 1
                                             if audit_row: self.audit_switches.append(audit_row)
                                             continue # Move to next candidate if entered

                    # Normal X-7 Entry (Scalp or Fallback for Swing if X-8 heuristic not met)
                    ok_gate, reason_gate, _ = candidate_gate(cand, CALIB, CFG)
                    if not ok_gate: continue 
                    
                    if cand.ticker in incumbent_indices: continue
                    
                    lc = self._get_lifecycle(cand.ticker)
                    ok_re, reason_re = can_reenter(lc['last_exit_ts'], lc['roundtrips_today'], cand, CFG)
                    if not ok_re: continue

                    # [X-7g] Entry Persistence Check (using config values)
                    if not self.sigmem.persistent(cand.ticker, threshold=CFG.entry_persist_score, need=CFG.entry_persist_need):
                        continue

                    empty_idx = next((i for i,p in enumerate(self.slots) if p is None), -1)
                    if empty_idx != -1:
                        self._open(empty_idx, cand, t, SignalType.X7_STRUCTURE)
                        lc['roundtrips_today'] += 1
                    else:
                        # [X-7f] Guarded Switch Logic (disabled on PROBE_ONLY)
                        if self.regime_gate.mode == "PROBE_ONLY":
                            continue
                            
                        best_diff = 0.0
                        target_idx = -1
                        audit_row = None
                        
                        for i, pos in enumerate(self.slots):
                            if not pos: continue
                            inc_now = candidates_map.get(pos.ticker)
                            if not inc_now: continue
                            
                            sd = should_switch_ev_guarded(pos, inc_now, cand, self.sigmem, CALIB, CFG)
                            if sd.decision == "SWITCH":
                                if sd.ev_diff > best_diff:
                                    best_diff = sd.ev_diff
                                    target_idx = i
                                    audit_row = build_switch_ledger_row(t, pos, inc_now, cand, sd)
                        
                        if target_idx != -1:
                            loser = self.slots[target_idx]
                            self._close(target_idx, loser.last_px, t, "EV_SWITCH")
                            lc_loser = self._get_lifecycle(loser.ticker)
                            lc_loser['last_exit_ts'] = t

                            self._open(target_idx, cand, t, SignalType.X7_STRUCTURE)
                            lc['roundtrips_today'] += 1
                            if audit_row: self.audit_switches.append(audit_row)

            # End of Day Close (Force Close Scapls, Hold Swings)
            if valid_times:
                last_ts = valid_times[-1]
                for i in range(SLOTS):
                    p = self.slots[i]
                    if p:
                        # [X-8] Overnight Check
                        if CFG.mode == StrategyMode.SWING and p.signal_type == SignalType.X8_TREND:
                            # Hold!
                            self.held_positions[i] = p
                            # Mark-to-Market PnL (Virtual Close) for Equity Curve
                            # We don't sell, but we record equity based on last px
                            pass 
                        else:
                            self._close(i, p.last_px, last_ts, "EOD")
            
            self._record_equity(d)
            
            # [X-7i] Update Turnover Memory (using accumulated typical_pv)
            # [X-7j] Update Volatility Memory (H-L/O from daily agg or just use day_data if efficient)
            for tkr, df in day_data.items():
                # Turnover
                day_turnover = typical_pv.get(tkr, 0.0)
                if day_turnover > 0:
                    self.turnover_history[tkr].append(day_turnover)
                
                # Volatility: We need daily OHLC. Approximation from min data:
                # We used `df` which contains the whole day.
                if not df.empty:
                    d_open = float(df.iloc[0]['open'])
                    d_high = float(df['high'].max())
                    d_low = float(df['low'].min())
                    if d_open > 0:
                        rng = (d_high - d_low) / d_open
                        self.volatility_history[tkr].append(rng)

            logging.info(f"Day Complete: {d} | Cash: {self.cash:,.0f} | Final Equity: {self.equity_curve[-1]['equity']:,.0f}")

    def _open(self, idx, cand: Candidate, t, signal_type: SignalType):
        """[X-7f] Position with signal_px/avg_px separation"""
        nl = net_liq(self.cash, self.slots)
        target_w = CFG.probe_weight
        alloc = nl * target_w
        if self.cash < alloc: alloc = self.cash
        qty = int(alloc / (cand.px * (1+FEE)))
        if qty <= 0: return
        
        cost = qty * cand.px * (1+FEE)
        self.cash -= cost
        self.slots[idx] = Position(
            ticker=cand.ticker,
            entry_ts=t,
            signal_px=cand.px,        # Stage anchor (never changes)
            signal_high_px=cand.px,
            avg_px=cand.px,           # Cost basis (updated on pyramid)
            qty=qty,
            last_ts=t,
            last_px=cand.px,
            low_px=cand.px,
            score_entry=cand.score,
            stage=Stage.CANDIDATE,
            weight=target_w,
            max_weight=target_w,
            last_add_ts=t,
            signal_type=signal_type
        )

    def _adjust_size(self, idx, target_w, px, t):
        """[X-7f] NetLiq sizing + apply_fill_add (P0 fix)"""
        pos = self.slots[idx]
        nl = net_liq(self.cash, self.slots)
        
        target_value = nl * target_w
        current_value = pos.qty * px
        add_value = target_value - current_value
        if add_value <= 0:
            return

        add_value = min(add_value, self.cash)
        add_qty = int(add_value / (px * (1+FEE)))
        if add_qty <= 0:
            return

        cost = add_qty * px * (1+FEE)
        self.cash -= cost

        # [X-7f P0] Update avg_px using weighted average
        apply_fill_add(pos, add_qty, px)

        pos.weight = (pos.qty * px) / nl if nl > 0 else pos.weight
        pos.last_add_ts = t
        pos.max_weight = max(pos.max_weight, pos.weight)

    def _close(self, idx, px, t, reason):
        p = self.slots[idx]
        proceeds = p.qty * px * (1-FEE)
        self.cash += proceeds
        
        # [X-7f] PnL from avg_px (correct)
        pnl = pnl_from_avg(p, px)
        
        self.trades.append({
            'date': self.cur_date, 'time': t, 'ticker': p.ticker,
            'pnl_pct': pnl, 'reason': reason, 'qty': p.qty
        })
        self.slots[idx] = None

        
        # Update Position
        # p.qty -= close_qty
        # p.partial_taken_qty += close_qty

    def _record_equity(self, d):
        val = net_liq(self.cash, self.slots)
        self.equity_curve.append({'date': d, 'equity': val})

    def report(self):
        if not self.equity_curve: return
        final = self.equity_curve[-1]['equity']
        ret = (final - INITIAL_CAPITAL)/INITIAL_CAPITAL
        tr = pd.DataFrame(self.trades)
        
        pd.DataFrame(self.audit_coverage).to_csv(OUT_DIR/"audit_coverage.csv", index=False)
        pd.DataFrame(self.audit_switches).to_csv(OUT_DIR/"audit_switches.csv", index=False)
        tr.to_csv(OUT_DIR/"trades.csv", index=False)
        
        msg = f"""
        [X-7h Profit Maximization Sim]
        Return: {ret*100:.2f}%
        Trades: {len(tr)}
        Switches: {len(self.audit_switches)}
        WinRate: {(tr['pnl_pct']>0).mean()*100:.1f}%

        [Exit Breakdown]
        {tr['reason'].value_counts().to_string() if not tr.empty else "No trades"}
        """
        print(msg)
        (OUT_DIR/"summary.txt").write_text(msg)
        df = pd.DataFrame(self.equity_curve)
        plt.figure(figsize=(10,6))
        plt.plot(df['date'], df['equity'])
        plt.title(f"X-7f Equity ({ret*100:.2f}%)")
        plt.savefig(OUT_DIR/"equity.png")

if __name__ == "__main__":
    sim = X7fSimulator()
    sim.run()
    sim.report()
