import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)

# Setup Path
sys.path.append("C:\\garam")

try:
    from garam.core.alpha_aggregator import AlphaAggregator
except ImportError:
    print("Error importing AlphaAggregator. Check path.")
    sys.exit(1)

def create_mock_market_data(start_date, end_date, symbols):
    """
    Create realistic mock data for simulation period + lookback.
    We need at least 120 days lookback for A1 (6M momentum).
    """
    lookback = 150
    sim_days = (end_date - start_date).days + 1
    total_days = lookback + sim_days
    
    # Start date for data generation
    data_start = start_date - timedelta(days=lookback)
    dates = pd.date_range(start=data_start, end=end_date, freq="D") # Includes weekends, but simple enough
    
    # Seed for reproducibility
    np.random.seed(42)
    
    # Generate random walks with some trend/reversion characteristics
    close_data = {}
    vol_data = {}
    
    for sym in symbols:
        # Random drift and volatility
        drift = np.random.normal(0.0005, 0.001) # Slight positive bias
        volatility = 0.02
        
        returns = np.random.normal(drift, volatility, len(dates))
        price_path = 100 * np.cumprod(1 + returns)
        
        # Add some "Alpha" patterns manually for testing
        # e.g., Symbol 005930 has strong momentum in last 20 days
        if sym == "005930":
            # Boost last 60 days to trigger 6M momentum (A1)
            # A1 looks at 120 days, so let's boost the whole period slightly and end strongly
            trend = np.linspace(1.0, 1.4, len(dates)) # 40% uptrend over the period
            price_path = price_path * trend
            
        if sym == "000660":
             # Flat then drop (Sell signal?)
             trend = np.linspace(1.0, 0.8, len(dates))
             price_path = price_path * trend
            
        close_data[sym] = price_path
        vol_data[sym] = np.random.randint(10000, 50000, len(dates))

    close_df = pd.DataFrame(close_data, index=dates)
    high_df = close_df * 1.01
    low_df = close_df * 0.99
    vol_df = pd.DataFrame(vol_data, index=dates)
    
    return {
        "daily_close": close_df,
        "daily_high": high_df,
        "daily_low": low_df,
        "daily_volume": vol_df
    }

def run_simulation():
    print("=== Multi-Alpha Engine Simulation (Dec 1 - Dec 5) ===")
    
    # 1. Setup
    agg = AlphaAggregator()
    if not agg.alphas:
        print("No active alphas found!")
        return

    universe = ["005930", "000660", "035420", "005380", "051910"] # Top 5
    start_date = datetime(2025, 12, 1)
    end_date = datetime(2025, 12, 5)
    
    # 2. Data Loading (Mock)
    print("Generating Mock Data (including 150 days lookback)...")
    market_data = create_mock_market_data(start_date, end_date, universe)
    
    # 3. Simulation Loop
    # We simulate decisions made at the END of each day (for next day open)
    # or purely based on Close price signal.
    
    sim_dates = pd.date_range(start=start_date, end=end_date, freq="D")
    
    portfolio = {sym: 0 for sym in universe} # Quantity
    cash = 100_000_000 # 100M KRW
    initial_equity = cash
    
    history = []
    
    for current_date in sim_dates:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"\n>> Processing {date_str}")
        
        # Slice data up to current date
        # In reality, we use data available AT that time.
        # Here we just pass the full DF but the alphas should ideally respect the index?
        # Our alphas compute for ALL dates. We just pick the row for 'current_date'.
        
        # 1. Get Multi-Alpha Scores
        # Regime is hardcoded for test, or could be dynamic
        # Use R1_STRONG_UP to favor Trend Alpha (A1)
        regime = "R1_STRONG_UP" 
        
        final_scores, breakdown = agg.compute_final_score(market_data, universe, regime)
        
        if final_scores.empty:
            print("  No scores computed.")
            continue
            
        try:
            # Get scores for today
            today_scores = final_scores.loc[current_date]
            
            # Debug: Print breakdown for 005930
            if "005930" in universe:
                print(f"  [DEBUG 005930] Final: {today_scores['005930']:.2f}")
                for aid, df in breakdown.items():
                    if current_date in df.index:
                        val = df.loc[current_date, "005930"]
                        print(f"    - {aid}: {val:.2f}")
                        
        except KeyError:
            print(f"  No data for {date_str}")
            continue
            
        print("  Scores:", today_scores.to_dict())
        
        # 2. Trading Logic (Simple)
        # Score > 70 -> Buy (Target 20% allocation)
        # Score < 40 -> Sell (Exit)
        
        current_prices = market_data['daily_close'].loc[current_date]
        
        daily_action_log = []
        
        for sym in universe:
            score = today_scores.get(sym, 0)
            price = current_prices[sym]
            
            # Position Sizing
            target_alloc = 0.0
            if score >= 70:
                target_alloc = 0.20 # 20% per stock
            elif score < 40:
                target_alloc = 0.0
            else:
                # Hold current allocation (approx)
                # Calculate current alloc
                current_val = portfolio[sym] * price
                total_equity = cash + sum(portfolio[s] * current_prices[s] for s in universe)
                target_alloc = current_val / total_equity if total_equity > 0 else 0
            
            # Rebalance
            total_equity = cash + sum(portfolio[s] * current_prices[s] for s in universe)
            target_val = total_equity * target_alloc
            current_val = portfolio[sym] * price
            diff_val = target_val - current_val
            
            # Trade if diff is significant (> 1M KRW)
            if abs(diff_val) > 1_000_000:
                qty_change = int(diff_val / price)
                if qty_change != 0:
                    portfolio[sym] += qty_change
                    cash -= qty_change * price
                    action = "BUY" if qty_change > 0 else "SELL"
                    daily_action_log.append(f"{action} {sym} {abs(qty_change)} @ {price:.0f} (Score: {score:.1f})")

        # 3. Daily Summary
        total_equity = cash + sum(portfolio[s] * current_prices[s] for s in universe)
        pnl_pct = (total_equity - initial_equity) / initial_equity * 100
        
        history.append({
            "date": date_str,
            "equity": total_equity,
            "pnl_pct": pnl_pct,
            "actions": daily_action_log
        })
        
        for log in daily_action_log:
            print(f"  [TRADE] {log}")
            
        print(f"  Equity: {total_equity:,.0f} ({pnl_pct:+.2f}%)")

    # Final Report
    print("\n=== Simulation Results ===")
    df_res = pd.DataFrame(history)
    print(df_res[['date', 'equity', 'pnl_pct']])
    print(f"\nFinal PnL: {df_res['pnl_pct'].iloc[-1]:.2f}%")

if __name__ == "__main__":
    run_simulation()
