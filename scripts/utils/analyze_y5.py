
import pandas as pd
from pathlib import Path

LOG_FILE = Path("C:/garam/garam/logs/y1_daily/trade_log.csv")

if not LOG_FILE.exists():
    print(f"Error: {LOG_FILE} not found.")
else:
    df = pd.read_csv(LOG_FILE)
    print("--- Trade Analysis ---")
    print(f"Total Trades: {len(df)}")
    
    # Exit Analysis (Side = SELL)
    exits = df[df['side'] == 'SELL']
    print(f"\nTotal Exits: {len(exits)}")
    
    # Clean Reason Codes
    df['reason_group'] = df['reason'].apply(lambda x: x.split(' for ')[0] if ' for ' in x else x)
    
    summary = df[df['side']=='SELL'].groupby('reason_group')['pnl'].agg(['count', 'mean', 'sum'])
    summary['mean_pnl_pct'] = (summary['sum'] / 100_000_000) * 100 
    print(summary)
    
    # Hero Analysis
    print("\n--- Hero Analysis (SK Hynix) ---")
    sk = df[df['ticker'].astype(str).str.contains('660')]
    print(sk)
