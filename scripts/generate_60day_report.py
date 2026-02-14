
import pandas as pd
import numpy as np
import os

CSV_PATH = "GARAM_Data/60day_equity.csv"

def generate_report():
    if not os.path.exists(CSV_PATH):
        print("CSV not found")
        return

    df = pd.read_csv(CSV_PATH)
    if df.empty: return

    # Extract EOD Equity
    # Assuming 'ts' is datetime
    df['ts'] = pd.to_datetime(df['ts'])
    df['date'] = df['ts'].dt.date
    eod_df = df.groupby('date').last().reset_index()
    
    eod_df['return'] = eod_df['Total_Equity'].pct_change()
    
    total_return = (eod_df['Total_Equity'].iloc[-1] / 10_000_000) - 1
    days = len(eod_df)
    
    wins = eod_df[eod_df['return'] > 0]
    losses = eod_df[eod_df['return'] < 0]
    
    win_rate = len(wins) / days if days > 0 else 0
    avg_win = wins['return'].mean() if not wins.empty else 0
    avg_loss = losses['return'].mean() if not losses.empty else 0
    wl_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    
    # MDD
    eod_df['peak'] = eod_df['Total_Equity'].cummax()
    eod_df['dd'] = (eod_df['Total_Equity'] - eod_df['peak']) / eod_df['peak']
    mdd = eod_df['dd'].min()
    
    # Text Report
    report = f"""
# Phase 35: 60-Day Verification Report
## Strategy: Baseline (Vol 3.0 / TP 5%) + Minimal Defense

- **Period**: {eod_df['date'].iloc[0]} ~ {eod_df['date'].iloc[-1]} ({days} Days)
- **Total Return**: {total_return*100:.2f}%
- **Final Equity**: {eod_df['Total_Equity'].iloc[-1]:,.0f} KRW
- **MDD**: {mdd*100:.2f}%

## Statistics
- **Win Rate**: {win_rate*100:.2f}% ({len(wins)} Wins / {len(losses)} Losses)
- **Avg Win**: {avg_win*100:.2f}%
- **Avg Loss**: {avg_loss*100:.2f}%
- **Win/Loss Ratio**: {wl_ratio:.2f}

## Daily Log
"""
    for _, row in eod_df.iterrows():
        ret = row['return'] * 100 if not np.isnan(row['return']) else 0.0
        report += f"- {row['date']}: {row['Total_Equity']:,.0f} ({ret:+.2f}%)\n"
        
    print(report)
    with open("GARAM_Data/60day_report.md", "w", encoding="utf-8") as f:
        f.write(report)
        
if __name__ == "__main__":
    generate_report()
