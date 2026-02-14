import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
from datetime import datetime, timedelta

# Setup Paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

class PolicyV1Simulator:
    def __init__(self, start_date, end_date, cost_bps=10, execution_delay=1):
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        self.cost_rate = cost_bps / 10000.0
        self.execution_delay = execution_delay 
        
        self.initial_capital = 10_000_000.0
        self.capital = 10_000_000.0
        self.shares = 0
        self.holding_symbol = None
        self.entry_price = 0.0
        
        # Policy V1 Params (from JSON)
        self.ENTRY_RANK_TOP = 5
        self.ENTRY_ROC_MAX = -0.0015 # -0.15% Pullback
        self.ENTRY_VOL_MIN = 0.8
        
        self.EXIT_VWAP_DIV_MIN = 0.005 # +0.5% Take Profit
        self.EXIT_ROC_MAX = -0.002 # -0.2% Stop Loss (Momentum Crash)
        
        self.trades = []
        
        # Output
        self.out_dir = project_root / "results" / "simulation" / "week1_v1"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
    def run(self):
        print(f"Running Policy v1 Simulation ({self.start_date.date()} ~ {self.end_date.date()}) | Cost={self.cost_rate*10000:.0f}bps")
        print(f"Policy: Pullback_Sniper (Enter < {self.ENTRY_ROC_MAX*100}%, Exit > {self.EXIT_VWAP_DIV_MIN*100}% VWAP)")
        
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
            
        price_map = {} # {symbol: DataFrame}
        for sym in candidate_symbols:
            p = project_root / "GARAM_Data" / "history" / "minute" / f"{str(sym).zfill(6)}.csv"
            if p.exists():
                try:
                    df = pd.read_csv(p, usecols=['date', 'close', 'volume']) # Added volume
                    df = df[df['date'].astype(str).str.startswith(ymd)].copy()
                    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S', errors='coerce')
                    df.dropna(subset=['date', 'close'], inplace=True)
                    df.set_index('date', inplace=True)
                    price_map[str(sym).zfill(6)] = df
                except: pass
        
        # Session Loop
        session_idx = pd.date_range(f"{ymd} 09:00", f"{ymd} 15:30", freq="1T")
        
        for t in session_idx:
            # 1. Calc Metrics for Candidates
            # Need to calc Roc5m, VolAccel for all candidates
            
            candidates_metrics = []
            
            # Optimization: Pre-calc ranks?
            # Doing it per minute is slow but correct for simulation.
            
            t_prev_30 = t - timedelta(minutes=30)
            t_prev_5 = t - timedelta(minutes=5)
            
            for sym, df in price_map.items():
                if t not in df.index: continue
                # We need historical data for features
                # Use slicing (window)
                
                # Rank Metric (30m momentum)
                try:
                    p_now = df['close'].asof(t)
                    p_prev_30 = df['close'].asof(t_prev_30)
                    ret_30 = (p_now / p_prev_30) - 1.0 if pd.notna(p_prev_30) and p_prev_30 > 0 else -999
                    
                    # Policy Features
                    p_prev_5 = df['close'].asof(t_prev_5)
                    roc_5m = (p_now / p_prev_5) - 1.0 if pd.notna(p_prev_5) and p_prev_5 > 0 else 0
                    
                    # Vol Accel: Current Vol / MA_10
                    # Need recent slice
                    t_win_start = t - timedelta(minutes=10)
                    vol_slice = df['volume'].loc[t_win_start:t]
                    curr_vol = df['volume'].at[t]
                    vol_ma = vol_slice.mean()
                    vol_accel = curr_vol / vol_ma if vol_ma > 0 else 0
                    
                    # VWAP Div
                    # Need VWAP from open. 
                    # Approx: use Cumulative sum of PV since loaded start (09:00)
                    # Since df is daily slice, cumsum works.
                    # Optimization: Don't recalc full cumsum every tick.
                    # Just use the pre-calclated day vwap if possible, or simple approximation.
                    # Let's do simple cumsum on full dataframe ONCE? No, lookahead.
                    # Do "asof" approach?
                    # Let's calc VWAP up to t using slice. `df.loc[:t]` is strictly past.
                    # But slow.
                    # Approx: VWAP ~ MA(60)? No.
                    # Let's assume we maintain VWAP state? Too complex for python loop script.
                    # Let's use simple slice cumsum for today.
                    df_sofar = df.loc[:t]
                    cum_vol = df_sofar['volume'].sum()
                    cum_pv = (df_sofar['close'] * df_sofar['volume']).sum()
                    vwap = cum_pv / cum_vol if cum_vol > 0 else p_now
                    vwap_div = (p_now / vwap) - 1.0
                    
                    candidates_metrics.append({
                        "symbol": sym,
                        "ret_30": ret_30,
                        "roc_5m": roc_5m,
                        "vol_accel": vol_accel,
                        "vwap_div": vwap_div,
                        "price": p_now
                    })
                except: pass
            
            # Sort by Rank (ret_30)
            candidates_metrics.sort(key=lambda x: x['ret_30'], reverse=True)
            
            # Identify Top-K
            top_list = candidates_metrics[:self.ENTRY_RANK_TOP]
            top_symbols = [x['symbol'] for x in top_list]
            
            # 2. Execution Logic
            
            # A. Exit Check
            if self.holding_symbol:
                # Find metrics for holding symbol
                h_metrics = next((x for x in candidates_metrics if x['symbol'] == self.holding_symbol), None)
                should_exit = False
                reason = ""
                
                if h_metrics:
                    # Policy Exit Rules
                    # 1. VWAP Div > Target (Take Profit)
                    if h_metrics['vwap_div'] > self.EXIT_VWAP_DIV_MIN:
                        should_exit = True
                        reason = "take_profit_vwap"
                    # 2. ROC Crash (Stop Loss)
                    elif h_metrics['roc_5m'] < self.EXIT_ROC_MAX:
                        should_exit = True
                        reason = "stop_loss_mom"
                    # 3. Rank Fallback? (Optional: if out of Top 20?)
                    # Let's stick to strict V1.
                else:
                    # Data missing? Exit.
                    should_exit = True
                    reason = "data_missing"
                    
                if should_exit:
                    self.execute_trade(t, "SELL", self.holding_symbol, reason, price_map)
            
            # B. Entry Check
            if not self.holding_symbol:
                # Look for candidates in Top-5 meeting criteria
                for cand in top_list:
                    # Criteria: Pullback + Vol
                    if (cand['roc_5m'] < self.ENTRY_ROC_MAX) and (cand['vol_accel'] >= self.ENTRY_VOL_MIN):
                        # Found target!
                        self.execute_trade(t, "BUY", cand['symbol'], "pullback_entry", price_map)
                        break # Only 1 pos

    def execute_trade(self, time, side, symbol, reason, price_map):
        series = price_map.get(symbol)
        if series is None: return
        
        # Gate A: Execution Delay
        exec_time = time + timedelta(minutes=self.execution_delay)
        
        # Handling for 'series' being DataFrame or Series?
        # In run_day, price_map stores DataFrame.
        # Need to handle logic.
        
        # Check if force close dict passed (handled differently)
        if isinstance(series, pd.Series): # Force close dict hack
             exec_price = series.iloc[0]
        else: # DataFrame
            if exec_time in series.index:
                exec_price = series.loc[exec_time]['close']
            else:
                 # asof?
                 idx = series.index.asof(exec_time)
                 if pd.isna(idx): return
                 exec_price = series.loc[idx]['close']
        
        if pd.isna(exec_price) or exec_price <= 0: return

        if side == "BUY":
            cost_amt = self.capital * (self.cost_rate / 2)
            net_capital = self.capital - cost_amt
            self.shares = net_capital / exec_price
            self.entry_price = exec_price
            self.holding_symbol = symbol
            
            self.capital = 0
            
            self.trades.append({
                "date": time.date(), "time": exec_time, "symbol": symbol, "side": "BUY",
                "qty": self.shares, "price": exec_price, 
                "fee": -cost_amt, 
                "gross_pnl": 0.0, "net_pnl": -cost_amt, 
                "balance": net_capital, "reason": reason
            })
            
        elif side == "SELL":
            gross_val = self.shares * exec_price
            cost_amt = gross_val * (self.cost_rate / 2)
            net_proceeds = gross_val - cost_amt
            
            gross_pnl = (exec_price - self.entry_price) * self.shares
            net_pnl = gross_pnl - cost_amt 
            
            self.capital = net_proceeds
            self.shares = 0
            self.holding_symbol = None
            
            self.trades.append({
                "date": time.date(), "time": exec_time, "symbol": symbol, "side": "SELL",
                "qty": self.shares, "price": exec_price, 
                "fee": -cost_amt, 
                "gross_pnl": gross_pnl, "net_pnl": net_pnl, 
                "balance": self.capital, "reason": reason
            })

    def force_close_all(self):
        if self.holding_symbol:
            close_time = self.end_date + timedelta(hours=15, minutes=35)
            print(f"Force closing {self.holding_symbol}")
            # Use entry price fallback map logic
            fallback_series = pd.Series({close_time: self.entry_price})
            self.execute_trade(close_time, "SELL", self.holding_symbol, "force_close", {self.holding_symbol: fallback_series})

    def finalize(self):
        df_trades = pd.DataFrame(self.trades)
        if df_trades.empty:
            print("No trades generated.")
            return

        out_path = self.out_dir / f"trades_week1_policy_v1.csv"
        df_trades.to_csv(out_path, index=False)
        
        # Recon
        sum_net_pnl = df_trades['net_pnl'].sum()
        start_eq = self.initial_capital
        end_eq = self.capital
        discrepancy = end_eq - (start_eq + sum_net_pnl)
        
        final_ret = (end_eq / start_eq) - 1.0
        
        recon = {
            "equity_start": start_eq,
            "equity_end": end_eq,
            "return_pct": final_ret * 100,
            "sum_net_pnl": sum_net_pnl,
            "discrepancy": discrepancy,
            "pass": bool(abs(discrepancy) < 1.0),
            "trade_count": len(df_trades),
            "fee_total": df_trades['fee'].sum()
        }
        
        with open(self.out_dir / "simulation_result_v1.json", "w") as f:
            json.dump(recon, f, indent=4)
            
        print(f"\n[Simulation Complete] Policy v1")
        print(f"Final Return: {final_ret*100:.2f}%")
        print(f"Trades: {len(df_trades)}")
        print(f"Reconciliation: {recon['pass']}")

if __name__ == "__main__":
    sim = PolicyV1Simulator("2025-12-15", "2025-12-19")
    sim.run()
