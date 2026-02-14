import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
from datetime import datetime, timedelta

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

class AuditSimulatorV2:
    def __init__(self, start_date, end_date, cost_bps=10, execution_delay=1):
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        self.cost_rate = cost_bps / 10000.0
        self.execution_delay = execution_delay 
        
        self.initial_capital = 10_000_000.0
        self.capital = 10_000_000.0
        self.shares = 0
        self.holding_symbol = None
        self.holding_entry_time = None
        
        self.trades = []
        self.entry_price = 0.0
        
        # Policy Config
        self.N_entry = 3
        self.K_hold = 3
        self.M_exit = 2
        self.cooldown_min = 5
        self.last_switch_time = None
        
        # State
        self.top1_continuity = 0
        self.hold_out_continuity = 0
        self.last_top1 = None
        
        # Oracle Data (For Death Audit & Regret)
        self.hero_segments = self.load_all_hero_segments()
        self.death_records = []
        self.regret_records = []
        
        # Output
        self.out_dir = project_root / "results" / "audit" / "week1_v2"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
    def load_all_hero_segments(self):
        # Load hero_segments.csv for the week to map "True End Time"
        segments = []
        current = self.start_date
        while current <= self.end_date:
            ymd = current.strftime("%Y%m%d")
            path = project_root / "results" / "labels" / f"day={ymd}" / "hero_segments.csv"
            if path.exists():
                df = pd.read_csv(path)
                df['start_time'] = pd.to_datetime(df['start_time'])
                df['end_time'] = pd.to_datetime(df['end_time'])
                segments.append(df)
            current += timedelta(days=1)
        
        if segments:
            return pd.concat(segments, ignore_index=True)
        return pd.DataFrame()

    def find_overlapping_segment(self, symbol, entry_time):
        if self.hero_segments.empty:
            return None
        # strict: segment must start <= entry_time <= segment end?
        # or just segment covers this period
        mask = (self.hero_segments['symbol'].astype(str).str.zfill(6) == str(symbol).zfill(6)) & \
               (self.hero_segments['start_time'] <= entry_time) & \
               (self.hero_segments['end_time'] >= entry_time)
        matched = self.hero_segments[mask]
        if not matched.empty:
            return matched.iloc[0]
        return None

    def run(self):
        print(f"Running Audit V2 ({self.start_date.date()} ~ {self.end_date.date()}) | Cost={self.cost_rate*10000:.0f}bps")
        
        current = self.start_date
        while current <= self.end_date:
            self.run_day(current)
            current += timedelta(days=1)
            
        self.force_close_all()
        self.finalize()

    def run_day(self, date_ts):
        ymd = date_ts.strftime("%Y%m%d")
        print(f"Processing {ymd}...")
        
        # Load Candidates (from Rank) & Price Map
        rank_path = project_root / "results" / "labels" / f"day={ymd}" / "hero_rank.csv"
        candidate_symbols = []
        if rank_path.exists():
            candidate_symbols = pd.read_csv(rank_path)['symbol'].unique()
            
        price_map = {}
        for sym in candidate_symbols:
            p = project_root / "GARAM_Data" / "history" / "minute" / f"{str(sym).zfill(6)}.csv"
            if p.exists():
                try:
                    df = pd.read_csv(p, usecols=['date', 'close'])
                    df = df[df['date'].astype(str).str.startswith(ymd)].copy()
                    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S', errors='coerce') # Handle mixed format if any
                    df.dropna(subset=['date', 'close'], inplace=True)
                    price_map[str(sym).zfill(6)] = df.set_index('date')['close']
                except: pass
        
        # Session Loop
        session_idx = pd.date_range(f"{ymd} 09:00", f"{ymd} 15:30", freq="1T")
        
        for t in session_idx:
            # 1. Calc Top-1 (Momentum 30m)
            t_prev = t - timedelta(minutes=30)
            ranks = []
            for sym, series in price_map.items():
                try:
                    p_now = series.asof(t)
                    p_prev = series.asof(t_prev)
                    if pd.notna(p_now) and pd.notna(p_prev) and p_prev > 0:
                        ret = (p_now / p_prev) - 1.0
                        ranks.append((sym, ret))
                except: pass
            
            ranks.sort(key=lambda x: x[1], reverse=True)
            top_list = [r[0] for r in ranks[:10]]
            current_top1 = top_list[0] if top_list else None
            top1_ret = ranks[0][1] if ranks else 0.0
            
            # --- Opportunity Regret Metric ---
            holding_ret = 0.0
            if self.holding_symbol:
                # Calculate metric for holding symbol (30m ret)
                series = price_map.get(self.holding_symbol)
                if series is not None:
                     p_now = series.asof(t)
                     p_prev = series.asof(t_prev)
                     if pd.notna(p_now) and pd.notna(p_prev) and p_prev > 0:
                         holding_ret = (p_now / p_prev) - 1.0
            
            regret = top1_ret - holding_ret
            self.regret_records.append({
                "time": t,
                "top1_symbol": current_top1,
                "holding_symbol": self.holding_symbol,
                "top1_ret": top1_ret,
                "holding_ret": holding_ret,
                "regret": regret
            })
            # ----------------------------------

            # 2. Update Policy State
            if current_top1:
                if current_top1 == self.last_top1:
                    self.top1_continuity += 1
                else:
                    self.top1_continuity = 1
                    self.last_top1 = current_top1
            else:
                self.top1_continuity = 0
            
            # 3. Execution Logic
            if self.holding_symbol:
                is_in_top_k = self.holding_symbol in top_list[:self.K_hold]
                if not is_in_top_k:
                    self.hold_out_continuity += 1
                else:
                    self.hold_out_continuity = 0
                
                if self.hold_out_continuity >= self.M_exit and self.top1_continuity >= self.N_entry:
                    self.execute_trade(t, "SELL", self.holding_symbol, "switch", price_map)
            
            if not self.holding_symbol:
                if self.last_switch_time and (t - self.last_switch_time).total_seconds()/60 < self.cooldown_min:
                    continue
                if self.top1_continuity >= self.N_entry:
                    self.execute_trade(t, "BUY", self.last_top1, "enter", price_map)
                    self.last_switch_time = t

    def execute_trade(self, time, side, symbol, reason, price_map):
        series = price_map.get(symbol)
        # Handle Force Close (series might be passed as simple dict)
        if isinstance(price_map.get(symbol), pd.Series) == False: 
            # Fallback for force close manual dict
             exec_price = list(price_map[symbol].values())[0] if symbol in price_map else 0
             exec_time = time # Force close is immediate/EOD
        else:
            exec_time = time + timedelta(minutes=self.execution_delay)
            if series is not None and exec_time in series.index:
                exec_price = series.loc[exec_time]
            elif series is not None:
                 exec_price = series.asof(exec_time)
            else:
                 exec_price = 0
        
        if pd.isna(exec_price) or exec_price <= 0: return

        if side == "BUY":
            cost_amt = self.capital * (self.cost_rate / 2)
            net_capital = self.capital - cost_amt
            self.shares = net_capital / exec_price # Precise Qty (Float)
            self.entry_price = exec_price
            self.holding_symbol = symbol
            self.holding_entry_time = exec_time
            
            self.capital = 0
            
            self.trades.append({
                "date": time.date(), "time": exec_time, "symbol": symbol, "side": "BUY",
                "qty": self.shares, "price": exec_price, 
                "fee": -cost_amt, # Cost is negative
                "tax": 0.0, 
                "gross_pnl": 0.0, "net_pnl": -cost_amt, 
                "balance": net_capital, "reason": reason
            })
            
        elif side == "SELL":
            gross_val = self.shares * exec_price
            cost_amt = gross_val * (self.cost_rate / 2)
            net_proceeds = gross_val - cost_amt
            
            gross_pnl = (exec_price - self.entry_price) * self.shares
            net_pnl = gross_pnl - cost_amt # Entry fee already booked
            
            # --- Death Audit Metric ---
            # Now we exited. Was it late?
            seg = self.find_overlapping_segment(symbol, self.holding_entry_time)
            if seg is not None:
                seg_end = seg['end_time']
                reaction_time = (seg_end - exec_time).total_seconds() / 60.0
                # Protected PnL: PnL if exited at end_time vs Actual
                # Need price at seg_end
                p_at_end = series.asof(seg_end) if series is not None else self.entry_price
                pnl_at_end = (p_at_end - self.entry_price) * self.shares
                protected_pnl = pnl_at_end - gross_pnl # If +ve, we lost money by exiting late/early?
                # Definition: protected_pnl = PnL_if_ideal - PnL_actual.
                # If ideal (end time) was 100, actual 80, protected = 20 (Opportunity Loss).
                # If actual was 80, ideal was 60 (price dropped), protected = -20 (We saved 20).
                # Wait, "Fast Exit" means we avoided drop. So Actual > Ideal (if drop).
                # Let's stick to reaction_time: +ve = Early Exit (Good if price drops later). -ve = Late Exit.
                
                self.death_records.append({
                    "symbol": symbol,
                    "entry_time": self.holding_entry_time,
                    "exit_time": exec_time,
                    "segment_end_time": seg_end,
                    "reaction_time": reaction_time,
                    "actual_pnl": net_pnl,
                    "ideal_price_at_end": p_at_end
                })
            else:
                 # False positive entry (No matching segment)
                 self.death_records.append({
                    "symbol": symbol,
                    "entry_time": self.holding_entry_time,
                    "exit_time": exec_time,
                    "segment_end_time": pd.NaT,
                    "reaction_time": 0, # N/A
                    "actual_pnl": net_pnl,
                    "ideal_price_at_end": 0
                })
            # ---------------------------

            self.capital = net_proceeds
            self.shares = 0
            self.holding_symbol = None
            self.holding_entry_time = None
            
            self.trades.append({
                "date": time.date(), "time": exec_time, "symbol": symbol, "side": "SELL",
                "qty": self.shares, "price": exec_price, 
                "fee": -cost_amt, 
                "tax": 0.0, 
                "gross_pnl": gross_pnl, "net_pnl": net_pnl, 
                "balance": self.capital, "reason": reason
            })

    def force_close_all(self):
        if self.holding_symbol:
            # EOD/End of Sim Force Close
            # Assume strict EOD: 15:30.
            # But run_day loop goes up to 15:30.
            # So this is for multi-day carry over (if any) or final cleanup.
            close_time = self.end_date + timedelta(hours=15, minutes=35) # 15:35
            print(f"Force closing {self.holding_symbol} at {close_time}")
            # Use entry price as fallback MTM to avoid PnL distortion if data missing
            self.execute_trade(close_time, "SELL", self.holding_symbol, "force_close", {self.holding_symbol: pd.Series({close_time: self.entry_price})})

    def finalize(self):
        # Save Artifacts
        pd.DataFrame(self.trades).to_csv(self.out_dir / f"trades_week1_cost{int(self.cost_rate*10000)}.csv", index=False)
        pd.DataFrame(self.death_records).to_csv(self.out_dir / f"death_audit_week1.csv", index=False)
        pd.DataFrame(self.regret_records).to_csv(self.out_dir / f"opportunity_regret_week1.csv", index=False)
        
        # Recon
        sum_net_pnl = sum(t['net_pnl'] for t in self.trades)
        start_eq = self.initial_capital
        end_eq = self.capital
        discrepancy = end_eq - (start_eq + sum_net_pnl)
        
        recon = {
            "equity_start": start_eq,
            "equity_end": end_eq,
            "sum_net_pnl": sum_net_pnl,
            "discrepancy": discrepancy,
            "pass": bool(abs(discrepancy) < 1.0),
            "trade_count": len(self.trades),
            "fee_total": sum(t['fee'] for t in self.trades)
        }
        with open(self.out_dir / f"pnl_reconciliation_week1_cost{int(self.cost_rate*10000)}.json", "w") as f:
            json.dump(recon, f, indent=4)
            
        print(f"[Audit V2 Complete] Cost={int(self.cost_rate*10000)}bps | Pass={recon['pass']}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--cost", type=float, default=10.0)
    args = parser.parse_args()
    
    sim = AuditSimulatorV2("2025-12-15", "2025-12-18", cost_bps=args.cost)
    sim.run()
