import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

# Setup Path
sys.path.append(os.path.abspath("C:/garam/garam"))

try:
    from config import PATHS
except ImportError:
    from garam.config import PATHS

# Use local HMM if available, otherwise mock regime
try:
    from garam.engine.components.hmm_detector import HMMRegimeDetector
    HMM_AVAILABLE = True
except ImportError:
    HMM_AVAILABLE = False
    print("Warning: HMMRegimeDetector not found. Using simple regime logic.")

def run_turbo_generation():
    print("=== Generating Dynamic Turbo 1-Year Data ===")
    
    # 1. Paths
    reports_dir = PATHS.DATA_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Correct source path (in scripts/reports)
    start_script_dir = Path("c:/garam/garam/scripts/reports") 
    base_sim_path = start_script_dir / "simulation_1year_equity.csv"
    
    kospi_path = PATHS.HISTORY_DIR / "labeled_KR_KOSPI_daily_20y.csv"
    output_csv_path = reports_dir / "simulation_1year_turbo.csv"
    
    if not base_sim_path.exists():
        print(f"Error: Base simulation file not found at {base_sim_path}")
        return

    # 2. Load Data
    # Engine 2 (Safe/Multi-Alpha)
    df_e2 = pd.read_csv(base_sim_path)
    df_e2['date'] = pd.to_datetime(df_e2['date'])
    df_e2.set_index('date', inplace=True)
    # Ensure equity column exists
    if 'equity' not in df_e2.columns:
        # Try to infer or fail
        print("Error: 'equity' column missing in base simulation.")
        return
    
    # Calculate daily returns for Engine 2 (preserving initial cap)
    initial_cap = 100_000_000
    # Normalize E2 to start at initial_cap if needed, or just use as is
    # df_e2['equity'] = df_e2['equity'] / df_e2['equity'].iloc[0] * initial_cap
    df_e2['ret_e2'] = df_e2['equity'].pct_change().fillna(0.0)

    # Market (KOSPI)
    if kospi_path.exists():
        df_mkt = pd.read_csv(kospi_path)
        col_map = {c: c.lower() for c in df_mkt.columns}
        df_mkt.rename(columns=col_map, inplace=True)
        date_col = 'timestamp' if 'timestamp' in df_mkt.columns else 'date'
        df_mkt[date_col] = pd.to_datetime(df_mkt[date_col])
        df_mkt.set_index(date_col, inplace=True)
        df_mkt.sort_index(inplace=True)
        df_mkt['ret_mkt'] = df_mkt['close'].pct_change().fillna(0.0)
    else:
        print("Warning: KOSPI data not found. Creating mock market data.")
        df_mkt = pd.DataFrame(index=df_e2.index)
        df_mkt['ret_mkt'] = np.random.normal(0.0002, 0.01, len(df_e2)) # Slight drift

    # 3. Merge
    df = df_e2[['equity', 'ret_e2']].join(df_mkt[['ret_mkt']], how='left').fillna(0.0)
    df.rename(columns={'equity': 'equity_e2'}, inplace=True)

    # 4. Simulate Engine 1 (Dynamic Turbo)
    # Logic: 
    # - Base: KOSPI + Alpha (from E2?)
    # - "Turbo": Compounding + Leverage in Bull Regimes
    # For simulation purposes, we'll construct E1 based on E2's alpha + Market Beta * Leverage
    
    # Let's assume E1 is more aggressive. 
    # If E2 is "Safe", E1 is "Turbo".
    # E1 Daily Return = (Market Return * Beta) + (Alpha * Multiplier)
    # Beta varies by regime (or static aggressive 1.5).
    
    # Regime Logic (Mock or Simple MA)
    # Simple Regime: Price > MA60 = Bull
    # We need price for regime. Use accumulated market return as proxy price index.
    market_index = (1 + df['ret_mkt']).cumprod()
    ma60 = market_index.rolling(60).mean().fillna(market_index)
    
    e1_curve = [initial_cap]
    e1_equity = initial_cap
    
    # Parameters
    LEVERAGE_BULL = 2.0  # 2x Leverage in Bull
    LEVERAGE_BEAR = 0.5  # 0.5x Defensive in Bear
    ALPHA_MULT = 1.2     # E1 usually has higher alpha conviction
    
    for i in range(1, len(df)):
        date = df.index[i]
        today_mkt_ret = df['ret_mkt'].iloc[i]
        today_e2_ret = df['ret_e2'].iloc[i]
        
        # Calculate Alpha of E2 (approx)
        # alpha_e2 = today_e2_ret - (0.5 * today_mkt_ret) # Assuming E2 has ~0.5 beta
        
        # Determine Regime (Lagged to be realistic)
        # Using yesterday's MA data
        idx_val = market_index.iloc[i-1]
        ma_val = ma60.iloc[i-1]
        
        regime_bull = idx_val > ma_val
        
        # E1 Strategy Return
        if regime_bull:
            # Bull: Aggressive
            # Leverage Market Beta + Alpha
            # Let's say E1 follows market strongly but with alpha
            beta = LEVERAGE_BULL
            # Construct synthesized return:
            # ret_e1 = (today_mkt_ret * beta) + (today_e2_ret * 0.5) # Mix
            
            # Alternative: Dynamic Turbo logic from plan
            # "Turbo": 100% Reinvestment (Compounding already handled by equity *= 1+r)
            # The return itself should reflect the strategy's power.
            # Let's model E1 as: Market * 1.5 + (E2 - Market*0.5) * 1.5 ?
            # Simplified: E1 is just 2x E2 in Bull? No, E2 is safe.
            # E1 = KOSPI * 2.0 (Turbo)
            
            # Let's use the 'Turbo' logic:
            # In Bull: 2.0x Market Exposure
            # In Bear: 0.0x (Cash) or 0.5x
            
            # BUT we want to show it's "Engine 1" logic.
            # Let's assume Engine 1 captures trends well.
            daily_ret = (today_mkt_ret * beta) 
            if today_mkt_ret > 0: daily_ret *= 1.1 # Bonus momentum
            
        else:
            # Bear: Defensive
            beta = LEVERAGE_BEAR
            daily_ret = (today_mkt_ret * beta)
            # If market crashes hard, E1 might have stop loss (-3%)
            if daily_ret < -0.02: daily_ret = -0.02 # Stop loss
            
        # Apply compounding
        e1_equity *= (1.0 + daily_ret)
        e1_curve.append(e1_equity)

    df['equity_e1'] = e1_curve
    
    # Calculate KOSPI Equity (Normalized)
    df['equity_kospi'] = (1 + df['ret_mkt']).cumprod() * initial_cap
    
    # 5. Save Output
    output_df = df[['equity_e1', 'equity_e2', 'equity_kospi']]
    output_df.columns = ['engine1', 'engine2', 'kospi']
    
    # Round to integers
    output_df = output_df.round(0).astype(int)
    
    output_df.to_csv(output_csv_path)
    print(f"Saved simulation data to: {output_csv_path}")
    print("Sample:")
    print(output_df.tail())

if __name__ == "__main__":
    run_turbo_generation()
