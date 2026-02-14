
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timedelta
import sys
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

# Setup Path
PROJECT_ROOT = Path("C:/garam/garam")
sys.path.append(str(PROJECT_ROOT))
DATA_DIR = PROJECT_ROOT / "GARAM_Data/60day_replay_kst"
OUT_DIR = PROJECT_ROOT / "logs/y1_daily"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', 
                    handlers=[logging.FileHandler(OUT_DIR/"run.log"), logging.StreamHandler(sys.stdout)])

@dataclass
class DailyConfig:
    # Trend Params
    lookback_high: int = 20
    lookback_low: int = 10
    ma_fast: int = 20
    ma_slow: int = 60
    
    # Filter Params
    min_turnover: float = 10_000_000_000  
    
    # Risk Params
    stop_loss_atr: float = 3.0    # Initial Stop
    trailing_stop_atr: float = 3.0 # Trailing Stop (Chandelier)
    risk_per_trade: float = 0.02 
    fixed_weight: float = 0.33 
    max_slots: int = 3         

CFG = DailyConfig()

class DailyTrendEngine:
    def __init__(self):
        self.universe = {} 
        self.cash = 100_000_000
        self.positions = {} 
        self.equity_curve = []
        self.trade_log = []
        
    def load_and_resample(self):
        logging.info("Loading and Resampling Data to Daily...")
        files = list(DATA_DIR.glob("*.csv"))
        loaded_count = 0
        
        for f in files:
            if 'K' in f.name: continue 
            
            try:
                df = pd.read_csv(f)
                cols = {c.lower(): c for c in df.columns}
                rename_map = {}
                if 'ts' in cols: rename_map[cols['ts']] = 'date'
                elif 'date' in cols: rename_map[cols['date']] = 'date'
                for k in ['open','high','low','close','volume']:
                    if k in cols: rename_map[cols[k]] = k
                df.rename(columns=rename_map, inplace=True)
                
                if 'date' not in df.columns or 'close' not in df.columns: continue
                
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                daily = df.resample('1D').agg({
                    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
                }).dropna()
                
                if daily.empty: continue
                
                daily['turnover'] = daily['close'] * daily['volume']
                daily['donchian_high'] = daily['high'].rolling(window=CFG.lookback_high).max().shift(1)
                daily['donchian_low'] = daily['low'].rolling(window=CFG.lookback_low).min().shift(1)
                daily['atr'] = self._calc_atr(daily)
                
                # Market Breadth Helper
                daily['ma20'] = daily['close'].rolling(20).mean()
                daily['above_ma20'] = (daily['close'] > daily['ma20']).astype(int)
                
                # Volatility & Turnover Helper (Y-8)
                daily['turnover_ma5'] = daily['turnover'].rolling(window=5).mean().shift(1) # Use previous 5 days avg
                
                self.universe[f.stem] = daily
                loaded_count += 1
                if loaded_count % 50 == 0: logging.info(f"Loaded {loaded_count} tickers...")
                    
            except Exception as e:
                logging.error(f"Error loading {f.name}: {e}")
        
        # Pre-calculate Market Breadth (Ratio > MA20)
        logging.info("Calculating Market Breadth...")
        breadth_list = []
        for df in self.universe.values():
            if 'above_ma20' in df.columns:
                breadth_list.append(df['above_ma20'])
        
        if breadth_list:
            breadth_df = pd.concat(breadth_list, axis=1)
            self.market_ratio = breadth_df.sum(axis=1) / breadth_df.count(axis=1)
            self.market_ratio_delta = self.market_ratio.diff()
        else:
            self.market_ratio = pd.Series()
            self.market_ratio_delta = pd.Series()

        logging.info(f"Total Universe Size: {len(self.universe)} tickers")

    def get_intraday_data(self, ticker, target_date):
        """Lazy load intraday data for specific ticker and date, resampled to 1H."""
        # Find file
        f_list = list(DATA_DIR.glob(f"{ticker}*.csv"))
        if not f_list: return None
        
        try:
            # We must read the whole file because files are by ticker (dates are rows)
            # Optimization: We could cache this if memory allows, but for now lazy load is strictly per ticker/day
            # Actually, re-reading CSV every day for every position is slow. 
            # Better to read once per ticker if holding. 
            # But simpler logic first: Read, filter date.
            
            # Optimization: Helper cache?
            if not hasattr(self, '_intraday_cache'): self._intraday_cache = {}
            if ticker not in self._intraday_cache:
                 df = pd.read_csv(f_list[0])
                 cols = {c.lower(): c for c in df.columns}
                 rename_map = {}
                 if 'ts' in cols: rename_map[cols['ts']] = 'date'
                 elif 'date' in cols: rename_map[cols['date']] = 'date'
                 for k in ['open','high','low','close','volume']:
                     if k in cols: rename_map[cols[k]] = k
                 df.rename(columns=rename_map, inplace=True)
                 df['date'] = pd.to_datetime(df['date'])
                 df.set_index('date', inplace=True)
                 self._intraday_cache[ticker] = df # Cache full DF
            
            df = self._intraday_cache[ticker]
            target_str = target_date.strftime('%Y-%m-%d')
            
            # Slice for the day
            day_data = df.loc[target_str]
            if day_data.empty: return None
            
            # Resample to 1H
            hourly = day_data.resample('1h').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
            }).dropna()
            return hourly
            
        except Exception as e:
            # logging.error(f"Intraday Load Error {ticker}: {e}")
            return None

    def _calc_atr(self, df, period=14):
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean()

    def run(self):
        all_dates = sorted(list(set().union(*[df.index for df in self.universe.values()])))
        logging.info(f"Simulation Range: {all_dates[0]} ~ {all_dates[-1]}")
        
        for i, today in enumerate(all_dates):
            if i == 0: continue
            
            # Get Market Regime
            # If today not in market_ratio index, assume Bull (0.5)
            m_ratio = self.market_ratio.get(today, 0.5)
            m_delta = self.market_ratio_delta.get(today, 0.0)
            
            # Bear Trigger: Low Level (<40%) OR Sharp Drop (>-5%)
            is_bear = (m_ratio < 0.40) or (m_delta < -0.05)
            
            # --- Valuation Update ---
            current_eq = self.cash
            for tkr, pos in self.positions.items():
                if today in self.universe[tkr].index:
                    px = self.universe[tkr].loc[today, 'close']
                    current_eq += pos['qty'] * px
                else:
                    current_eq += pos['qty'] * pos['last_px']
            
            self.equity_curve.append({'date': today, 'equity': current_eq})
            
            # --- Manage Existing Positions (Exits) ---
            kill_list = []
            for tkr, pos in self.positions.items():
                df = self.universe[tkr]
                if today not in df.index: continue
                row = df.loc[today]
                
                # Update Highest High for Trailing Stop
                if row['high'] > pos.get('highest_high', 0):
                    pos['highest_high'] = row['high']
                
                exit_price = row['close']
                exit_reason = None
                
                # Calculate PnL % for Adaptive Stop
                curr_pnl_pct = (row['close'] - pos['avg_px']) / pos['avg_px']
                
                # Adaptive Stop Multiplier
                # Bear Market (<40% OR Crash) AND Weak Position (<10%) -> Tighten to 2.0
                if is_bear and curr_pnl_pct < 0.10:
                    stop_mult = 2.0
                else:
                    stop_mult = 3.0
                
                # --- Intraday Stop Logic (Project Y-7) & Climax Profit (Project Y-8) ---
                hourly_data = self.get_intraday_data(tkr, today)
                if hourly_data is not None and not hourly_data.empty:
                    # Check Hourly Bars
                    trailing_stop_px = pos['highest_high'] - (pos['atr_at_entry'] * stop_mult)
                    atr_stop_px = pos['entry_px'] - (pos['atr_at_entry'] * CFG.stop_loss_atr)
                    
                    found_intraday_exit = False
                    
                    # Y-8 Climax Helpers
                    ma5_to = row.get('turnover_ma5', 0)
                    prev_close = self.universe[tkr].shift(1).loc[today]['close'] if today in self.universe[tkr].shift(1).index else pos['last_px']
                    cum_volume = 0
                    
                    for ts, h_row in hourly_data.iterrows():
                        # Update Intraday High for Trailing Stop
                        if h_row['high'] > pos['highest_high']:
                            pos['highest_high'] = h_row['high']
                            trailing_stop_px = pos['highest_high'] - (pos['atr_at_entry'] * stop_mult)
                        
                        # --- Y-8 Climax Profit Taking ---
                        # Accumulate Volume for Turnover Estimation
                        cum_volume += h_row['volume']
                        curr_turnover = cum_volume * h_row['close']
                        curr_return = (h_row['close'] - prev_close) / prev_close
                        
                        # Check Stops
                        # 1. Trailing Stop

                        if h_row['low'] < trailing_stop_px:
                            exit_reason = f"Trailing Stop ({stop_mult}ATR) [Intraday]"
                            # Gap Check
                            if h_row['open'] < trailing_stop_px:
                                exit_price = h_row['open'] # Gap Down -> Open Price
                            else:
                                exit_price = trailing_stop_px # Intraday Hit -> Limit Price
                            found_intraday_exit = True
                        
                        # 2. ATR Stop
                        elif h_row['low'] < atr_stop_px:
                            exit_reason = "ATR Stop [Intraday]"
                            if h_row['open'] < atr_stop_px:
                                exit_price = h_row['open']
                            else:
                                exit_price = atr_stop_px
                            found_intraday_exit = True
                            
                        if found_intraday_exit:
                            # Apply Slippage 0.5%
                            exit_price = exit_price * 0.995 
                            break
                    
                    if found_intraday_exit:
                         pnl = (exit_price - pos['avg_px']) * pos['qty']
                         self.cash += exit_price * pos['qty']
                         self.trade_log.append({
                            'date': today, 'ticker': tkr, 'side': 'SELL', 
                            'price': exit_price, 'qty': pos['qty'], 
                            'reason': exit_reason, 'pnl': pnl,
                            'market_ratio': m_ratio
                         })
                         kill_list.append(tkr)
                         continue # Skip Daily Checks
                
                # --- Daily Fallback Logic (if no Intraday data or no exit) ---
                # Update Highest High (Daily)
                if row['high'] > pos.get('highest_high', 0):
                    pos['highest_high'] = row['high']
                
                # 1. Donchian Exit (Daily Only)
                if row['close'] < row['donchian_low']:
                    exit_reason = "Donchian Low Breakdown"
                
                if exit_reason:
                    pnl = (exit_price - pos['avg_px']) * pos['qty']
                    self.cash += exit_price * pos['qty']
                    self.trade_log.append({
                        'date': today, 'ticker': tkr, 'side': 'SELL', 
                        'price': exit_price, 'qty': pos['qty'], 
                        'reason': exit_reason, 'pnl': pnl,
                        'market_ratio': m_ratio
                    })
                    kill_list.append(tkr)
            
            for k in kill_list: del self.positions[k]
                
            # --- Scan for Entries ---
            if current_eq <= 0: break
            
            candidates = []
            for tkr, df in self.universe.items():
                if today not in df.index: continue
                row = df.loc[today]
                
                if row['turnover'] < CFG.min_turnover: continue
                
                if row['close'] > row['donchian_high']:
                    candidates.append((tkr, row['turnover'], row['close'], row['atr']))
                    logging.info(f"Signal: {tkr} on {today} (Close {row['close']} > Donch {row['donchian_high']})")

            # Top 3 Hero Priority
            candidates.sort(key=lambda x: x[1], reverse=True)
            daily_top3 = [c[0] for c in candidates[:3]]
            
            if candidates:
                logging.info(f"{today}: Top 3 Heroes: {daily_top3}")
            
            for tkr, to, close, atr in candidates:
                is_top3 = tkr in daily_top3
                if tkr in self.positions: continue
                
                slots_avail = CFG.max_slots - len(self.positions)
                can_enter = False
                
                if slots_avail > 0:
                    can_enter = True
                elif is_top3:
                    # Slot Full, Force Entry for Hero
                    can_enter = True
                
                if not can_enter: continue
                
                # --- Execution Logic (Liquidity Harvesting) ---
                target_amt = current_eq * CFG.fixed_weight
                qty = int(target_amt / close)
                cost = qty * close
                
                if qty == 0: continue
                
                # Helper to get Harvest Candidate List (Sorted by PnL)
                def get_harvest_candidates(positions, universe, current_date):
                    cands = []
                    for pt, pdata in positions.items():
                        # Get Current Price
                        if current_date in universe[pt].index:
                            curr_px = universe[pt].loc[current_date, 'close']
                            curr_to = universe[pt].loc[current_date, 'turnover']
                        else:
                            curr_px = pdata['last_px']
                            curr_to = 0
                        
                        # PnL %
                        pnl_pct = (curr_px - pdata['avg_px']) / pdata['avg_px']
                        
                        # Vicim Score: 
                        # We want to sell Losers first (neg PnL).
                        # Winners (>10%) should be protected (higher score).
                        # Score = pnl_pct. 
                        # Sort Ascending: -10%, -5%, +2%, +20%.
                        # So simply sorting by PnL % works. Losers (-0.1) come before Winners (0.2).
                        
                        cands.append({
                            'ticker': pt,
                            'pnl_pct': pnl_pct,
                            'turnover': curr_to,
                            'curr_px': curr_px,
                            'qty': pdata['qty'],
                            'avg_px': pdata['avg_px']
                        })
                    
                    # Sort by PnL Ascending (Sell Losers First)
                    # Tie-breaker: Turnover Ascending (Sell Weaker Liquidity)
                    cands.sort(key=lambda x: (x['pnl_pct'], x['turnover']))
                    return cands

                # 1. Clear Slot Logic (if full)
                if len(self.positions) >= CFG.max_slots:
                    harvest_list = get_harvest_candidates(self.positions, self.universe, today)
                    victim = harvest_list[0]
                    v_tkr = victim['ticker']
                    
                    # Y-5 Optimization: Churn Protection
                    # If Victim is NOT a Loser (PnL > -1%) AND has Higher Liquidity -> Don't Swap
                    if victim['pnl_pct'] > -0.01 and to < victim['turnover']:
                        continue

                    # Execute Sell
                    self.cash += victim['curr_px'] * victim['qty']
                    pnl = (victim['curr_px'] - victim['avg_px']) * victim['qty']
                    
                    del self.positions[v_tkr]
                    self.trade_log.append({
                        'date': today, 'ticker': v_tkr, 'side': 'SELL', 
                        'price': victim['curr_px'], 'qty': victim['qty'], 
                        'reason': f'Slot Cleared for {tkr}', 'pnl': pnl
                    })
                    logging.info(f"SLOT CLEAR (Loser Priority): Sell {v_tkr}(PnL {victim['pnl_pct']*100:.1f}%) for {tkr}")

                # 2. Harvest Cash Logic (sell MORE if needed)
                harvest_attempts = 0
                while self.cash < cost and len(self.positions) > 0 and harvest_attempts < 5:
                    harvest_list = get_harvest_candidates(self.positions, self.universe, today)
                    victim = harvest_list[0]
                    v_tkr = victim['ticker']
                    
                    # Protect Super Winners? If PnL > 10% and we still need cash?
                    # Y-5 Rule: "Sell Biggest Losers First". If we ran out of losers, we sell winners.
                    # That is acceptable for Molbbang logic (Cash is King for Hero).
                    
                    self.cash += victim['curr_px'] * victim['qty']
                    pnl = (victim['curr_px'] - victim['avg_px']) * victim['qty']
                    
                    del self.positions[v_tkr]
                    self.trade_log.append({
                        'date': today, 'ticker': v_tkr, 'side': 'SELL', 
                        'price': victim['curr_px'], 'qty': victim['qty'], 
                        'reason': f'Cash Harvest for {tkr}', 'pnl': pnl
                    })
                    logging.info(f"CASH HARVEST: Sell {v_tkr}(PnL {victim['pnl_pct']*100:.1f}%) for {tkr}")
                    harvest_attempts += 1
                
                # Final Buy
                if self.cash >= cost:
                    self.cash -= cost
                    self.positions[tkr] = {
                        'ticker': tkr,
                        'qty': qty,
                        'avg_px': close,
                        'entry_px': close,
                        'entry_ts': today,
                        'atr_at_entry': atr if not np.isnan(atr) else close*0.05,
                        'last_px': close,
                        'highest_high': close, # Init Highest High
                        'turnover_at_entry': to
                    }
                    self.trade_log.append({
                        'date': today, 'ticker': tkr, 'side': 'BUY', 
                        'price': close, 'qty': qty, 
                        'reason': 'Hero Entry' if is_top3 else 'Trend Entry'
                    })
                    logging.info(f"BUY EXEC: {tkr} Qty={qty} Amt={cost:,.0f}")
                else:
                    logging.warning(f"BUY FAIL: {tkr} Insufficient Cash {self.cash:,.0f} < {cost:,.0f}")


        # Final Report
        final_eq = self.equity_curve[-1]['equity'] if self.equity_curve else self.cash
        ret = (final_eq - 100_000_000) / 100_000_000 * 100
        logging.info(f"Final Equity: {final_eq:,.0f} KRW ({ret:.2f}%)")
        
        pd.DataFrame(self.trade_log).to_csv(OUT_DIR / "trade_log.csv", index=False)
        pd.DataFrame(self.equity_curve).to_csv(OUT_DIR / "equity.csv", index=False)

if __name__ == "__main__":
    sim = DailyTrendEngine()
    sim.load_and_resample()
    sim.run()
