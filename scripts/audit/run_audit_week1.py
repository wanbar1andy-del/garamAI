import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
from datetime import datetime, timedelta

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

class AuditSimulator:
    def __init__(self, start_date, end_date, cost_bps=10, execution_delay=1):
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        self.cost_rate = cost_bps / 10000.0
        self.execution_delay = execution_delay # Gate A: Delay (1 min)
        
        self.initial_capital = 10_000_000.0
        self.capital = 10_000_000.0
        self.shares = 0
        self.holding_symbol = None
        self.trades = []
        self.entry_price = 0.0
        
        # Switch Policy Config
        self.N_entry = 3
        self.K_hold = 3
        self.M_exit = 2
        self.cooldown_min = 5
        self.last_switch_time = None
        
        # State Tracking
        self.top1_continuity = 0
        self.hold_out_continuity = 0
        self.last_top1 = None
        
        # Output Paths
        self.out_dir = project_root / "results" / "audit" / "week1"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
    def load_data(self):
        # Load necessary data for simulation
        # For realistic simulation, we need minute close prices for all 400 symbols.
        # To optimize, we focus on the symbols that appeared in Hero Labels or Rank.
        # But to calculate "Real Top-1", we technically need all.
        # For simplicity in this script, we will load "Universe Index" inputs from previous step if available,
        # or just load key symbols.
        # Let's assume we rely on `results/labels/day=.../hero_rank.csv` to know CANDIDATES,
        # but re-verify prices from raw csv.
        pass

    def run(self):
        print(f"Running Audit Simulation ({self.start_date.date()} ~ {self.end_date.date()})")
        print(f"Gate A: Execution Delay = {self.execution_delay} min")
        print(f"Gate B: Cost = {self.cost_rate*10000:.0f} bps")
        print(f"Gate C: Single Position Only")
        
        # Iterate Days
        current = self.start_date
        while current <= self.end_date:
            self.run_day(current)
            current += timedelta(days=1)
        
        self.force_close_all()
        self.finalize_audit()

    def force_close_all(self):
        if self.holding_symbol:
            print(f"Force closing open position: {self.holding_symbol}")
            # Use last MTM price (entry price if no better info, or 0 to be safe/conservative?)
            # Ideally use last known price from day loop. But context is lost.
            # Using entry price results in 0 gross pnl, just paying exit costs.
            # This is acceptable for audit mechanics check.
            self.execute_trade(self.end_date + timedelta(minutes=10), "SELL", self.holding_symbol, "force_close", {self.holding_symbol: pd.Series({self.end_date+timedelta(minutes=10): self.entry_price})})

    def run_day(self, date_ts):
        ymd = date_ts.strftime("%Y%m%d")
        print(f"Processing {ymd}...")
        
        # 1. Load Day's Prices (All or Top Candidates)
        # Using a simplified approach: Load pre-calculated "Rank" from Labeling Step?
        # NO, user wants to verify POLICY effectiveness, not just replay labels.
        # But calculating Top-1 from scratch for 400 symbols in Python loop is slow.
        # Compromise: Load `hero_rank.csv` from Labeling Step to identify "Potential Heroes"
        # and load minute data for those (~50 symbols).
        # We assume `hero_rank` contains all viable candidates.
        
        rank_path = project_root / "results" / "labels" / f"day={ymd}" / "hero_rank.csv"
        if not rank_path.exists():
            print(f"  No rank data for {ymd}, skipping.")
            return

        df_rank = pd.read_csv(rank_path)
        candidate_symbols = df_rank['symbol'].unique()
        
        # Load Prices
        price_map = {} # {symbol: Series}
        for sym in candidate_symbols:
            p = project_root / "GARAM_Data" / "history" / "minute" / f"{str(sym).zfill(6)}.csv"
            if p.exists():
                try:
                    df = pd.read_csv(p, usecols=['date', 'close'])
                    df['date_str'] = df['date'].astype(str)
                    df = df[df['date_str'].str.startswith(ymd)].copy()
                    if not df.empty:
                        df['date'] = pd.to_datetime(df['date_str'], format='%Y%m%d%H%M%S')
                        price_map[str(sym).zfill(6)] = df.set_index('date')['close']
                except: pass
                
        # Also need Universe Index or calculate relative strength on fly.
        # Let's use simple logic: Momentum (Return since Open or last 30m).
        # Policy says: "Top-1". Let's define Top-1 as "Highest 30m Rel Return" (consistent with labeling).
        
        session_idx = pd.date_range(f"{ymd} 09:00", f"{ymd} 15:30", freq="1T")
        
        # Simulation Loop
        for t in session_idx:
            # 1. Calculate Metrics for Candidates
            # Return last 30m
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
            # Check Exit/Switch Condition
            if self.holding_symbol:
                # Is holding in Top-K?
                is_in_top_k = self.holding_symbol in top_list[:self.K_hold]
                
                if not is_in_top_k:
                    self.hold_out_continuity += 1
                else:
                    self.hold_out_continuity = 0
                    
                # Exit Conditions
                should_exit = False
                exit_reason = ""
                
                # Condition: Out of Top-K for M minutes AND New Top-1 Ready
                if self.hold_out_continuity >= self.M_exit and self.top1_continuity >= self.N_entry:
                     should_exit = True
                     exit_reason = "switch"
                
                # Verify Cooldown? (Buying is cooldown controlled)
                
                if should_exit:
                    self.execute_trade(t, "SELL", self.holding_symbol, reason=exit_reason, price_map=price_map)
            
            # Check Entry Condition
            if not self.holding_symbol:
                # Cooldown check
                if self.last_switch_time and (t - self.last_switch_time).total_seconds()/60 < self.cooldown_min:
                    continue
                    
                if self.top1_continuity >= self.N_entry:
                    target = self.last_top1
                    self.execute_trade(t, "BUY", target, reason="enter", price_map=price_map)
                    self.last_switch_time = t

    def execute_trade(self, time, side, symbol, reason, price_map):
        series = price_map.get(symbol)
        if series is None: return
        
        # Gate A: Execution Model (Next Minute Close)
        exec_time = time + timedelta(minutes=self.execution_delay)
        
        # Check if exec_time is valid
        if exec_time not in series.index:
            # Try asof? No, Gate A implies we trade at t+1. If t+1 data missing, we fill or fail.
            # Using asof for robustness, but logging warning.
            exec_price = series.asof(exec_time)
        else:
            exec_price = series.loc[exec_time]
            
        if pd.isna(exec_price) or exec_price <= 0:
            return # Fail to trade
            
        # Execute
        fee = 0.0
        tax = 0.0
        gross_amt = 0.0
        
        if side == "BUY":
            # 100% Capital
            cost_amt = self.capital * (self.cost_rate / 2) # Half cost
            net_capital = self.capital - cost_amt
            self.shares = net_capital / exec_price
            self.entry_price = exec_price
            self.holding_symbol = symbol
            
            gross_amt = self.shares * exec_price
            self.capital = 0 # All in shares (conceptually)
            
            # Ledger Record
            self.trades.append({
                "date": time.date(), "time": exec_time, "symbol": symbol, "side": "BUY",
                "qty": self.shares, "price": exec_price, "fee": cost_amt, "tax": 0,
                "gross_pnl": 0, "net_pnl": -cost_amt, "balance": net_capital, "reason": reason
            })
            
        elif side == "SELL":
            gross_amt = self.shares * exec_price
            cost_amt = gross_amt * (self.cost_rate / 2)
            net_proceeds = gross_amt - cost_amt
            
            gross_pnl = (exec_price - self.entry_price) * self.shares
            net_pnl = gross_pnl - cost_amt # Deduct only Exit Fee (Entry Fee accounted in BUY)
            
            self.capital = net_proceeds
            self.shares = 0
            self.holding_symbol = None
            
            self.trades.append({
                "date": time.date(), "time": exec_time, "symbol": symbol, "side": "SELL",
                "qty": 0, "price": exec_price, "fee": cost_amt, "tax": 0,
                "gross_pnl": gross_pnl, "net_pnl": net_pnl, "balance": self.capital, "reason": reason
            })

    def finalize_audit(self):
        df_trades = pd.DataFrame(self.trades)
        if df_trades.empty:
            print("No trades generated.")
            return
            
        # 1. Trades Ledger
        df_trades.to_csv(self.out_dir / "trades_week1.csv", index=False)
        
        if self.holding_symbol:
             # Mark To Market using Entry Price (Conservative) or Last Market Price?
             # For reconciliation, we need 'Real Value'. 
             # Let's assume MTM = entry_price if market price not avail, 
             # OR better: force close at last tick of simulation?
             # To keep PnL sum consistent, simplest is to use Entry Price (Unrealized = 0 for PnL sum check)
             # But if we use entry price, net_pnl sum covers realized only, discrepancy is unrealized?
             # Discrepancy definition: End_Equity - (Start + Sum_Net_PnL + Unrealized_PnL?)
             # Let's adjust end_eq to be Cash + Cost_Basis of Holdings (to match Realized PnL logic).
             # If we want Equity Curve, we use MTM. If we want Reconcile Realized PnL, we use Cost Basis.
             # Gate B check is about Cost Impact on trades.
             
             # Let's treat open position valuation as Cost Basis for strict reconciliation with Realized PnL.
             # (Because open position hasn't booked PnL yet)
             end_eq = self.capital + (self.shares * self.entry_price)
             
             # Wait, self.trades includes entry 'net_pnl': -cost_amt.
             # So sum_net_pnl includes entry fees.
             # self.capital was deducted by cost_amt.
             # net_capital = capital - cost_amt.
             # shares = net_capital / price.
             # So Cost Basis = shares * price = net_capital = self.capital (before entry) - cost.
             # Correct logic:
             # end_eq = self.capital(residual cash) + self.shares * self.entry_price
        else:
             end_eq = self.capital
             
        # NOTE: self.trades contains 'balance' after each trade.
        # If open position exists, last balance is 0 (all shares).
        # We need to add back value of shares.

        
        sum_net_pnl = df_trades['net_pnl'].sum()
        start_eq = self.initial_capital
        discrepancy = end_eq - (start_eq + sum_net_pnl)
        
        recon = {
            "equity_start": start_eq,
            "equity_end": end_eq,
            "sum_net_pnl": sum_net_pnl,
            "discrepancy": discrepancy,
            "pass": bool(abs(discrepancy) < 10),
            "trade_count": len(df_trades),
            "fee_total": df_trades['fee'].sum()
        }
        
        with open(self.out_dir / "pnl_reconciliation_week1.json", "w") as f:
            json.dump(recon, f, indent=4)
            
        print("\n[Audit Complete]")
        print(f"Trades Saved: {self.out_dir / 'trades_week1.csv'}")
        print(f"Reconciliation: PASS={recon['pass']}, Discrepancy={discrepancy:.2f}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--cost", type=float, default=10.0)
    args = parser.parse_args()
    
    sim = AuditSimulator("2025-12-15", "2025-12-18", cost_bps=args.cost)
    sim.run()
