import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Setup Paths
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from garam_core.fastlane.feature_store import FeatureStore
from garam_core.analysis.hero_finder import (
    HeroFinder, HeroProbe, 
    HeroCriteria, OvernightCriteriaStrict, OvernightCriteriaSoft
)
from scripts.scan_heroes import ensure_ssot_champion_scan_schema, PROBES
from typing import Optional

# --- 1. Pure Minute Time Traveling Feature Store ---
class TimeTravelingFeatureStore(FeatureStore):
    """
    Returns MINUTE level features up to cutoff_date.
    User explicitly requested strict minute data usage.
    """
    def __init__(self, cutoff_date: pd.Timestamp, cache_dir="cache/features"):
        super().__init__(cache_dir)
        self.cutoff_date = cutoff_date
        # No memory cache for 32-bit/Minute data to prevent OOM
        # self._memory_cache = {} 

    def get_features(self, symbol: str, force_recompute: bool = False) -> pd.DataFrame:
        # Load Minute Data (SSOT Standard)
        # Always load from disk/super, do not cache in memory long-term
        df = super().get_features(symbol, force_recompute=False)
        if df is None or df.empty:
            return df
            
        if not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"])
        
        # Ensure TZ Naive for simple comparison
        if df["date"].dt.tz is not None:
            df["date"] = df["date"].dt.tz_localize(None)

        # Strict Time Slice (Minute level)
        mask = df["date"] <= self.cutoff_date
        return df[mask].copy()

    def get_market_price(self, symbol: str, current_date: pd.Timestamp) -> float:
        """
        Get Close price at exactly current_date.
        If missing, return 0.0
        """
        if symbol not in self._memory_cache:
            self.get_features(symbol)
            
        if symbol not in self._memory_cache:
            return 0.0
            
        df = self._memory_cache[symbol]
        # Exact match
        row = df[df["date"] == current_date]
        if not row.empty:
            return float(row.iloc[0]["close"])
        return 0.0

