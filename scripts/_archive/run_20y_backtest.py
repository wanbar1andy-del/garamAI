"""
Run 20-Year Backtest
Simulates trading performance over the last 20 years using the current Regime Strategy Matrix.
"""

import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS

def run_backtest():
    # 1. Load Config
    config_path = PATHS.CONFIG_DIR / "regime_strategy_matrix.yaml"
    if not config_path.exists():
        print(f"Error: Config not found at {config_path}")
        return

    with open(config_path) as f:
        matrix = yaml.safe_load(f)
    
    print("Loaded Strategy Matrix:")
    for r, c in matrix.items():
        print(f"  {r}: {c['strategy']} {c['params']}")

    # 2. Load Data
    data_path = Path("g:/내 드라이브/garamdata/history/labeled_KR_KOSPI_daily_20y.csv")
    if not data_path.exists():
        print(f"Error: Data not found at {data_path}")
        return

    df = pd.read_csv(data_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').sort_index()
    
    # Filter for last 20 years (approx 2005)
    df = df[df.index >= '2005-01-01']
    
    print(f"\nLoaded {len(df)} days of data ({df.index[0].date()} to {df.index[-1].date()})")

    # 3. Pre-calculate Indicators
    # We calculate all indicators used in the matrix to avoid overhead in the loop
    # This assumes we know the params. For robustness, we'll calculate what's needed.
    
    # Helper to get params safely
    def get_param(regime, key):
        return matrix.get(regime, {}).get('params', {}).get(key)

    # Trend Following MAs
    mas_needed = set()
    for r in ['GREEN', 'RED']: # Usually Trend Following
        if matrix.get(r, {}).get('strategy') == 'TrendFollowing':
            p = matrix[r]['params']
            mas_needed.add(p['window_fast'])
            mas_needed.add(p['window_slow'])
    
    for w in mas_needed:
        df[f'ma_{w}'] = df['close'].rolling(window=w).mean()

    # Mean Reversion Bands
    # Pre-calculate for ALL regimes that use MeanReversion
    for r in matrix:
        if matrix[r]['strategy'] == 'MeanReversion':
            p = matrix[r]['params']
            w = p['window']
            std = p['std_dev']
            
            # Create unique column names for this setting
            col_ma = f'ma_{w}'
            col_std = f'std_{w}'
            col_upper = f'upper_{w}_{std}'
            col_lower = f'lower_{w}_{std}'
            
            if col_ma not in df.columns:
                df[col_ma] = df['close'].rolling(window=w).mean()
            if col_std not in df.columns:
                df[col_std] = df['close'].rolling(window=w).std()
                
            df[col_upper] = df[col_ma] + (df[col_std] * std)
            df[col_lower] = df[col_ma] - (df[col_std] * std)

    # 4. Simulation Loop
    capital = 10000.0
    equity = capital
    position = 0 # 1 (Long), -1 (Short), 0 (Flat)
    entry_price = 0.0
    
    equity_curve = []
    trades = []
    
    # We need to iterate. 
    # Signal at T determines position for T+1 (or Close of T).
    # Let's assume we trade at Close of T based on signal at T.
    
    for i in range(len(df)):
        date = df.index[i]
        row = df.iloc[i]
        regime = row['state']
        close = row['close']
        
        # 1. Update Equity (Mark to Market)
        # If we held a position from previous step
        if i > 0:
            prev_close = df.iloc[i-1]['close']
            if position != 0:
                pnl = (close - prev_close) * position * (capital / prev_close) # Simple compounding approximation
                # Better: equity = equity * (1 + ret * pos)
                ret = (close - prev_close) / prev_close
                equity = equity * (1 + ret * position)
        
        equity_curve.append({'date': date, 'equity': equity})

        # 2. Generate Signal for NEXT period (or execute now)
        # Strategy Logic
        strat_config = matrix.get(regime)
        if not strat_config:
            position = 0
            continue
            
        strat_name = strat_config['strategy']
        params = strat_config['params']
        
        signal = 0
        
        if strat_name == 'TrendFollowing':
            fast = row.get(f"ma_{params['window_fast']}")
            slow = row.get(f"ma_{params['window_slow']}")
            if pd.notna(fast) and pd.notna(slow):
                if fast > slow: signal = 1
                elif fast < slow: signal = -1 # Or 0
                
        elif strat_name == 'MeanReversion':
            w = params['window']
            std = params['std_dev']
            upper = row.get(f'upper_{w}_{std}')
            lower = row.get(f'lower_{w}_{std}')
            
            if pd.notna(upper) and pd.notna(lower):
                if close < lower: signal = 1
                elif close > upper: signal = -1 # Or 0
                else: signal = position # Hold? Or 0? MR usually holds until cross.
                # Simple MR: Buy < Lower, Sell > Upper. Hold in between? 
                # Let's assume Hold in between for now.
        
        # 3. Execution (Change Position)
        # If signal changes, we trade.
        # Transaction costs? Let's ignore for now or add small slippage.
        if signal != position:
            # Trade happens
            position = signal
            
    # 5. Analysis
    equity_series = pd.Series([e['equity'] for e in equity_curve], index=df.index)
    
    total_return = (equity - capital) / capital
    cagr = (equity / capital) ** (365 / (df.index[-1] - df.index[0]).days) - 1
    
    # MDD
    rolling_max = equity_series.cummax()
    drawdown = (equity_series - rolling_max) / rolling_max
    max_dd = drawdown.min()
    
    # Sharpe
    daily_rets = equity_series.pct_change().dropna()
    sharpe = (daily_rets.mean() / daily_rets.std()) * np.sqrt(252) if daily_rets.std() > 0 else 0
    
    print("\n" + "="*40)
    print("20-YEAR BACKTEST RESULTS (GARAM SYSTEM)")
    print("="*40)
    print(f"Period       : {df.index[0].date()} ~ {df.index[-1].date()}")
    print(f"Initial Cap  : ${capital:,.0f}")
    print(f"Final Equity : ${equity:,.0f}")
    print("-" * 40)
    print(f"Total Return : {total_return*100:,.2f}%")
    print(f"CAGR         : {cagr*100:.2f}%")
    print(f"MDD          : {max_dd*100:.2f}%")
    print(f"Sharpe Ratio : {sharpe:.2f}")
    print("="*40)

if __name__ == "__main__":
    run_backtest()
