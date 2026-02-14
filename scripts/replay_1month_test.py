"""
1개월 모의 테스트 (Kiwoom 1년 Rolling Window 제약) - Enhanced with Portfolio & Exit Strategies

목적:
- 실전과 동일한 정보 환경에서 테스트
- 매 영업일 D에서 과거 1년치만 사용
- 히어로 스캔 + 모의 체결 + 성과 기록
- SSOT 리포트 생성
- Exit A/B Testing 지원 (HOLD_1D, RSI_REBOUND_50, HOLD_3D)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from scripts.load_minute_robust import MinuteDataLoader

class Portfolio:
    def __init__(self, start_cash: float, cost_bps: float = 30.0):
        self.cash = start_cash
        self.equity = start_cash
        self.positions = {} # symbol -> {entry_date, entry_price, qty, entry_rsi, days_held}
        self.closed_trades = [] # list of dicts
        # User Requirement: cost_bps is TOTAL Roundtrip.
        # Check: 30bps total -> 15bps entry, 15bps exit.
        self.cost_rate_oneway = (cost_bps / 2) / 10000.0
        self.history = [] # daily equity
    
    def update_holding_period(self):
        for sym in self.positions:
            self.positions[sym]["days_held"] += 1
            
    def process_exits(self, date: datetime, current_prices: dict, current_rsis: dict, exit_strategy: str,
                     minute_data_source=None):
        """
        Exit Strategies:
        - HOLD_1D: Exit after 1 day (Next Close)
        - RSI_REBOUND_50: Exit if RSI >= 50 OR Max Hold 5 days
        - HOLD_3D: Exit after 3 days
        - NEXT_OPEN: Exit Next Day Open (09:00)
        """
        to_sell = []
        
        for sym, pos in self.positions.items():
            price = current_prices.get(sym)
            rsi = current_rsis.get(sym)
            
            # Logic: NEXT_OPEN needs "Open" price, not "Close" price of the day.
            # But here `current_prices` is likely Close price (EOD).
            # For NEXT_OPEN, we sell at the "open" of the exit day.
            # If exit_strategy is NEXT_OPEN, we sell on day 1 (pos['days_held'] >= 1).
            
    def process_exits(self, date, current_prices, current_rsis, exit_strategy, minute_data_source=None):
        to_sell = []
        
        for sym, pos in list(self.positions.items()):
            price = current_prices.get(sym)
            rsi = current_rsis.get(sym)
            
            should_exit = False
            exit_reason = ""
            exit_price = None
            fill_source = "UNSET"
            
            if exit_strategy == "HOLD_1D":
                if pos["days_held"] >= 1:
                    should_exit = True
                    exit_reason = "hold_1d"
                    # EOD close를 확정
                    if price is None:
                        px, src, _ = self._get_eod_close_fill(sym, date, minute_data_source)
                        exit_price, fill_source = px, src
                    else:
                        exit_price, fill_source = price, "EOD_CLOSE"
            
            elif exit_strategy == "RSI_REBOUND_50":
                if (rsi is not None and rsi >= 50) or (pos["days_held"] >= 5):
                    should_exit = True
                    exit_reason = "rsi_50_hit" if (rsi is not None and rsi >= 50) else "max_hold_5"
                    if price is None:
                        px, src, _ = self._get_eod_close_fill(sym, date, minute_data_source)
                        exit_price, fill_source = px, src
                    else:
                        exit_price, fill_source = price, "EOD_CLOSE"
            
            elif exit_strategy == "HOLD_3D":
                if pos["days_held"] >= 3:
                     should_exit = True
                     exit_reason = "hold_3d"
                     if price is None:
                         px, src, _ = self._get_eod_close_fill(sym, date, minute_data_source)
                         exit_price, fill_source = px, src
                     else:
                         exit_price, fill_source = price, "EOD_CLOSE"

            elif exit_strategy == "NEXT_OPEN":
                 if pos["days_held"] >= 1:
                     should_exit = True
                     exit_reason = "next_open"
                     px, src, _ = self._get_next_open_fill(sym, date, minute_data_source)
                     # open도 없으면 (매우 예외) eod close로라도 종료하되 태깅
                     if px is None:
                         px2, src2, _ = self._get_eod_close_fill(sym, date, minute_data_source)
                         exit_price, fill_source = px2, f"MISSING_OPEN_FALLBACK_{src2}"
                     else:
                         exit_price, fill_source = px, src

            if should_exit:
                 # 최종 방어: exit_price가 끝내 None이면 해당 종목은 그날 청산하지 않음(데이터 결손)
                 if exit_price is None or exit_price <= 0:
                      continue
                 self._close_position(date, sym, exit_price, exit_reason, fill_source)
                 to_sell.append(sym)
        
        for sym in to_sell:
             self.positions.pop(sym, None)

    def _get_day_slice(self, symbol, date, data_source):
        if not data_source or symbol not in data_source:
             return None
             
        df, _ = data_source[symbol]
        if df is None or df.empty: return None
        
        # Slicing
        day_df = df[df["dt"].dt.date == date.date()]
        if day_df.empty: return None
        
        return day_df

    def _get_eod_close_fill(self, symbol, date, data_source):
        day_df = self._get_day_slice(symbol, date, data_source)
        if day_df is None:
             return None, "NO_DATA_DAY", False
             
        last_bar = day_df.iloc[-1]
        return float(last_bar["close"]), "MINUTE_BAR.eod_close", False

    def _get_next_open_fill(self, symbol, date, data_source):
        """
        Fill priority:
        1) Exact 09:00 bar open (if open exists)
        2) First bar open (if open exists)
        3) First bar close proxy
        """
        day_df = self._get_day_slice(symbol, date, data_source)
        if day_df is None:
             return None, "NO_DATA_DAY", False
             
        # 09:00 Bar Priority
        t0 = pd.Timestamp(date.date()) + pd.Timedelta(hours=9)
        t1 = t0 + pd.Timedelta(minutes=1)
        
        bar_0900 = day_df[(day_df["dt"] >= t0) & (day_df["dt"] < t1)]
        first_bar = (bar_0900.iloc[0] if not bar_0900.empty else day_df.iloc[0])
        
        has_open = "open" in day_df.columns and pd.notna(first_bar.get("open", np.nan))
        
        if has_open:
             return float(first_bar["open"]), "MINUTE_BAR.open_at_0900", False
             
        # Proxy
        return float(first_bar["close"]), "MINUTE_BAR.first_close_proxy", True

    def _close_position(self, date, sym, price, reason, fill_source="EOD_CLOSE"):
        pos = self.positions[sym]
        qty = pos["qty"]
        sell_val = price * qty
        cost = sell_val * self.cost_rate_oneway
        net_proceeds = sell_val - cost
        
        self.cash += net_proceeds
        
        entry_val = pos["entry_price"] * qty
        # Net Return calculation should consider Entry Cost too.
        # Positions store 'entry_price'. Did we dedcut cost from Cash on entry? Yes.
        # But 'entry_val' is Gross.
        # To get accurate Net Return:
        # Net Profit = Net Proceeds - (Entry Gross + Entry Cost)
        # Entry Cost was calculated at entry. We need to store it?
        # Or re-calc: entry_cost = entry_val * self.cost_rate_oneway
        
        entry_cost = entry_val * self.cost_rate_oneway
        total_investment = entry_val + entry_cost
        
        ret = (net_proceeds / total_investment) - 1.0 
        
        self.closed_trades.append({
            "symbol": sym,
            "entry_date": pos["entry_date"],
            "exit_date": date.strftime("%Y%m%d"),
            "entry_price": pos["entry_price"],
            "exit_price": price,
            "qty": qty,
            "net_return": ret,
            "reason": reason,
            "fill_source": fill_source,
            "days_held": pos["days_held"]
        })

    def enter_position(self, date, sym, price, rsi, amount):
        if sym in self.positions: return # No pyramiding
        
        # cost is paid from cash, but amount is target exposure?
        if price <= 0: return
        
        # Amount is target allocation (Gross or Net?) 
        # Usually target inclusion amount.
        # If we have 5M cash, we buy 5M worth? 
        # cost is extra?
        # If per_trade_amt is 5M. 
        # qty = 5M / price.
        # cost = 5M * rate.
        # total_outflow = 5M + cost.
        # If total_outflow > cash, we reduce qty?
        
        qty = int(amount // price)
        if qty == 0: return
        
        gross_val = qty * price
        cost = gross_val * self.cost_rate_oneway
        total_outflow = gross_val + cost
        
        # Check cash again (though loop checked per_trade_amt)
        if total_outflow > self.cash:
            # Adjust qty to fit cash (including cost)
            # cash = qty * price * (1 + rate)
            # qty = cash / (price * (1 + rate))
            qty = int(self.cash // (price * (1 + self.cost_rate_oneway)))
            if qty == 0: return
            gross_val = qty * price
            cost = gross_val * self.cost_rate_oneway
            total_outflow = gross_val + cost
            
        self.cash -= total_outflow
        self.positions[sym] = {
            "entry_date": date.strftime("%Y%m%d"),
            "entry_price": price,
            "qty": qty,
            "entry_rsi": rsi,
            "days_held": 0
        }

    def update_mark_to_market(self, date, current_prices):
        mkt_val = 0
        for sym, pos in self.positions.items():
            price = current_prices.get(sym, pos["entry_price"])
            mkt_val += price * pos["qty"]
        
        self.equity = self.cash + mkt_val
        self.history.append({
            "date": date.strftime("%Y%m%d"),
            "equity": self.equity,
            "cash": self.cash,
            "positions": len(self.positions)
        })


class ReplayTest1Month:
    """1개월 모의 테스트"""
    
    def __init__(
        self,
        start_date: str,  # YYYYMMDD
        end_date: str,    # YYYYMMDD
        universe_csv: Path,
        minute_dir: Path,
        probe: str = "MR_RSI_30",
        window: int = 14,
        aum: float = 100_000_000,
        cost_bps: float = 30.0,
        exit_strategy: str = "HOLD_1D"
    ):
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.universe_csv = Path(universe_csv)
        self.minute_dir = Path(minute_dir)
        self.probe = probe
        self.window = window
        self.aum = aum
        self.cost_bps = cost_bps
        self.exit_strategy = exit_strategy
        
        # Results
        self.run_id = f"replay_1m_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{exit_strategy}"
        self.run_dir = Path(f"results/replay/{self.run_id}")
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[REPLAY 1M] Run ID: {self.run_id}")
        print(f"[REPLAY 1M] Period: {start_date} ~ {end_date}")
        print(f"[REPLAY 1M] Probe: {self.probe} | Window: {self.window}")
        print(f"[REPLAY 1M] Exit: {self.exit_strategy}")
        
        # Cache for dataframes
        self.data_cache = {}
    
    def load_universe(self) -> list[str]:
        df = pd.read_csv(self.universe_csv)
        col = None
        for c in ["Code", "code", "symbol"]:
            if c in df.columns:
                col = c
                break
        if col is None:
            raise ValueError("Universe CSV has no recognizable symbol column")
        symbols = df[col].astype(str).str.strip().str.zfill(6).tolist()
        symbols = [s for s in symbols if s.isdigit() and len(s) == 6]
        symbols = sorted(set(symbols))
        print(f"[Universe] Loaded {len(symbols)} symbols")
        return symbols
    
    def get_trading_days(self) -> list[datetime]:
        # SSOT: Data Driven Scan (No Holiday Bugs)
        found_dates = set()
        count = 0
        # Scan first 10 files
        for f in self.minute_dir.glob("*.csv"):
            if count >= 10: break
            try:
                # Load only date column
                df = pd.read_csv(f, usecols=["date"])
                
                # Check format
                # If date is YYYYMMDDHHMMSS (integer or string)
                # Parse with format to be safe
                # First convert to string
                df["date"] = df["date"].astype(str)
                # Try format with Hours (robust loader format)
                dt_series = pd.to_datetime(df["date"], format="%Y%m%d%H%M%S", errors='coerce')
                valid_dates = dt_series.dt.date.dropna().unique()
                
                found_dates.update(valid_dates)
                count += 1
            except Exception as e:
                continue

        if not found_dates:
            print("[WARN] Data scan failed. Fallback to Weekdays.")
            days = []
            current = self.start_date
            while current <= self.end_date:
                if current.weekday() < 5:
                    days.append(current)
                current = current + timedelta(days=1)
            return days
            
        # Filter range
        valid_days = [
            datetime.combine(d, datetime.min.time()) 
            for d in found_dates 
            if self.start_date.date() <= d <= self.end_date.date()
        ]
        valid_days.sort()
        print(f"[Trading Days] Scanned {count} files. Found {len(valid_days)} valid trading days.")
        return valid_days
        
    def _calculate_rsi_series(self, prices, window=14):
        # Extended calc for full series to get today's value safely
        deltas = np.diff(prices)
        seed = deltas[:window+1]
        up = seed[seed >= 0].sum()/window
        down = -seed[seed < 0].sum()/window
        rs = up/down if down != 0 else 0
        rsi = np.zeros_like(prices)
        # Pre-fill
        rsi[:window] = 100. - 100./(1. + rs) # Approx
        
        avg_gain = up
        avg_loss = down
        
        # Rolling Wilder
        for i in range(window, len(prices)):
            delta = prices[i] - prices[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            avg_gain = (avg_gain * (window - 1) + upval) / window
            avg_loss = (avg_loss * (window - 1) + downval) / window
            
            if avg_loss == 0:
                rsi[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi[i] = 100.0 - (100.0 / (1.0 + rs))
        return rsi

    def run(self):
        symbols = self.load_universe()
        trading_days = self.get_trading_days()
        loader = MinuteDataLoader(self.minute_dir)
        portfolio = Portfolio(self.aum, self.cost_bps)
        
        all_scans = []
        
        for trade_date in trading_days:
            date_str = trade_date.strftime("%Y%m%d")
            print(f"[{date_str}] Processing...")
            
            # --- 0. Data Prep (For all universe to scan & price check) ---
            current_prices = {}
            current_rsis = {}
            candidates = []
            
            # Optimization: Load only necessary data? 
            # We need to scan WHOLE universe for entries.
            # Efficient caching is key.
            
            # --- 0. Data Prep (For all universe to scan & price check) ---
            current_prices = {}
            current_rsis = {}
            candidates = []
            
            loaded_count = 0
            for symbol in symbols:
                # Check cache
                if symbol not in self.data_cache:
                    df, quality = loader.load_symbol(symbol, lookback_days=400, tail_rows=50000)
                    
                    if not df.empty and quality["status"] == "ok":
                         # Pre-calculate RSI for the whole series ONCE
                        close_full = df["close"].values
                        rsi_full = self._calculate_rsi_series(close_full, self.window)
                        # Add to dataframe for easy lookup
                        df["rsi"] = rsi_full
                        self.data_cache[symbol] = (df, quality)
                    else:
                        self.data_cache[symbol] = (df, quality)
                    
                    loaded_count += 1
                    if loaded_count % 50 == 0:
                        print(f"  [DataLoad] Loaded {loaded_count} new symbols...")
                
                df, quality = self.data_cache[symbol]
                
                if df.empty or quality["status"] != "ok":
                    continue
                
                # Filter strictly by date (No Lookahead)
                # Use 'dt' column
                # Optimization: df is sorted. Use searchsorted to find index of trade_date EOD
                # But simple mask is fine if RSI is already in DF
                
                # We need the row exactly at or before trade_date
                # Let's use searchsorted on dates? 
                # df["dt"] is monotonic increasing.
                # Find insertion point
                
                # Mask method (slower but safe):
                # sub_df = df[df["dt"] <= trade_date]
                # if sub_df.empty: continue
                # if len(sub_df) < self.window + 10: continue
                # current_row = sub_df.iloc[-1]
                
                # Optimized Method:
                # We can assume 1 row per minute or just find the last row <= trade_date
                # Since we iterate days sequentially, we could optimize more.
                # But strict mask is robust.
                
                # CRITICAL FIX: Use Date matching to include intraday data
                day_mask = (df["dt"].dt.date == trade_date.date())
                sub_df = df[day_mask]
                
                if sub_df.empty or len(sub_df) < self.window + 10:
                    continue
                
                current_row = sub_df.iloc[-1]
                close_price = float(current_row["close"])
                current_rsi = float(current_row["rsi"])
                
                current_prices[symbol] = close_price
                current_rsis[symbol] = current_rsi
                
                # Scan Candidate
                if self.probe == "MR_RSI_30":
                    if current_rsi < 30:
                        candidates.append((symbol, current_rsi, close_price))
            
            # --- 1. Portfolio Update (Exits) ---
            portfolio.update_holding_period()
            portfolio.process_exits(trade_date, current_prices, current_rsis, self.exit_strategy, 
                                  minute_data_source=self.data_cache)
            
            # --- 2. Entry Logic ---
            # Allocation rule: Equal Weight (Cash / Count)
            # Restore SSOT Baseline logic: Invest all available cash divided by N candidates.
            # Use 99% of cash to reserve for costs/slippage.
            
            # Sort candidates by RSI (lower is better) to prioritize?
            candidates.sort(key=lambda x: x[1]) 
            
            n_candidates = len(candidates)
            if n_candidates > 0:
                # Calculate per-trade amount dynamically
                # Note: This is aggressive compounding.
                total_cash = portfolio.cash
                per_trade_amt = (total_cash * 0.99) / n_candidates
                
                heroes_count = 0
                for sym, rsi, price in candidates:
                    # If we have cash, buy.
                    # Check if already held (should logic allow re-buy? usually no, but here we exited already)
                    if sym in portfolio.positions: continue
                    
                    if portfolio.cash > per_trade_amt:
                        portfolio.enter_position(trade_date, sym, price, rsi, per_trade_amt)
                        heroes_count += 1
                
                print(f"  Heroes found: {n_candidates}, Bought: {heroes_count}, Positions: {len(portfolio.positions)}")
            else:
                print(f"  Heroes found: 0, Bought: 0, Positions: {len(portfolio.positions)}")
            
            # --- 3. Mark to Market ---
            portfolio.update_mark_to_market(trade_date, current_prices)
            
        
        # End of Loop
        print(f"\n[DONE] Run ID: {self.run_id}")
        
        # Save Artifacts
        # 1. Equity
        df_equity = pd.DataFrame(portfolio.history)
        df_equity.to_csv(self.run_dir / "equity_curve.csv", index=False)
        print(f"Saved equity: {self.run_dir / 'equity_curve.csv'}")
        
        # 2. Trades
        df_trades = pd.DataFrame(portfolio.closed_trades)
        if not df_trades.empty:
            df_trades.to_csv(self.run_dir / "all_trades.csv", index=False)
            
        # Stats
        proxies = 0
        total_exits = 0
        if not df_trades.empty and "fill_source" in df_trades.columns:
            proxies = df_trades["fill_source"].str.contains("proxy", case=False).sum()
            total_exits = len(df_trades)
        
        proxy_rate = (proxies / total_exits * 100) if total_exits > 0 else 0.0
        
        # User Feedback: Rename NEXT_OPEN to NEXT_0900_PROXY_EXIT if proxy used.
        eff_exit_strategy = self.exit_strategy
        if self.exit_strategy == "NEXT_OPEN":
            eff_exit_strategy = "NEXT_0900_PROXY_EXIT"

        manifest = {
            "run_id": self.run_id,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "trading_days": len(trading_days),
            "probe": self.probe,
            "window": self.window,
            "exit_strategy": eff_exit_strategy,
            "aum": self.aum,
            "cost_bps": self.cost_bps,
            "cost_semantics": "roundtrip_total_bps",
            "entry_rule": "RSI < 30 (Daily Close)",
            "exit_rule": eff_exit_strategy,
            "final_equity": float(portfolio.equity),
            "return_pct": float((portfolio.equity / self.aum - 1) * 100),
            "total_trades": len(portfolio.closed_trades),
            "open_proxy_rate": float(proxy_rate),
            "open_fill_policy": "0900_bar_open > first_bar_open > first_bar_close_proxy",
            "eod_fill_policy": "minute_day_last_close"
        }
        
        with open(self.run_dir / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="YYYYMMDD")
    parser.add_argument("--end", required=True, help="YYYYMMDD")
    parser.add_argument("--universe", required=True)
    parser.add_argument("--minute_dir", required=True)
    parser.add_argument("--probe", default="MR_RSI_30")
    parser.add_argument("--window", type=int, default=14)
    parser.add_argument("--aum", type=float, default=100000000)
    parser.add_argument("--exit", default="HOLD_1D", help="HOLD_1D | RSI_REBOUND_50 | HOLD_3D | NEXT_OPEN")
    parser.add_argument("--cost_bps", type=float, default=30.0, help="Transaction cost in bps")
    
    args = parser.parse_args()
    
    tester = ReplayTest1Month(
        start_date=args.start,
        end_date=args.end,
        universe_csv=args.universe,
        minute_dir=args.minute_dir,
        probe=args.probe,
        window=args.window,
        aum=args.aum,
        exit_strategy=args.exit,
        cost_bps=args.cost_bps
    )
    tester.run()