# --- 2. Simulation Logic ---
def run_simulation():
    print("=== SSOT 1-Year Simulation (PURE MINUTE DATA) ===")
    
    # Init Paths
    universe_path = project_root / "GARAM_Data" / "real_universe_400.csv"
    if not universe_path.exists():
        print(f"[FAIL] Universe not found: {universe_path}")
        return
        
    df_univ = pd.read_csv(universe_path)
    universe = [str(x).zfill(6) for x in df_univ["Code"].tolist()]
    
    # Determine Time Range
    sample_fs = FeatureStore()
    df_sample = sample_fs.get_features("005930")
    if not pd.api.types.is_datetime64_any_dtype(df_sample["date"]):
        df_sample["date"] = pd.to_datetime(df_sample["date"])
    if df_sample["date"].dt.tz is not None:
        df_sample["date"] = df_sample["date"].dt.tz_localize(None)
    
    all_dates = sorted(df_sample["date"].unique())
    start_date = pd.Timestamp("2024-12-01")
    # Convert to pd.Timestamp explicitly
    trading_minutes = [pd.Timestamp(d) for d in all_dates if pd.Timestamp(d) >= start_date]
    
    if not trading_minutes:
        print("[WARN] No data after start date. Using valid range.")
        trading_minutes = [pd.Timestamp(d) for d in all_dates[-10000:]]
    
    print(f"Range: {trading_minutes[0]} ~ {trading_minutes[-1]} ({len(trading_minutes)} minutes)")
    print("Logic: 09:00 Exit, 15:20 Scan (Minute Logic)")
    
    # State
    capital = 10_000_000.0
    initial_capital = capital
    portfolio = [] # List[dict]
    equity_curve = []
    
    # Criteria
    crit = HeroCriteria(min_trades=10)
    ov_strict = OvernightCriteriaStrict()
    ov_soft = OvernightCriteriaSoft()
    
    # Loop
    for i, current_date in enumerate(trading_minutes):
        t = current_date.time()
        
        # Log periodically
        if i % 5000 == 0:
            print(f"[{i}/{len(trading_minutes)}] {current_date} Cap: {capital:,.0f} Pos: {len(portfolio)}")

        # A. EXIT (09:00:00)
        if t.hour == 9 and t.minute == 0:
            if portfolio:
                fs = TimeTravelingFeatureStore(current_date)
                daily_pnl = 0.0
                logs = []
                
                for pos in portfolio:
                    price = fs.get_market_price(pos['symbol'], current_date)
                    if price <= 0:
                        # Fallback to entry price if missing data?
                        price = pos['entry_price']
                    
                    shares = pos['shares']
                    val = shares * price
                    net = val * (1 - 0.00215) # Tax+Fee
                    
                    capital += net
                    raw_ret = (price - pos['entry_price']) / pos['entry_price']
                    logs.append(f"{pos['symbol']}:{raw_ret*100:.1f}%")
                
                print(f"  [EXIT] {current_date} | {', '.join(logs)} | Cap: {capital:,.0f}")
                portfolio = []

        # B. SCAN & ENTRY (15:20:00)
        elif t.hour == 15 and t.minute == 20:
             # DEBUG
            # print(f"[DEBUG] Scanning at {current_date}...")
            
            # Use FeatureStore with Minute Data
            fs = TimeTravelingFeatureStore(current_date)
            finder = HeroFinder(fs)
            
            try:
                pp = finder.scan(universe, probe=PROBES["CHAMPION_V21"], 
                                 criteria=crit,
                                 overnight_strict=ov_strict,
                                 overnight_soft=ov_soft,
                                 window_days=30, # NOTE: This might mean 30 minutes or 30 days depending on HeroFinder impl
                                 two_pass=False)
                
                # Convert
                results = [r.to_dict() for r in pp]
                df_scan = pd.DataFrame(results)
                df_scan = ensure_ssot_champion_scan_schema(df_scan)
                
                # Pick
                eligible = df_scan[
                    (df_scan["champion_score_norm"] > 0) & 
                    (~df_scan["veto"]) 
                ].copy().sort_values("champion_score_norm", ascending=False)
                
                top_score = eligible["champion_score_norm"].max() if not eligible.empty else 0.0
                # print(f"[DEBUG] Scan: {len(results)} items, Eligible: {len(eligible)}, Top: {top_score:.3f}")

                k = 0
                target_weight = 0.0
                
                if top_score >= 0.93:
                    k = 2; target_weight = 0.50
                elif top_score >= 0.80:
                    k = 5; target_weight = 0.20
                    
                if k > 0 and not eligible.empty:
                    picks = eligible.head(k)
                    buys = []
                    
                    alloc_amt = capital * target_weight * 0.99
                    
                    for _, r in picks.iterrows():
                        sym = str(r["symbol"])
                        # ref_price in Scan result is the Close of the slice (15:20 price)
                        price = float(r["ref_price"])
                        
                        if price <= 0: continue
                        
                        shares = int(alloc_amt / price)
                        if shares > 0:
                            cost = shares * price * (1 + 0.00015)
                            if capital >= cost:
                                capital -= cost
                                portfolio.append({
                                    "symbol": sym,
                                    "shares": shares,
                                    "entry_price": price,
                                    "weight": target_weight
                                })
                                buys.append(f"{sym}")
                    
                    if buys:
                         print(f"  [BUY]  {current_date} (K={k}) | {', '.join(buys)} | Cash: {capital:,.0f}")

            except Exception as e:
                print(f"[ERR] Scan {current_date}: {e}")

        # C. Record Equity (15:30)
        if t.hour == 15 and t.minute == 30:
            mtm = 0.0
            if portfolio:
                fs_mtm = TimeTravelingFeatureStore(current_date)
                for pos in portfolio:
                    p = fs_mtm.get_market_price(pos['symbol'], current_date)
                    if p <= 0: p = pos['entry_price']
                    mtm += pos['shares'] * p
            
            total_equity = capital + mtm
            equity_curve.append({
                "date": current_date.strftime("%Y-%m-%d %H:%M"),
                "capital": total_equity
            })

    # Report
    df_res = pd.DataFrame(equity_curve)
    out_csv = project_root / "results" / f"simulation_1y_ssot_{datetime.now().strftime('%Y%m%d')}.csv"
    df_res.to_csv(out_csv, index=False)
    print(f"\n[Saved] {out_csv}")
    
    if not df_res.empty:
        total_ret = (capital / initial_capital) - 1.0
        print(f"Return: {total_ret*100:.2f}%")
        
        # ASCII Chart
        prices = df_res["capital"].tolist()
        if not prices: return 
        mx = max(prices); mn = min(prices)
        rng = mx - mn if mx != mn else 1.0
        print("\n[Equity Curve]")
        step = max(1, len(prices) // 20)
        for i in range(0, len(prices), step):
            val = prices[i]
            n = int(30 * (val - mn)/rng)
            print(f"{i:03}: {val:,.0f} |{'#'*n}")

if __name__ == "__main__":
    run_simulation()
