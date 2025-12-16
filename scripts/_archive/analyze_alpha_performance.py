"""
Alpha Health Check Script
- Loads alpha scores and market data.
- Calculates IC (Information Coefficient) and Rank Correlation.
- Analyzes performance breakdown by Regime.
- Simulates Single Alpha Portfolios (Top N).
"""

import pandas as pd
import numpy as np
import yaml
import sys
from pathlib import Path
from datetime import timedelta

# Add project root
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent))

from config import PATHS
from garam.scoring.multi_alpha_aggregator import MultiAlphaAggregator
from garam.regime.micro_regime import calculate_latest_micro_regime

def load_market_data(universe_symbols):
    print("Loading Market Data...")
    daily_dir = Path("g:/내 드라이브/garamdata/history/daily")
    
    df_close = pd.DataFrame()
    
    for sym in universe_symbols:
        p = daily_dir / f"{sym}_daily.csv"
        if p.exists():
            df = pd.read_csv(p)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
            elif 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            
            df = df[~df.index.duplicated(keep='last')]
            if 'close' in df.columns: df_close[sym] = df['close']
            if 'high' in df.columns: 
                if 'daily_high' not in locals(): daily_high = pd.DataFrame()
                daily_high[sym] = df['high']
            if 'low' in df.columns:
                if 'daily_low' not in locals(): daily_low = pd.DataFrame()
                daily_low[sym] = df['low']
            if 'volume' in df.columns:
                if 'daily_volume' not in locals(): daily_volume = pd.DataFrame()
                daily_volume[sym] = df['volume']
            
    return {'daily_close': df_close.sort_index(), 
            'daily_high': daily_high.sort_index() if 'daily_high' in locals() else None,
            'daily_low': daily_low.sort_index() if 'daily_low' in locals() else None,
            'daily_volume': daily_volume.sort_index() if 'daily_volume' in locals() else None}

def calculate_forward_returns(close_df, horizons=[1, 5, 20]):
    print("Calculating Forward Returns...")
    fwd_returns = {}
    for h in horizons:
        # Return from Close(t) to Close(t+h)
        # Shifted back to align with t
        ret = close_df.pct_change(h).shift(-h)
        fwd_returns[h] = ret
    return fwd_returns

def calculate_ic(scores, fwd_returns):
    """
    Calculate Rank IC (Spearman) per day.
    """
    ic_series = scores.corrwith(fwd_returns, axis=1, method='spearman')
    return ic_series

def main():
    print("=== Alpha Health Check ===")
    
    # 1. Load Configuration & Universe
    alpha_catalog_path = project_root / "config" / "alpha_catalog.yaml"
    with open(alpha_catalog_path, 'r', encoding='utf-8') as f:
        catalog = yaml.safe_load(f)
    
    universe_file = PATHS.DATA_DIR / "real_universe.csv"
    universe_df = pd.read_csv(universe_file, dtype={'symbol': str})
    universe_symbols = universe_df['symbol'].tolist()
    
    # 2. Load Scores
    # A1 (Static CSV for now)
    scores_file = PATHS.DATA_DIR / "real_scores_2024.csv"
    scores_df = pd.read_csv(scores_file, dtype={'symbol': str})
    scores_df['date'] = pd.to_datetime(scores_df['date'])
    score_matrix_a1 = scores_df.pivot(index='date', columns='symbol', values='score')
    
    # A3/A4 (Dynamic - need to compute or load if cached)
    # For this check, let's focus on A1 first as it's the primary culprit.
    # TODO: Load A3/A4 from cache or recompute using Aggregator
    
    alphas = {
        'A1_trend_mom_6m': score_matrix_a1
    }
    
    # 3. Load Market Data & Compute Returns
    market_data = load_market_data(universe_symbols)
    close_df = market_data['daily_close']
    fwd_returns = calculate_forward_returns(close_df, horizons=[5, 20])
    
    # Compute A5 Scores
    print("Computing A5_vol_breakout...")
    from garam.alphas.a5_vol_breakout import A5VolBreakout
    a5 = A5VolBreakout('A5_vol_breakout', {})
    score_matrix_a5 = a5.compute_scores(market_data, universe_symbols)
    
    # Compute A6 Scores
    print("Computing A6_volume_shock...")
    from garam.alphas.a6_volume_shock import A6VolumeShock
    a6 = A6VolumeShock('A6_volume_shock', {})
    score_matrix_a6 = a6.compute_scores(market_data, universe_symbols)
    
    alphas = {
        'A1_trend_mom_6m': score_matrix_a1,
        'A5_vol_breakout': score_matrix_a5,
        'A6_volume_shock': score_matrix_a6
    }
    # Re-calculate regime history for the period
    market_proxy_file = Path("g:/내 드라이브/garamdata/history/KR_005930_SamsungElec_daily_20y.csv")
    market_history = pd.read_csv(market_proxy_file)
    market_history['timestamp'] = pd.to_datetime(market_history['timestamp'])
    market_history.set_index('timestamp', inplace=True)
    
    regime_history = {}
    # Calculate for relevant period (e.g., 2024-2025)
    dates = score_matrix_a1.index.sort_values()
    dates = [d for d in dates if d >= pd.to_datetime("2024-01-01")]
    
    print("Calculating Regimes...")
    for d in dates:
        subset = market_history.loc[:d]
        if len(subset) > 100:
            regime_history[d] = calculate_latest_micro_regime(subset)
            
    regime_series = pd.Series(regime_history)
    
    # 5. Analyze Performance
    results = []
    
    for alpha_id, scores in alphas.items():
        print(f"Analyzing {alpha_id}...")
        
        # Align dates
        common_dates = scores.index.intersection(fwd_returns[20].index).intersection(regime_series.index)
        scores_aligned = scores.loc[common_dates]
        ret20_aligned = fwd_returns[20].loc[common_dates]
        regimes_aligned = regime_series.loc[common_dates]
        
        # Calculate IC
        ic_daily = calculate_ic(scores_aligned, ret20_aligned)
        
        # Group by Regime
        df_analysis = pd.DataFrame({'ic': ic_daily, 'regime': regimes_aligned})
        regime_stats = df_analysis.groupby('regime')['ic'].agg(['mean', 'count', 'std'])
        
        print(f"\n--- {alpha_id} Performance by Regime (IC 20d) ---")
        print(regime_stats)
        
        # Save Report
        report_path = project_root / f"reports/alpha_health_{alpha_id}.csv"
        report_path.parent.mkdir(exist_ok=True)
        regime_stats.to_csv(report_path)
        print(f"Saved report to {report_path}")

if __name__ == "__main__":
    main()
