import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.append("C:\\garam")
from garam.config import PATHS

def analyze():
    print("=== Simulation Performance Analysis ===")
    
    # 1. Load Data
    snapshot_path = PATHS.ACCOUNT_SNAPSHOT
    trades_path = PATHS.LIVE_TRADES
    
    if not snapshot_path.exists():
        print("No account snapshot found.")
        return
        
    df_curve = pd.read_csv(snapshot_path)
    df_curve['timestamp'] = pd.to_datetime(df_curve['timestamp'])
    df_curve.sort_values('timestamp', inplace=True)
    
    # 2. Calculate Deployment Rate
    # Deployment = (Equity - Cash) / Equity
    # Handle NaN equity (though we fixed it, good to be safe)
    df_curve['total_equity'] = df_curve['total_equity'].astype(float)
    df_curve['cash'] = df_curve['cash'].astype(float)
    
    df_curve['invested'] = df_curve['total_equity'] - df_curve['cash']
    df_curve['deployment_rate'] = df_curve['invested'] / df_curve['total_equity']
    
    avg_deployment = df_curve['deployment_rate'].mean()
    max_deployment = df_curve['deployment_rate'].max()
    min_deployment = df_curve['deployment_rate'].min()
    
    print(f"\n[Capital Deployment]")
    print(f"Average Rate: {avg_deployment*100:.2f}%")
    print(f"Max Rate:     {max_deployment*100:.2f}%")
    print(f"Min Rate:     {min_deployment*100:.2f}%")
    
    # 3. Drawdown Analysis
    df_curve['peak'] = df_curve['total_equity'].cummax()
    df_curve['drawdown'] = df_curve['total_equity'] - df_curve['peak']
    df_curve['drawdown_pct'] = (df_curve['drawdown'] / df_curve['peak']) * 100
    
    max_dd_row = df_curve.loc[df_curve['drawdown'].idxmin()]
    max_dd_val = max_dd_row['drawdown']
    max_dd_pct = max_dd_row['drawdown_pct']
    max_dd_date = max_dd_row['timestamp'].date()
    
    print(f"\n[Drawdown]")
    print(f"Max Drawdown: {max_dd_val:,.0f} KRW ({max_dd_pct:.2f}%) on {max_dd_date}")
    
    # 4. Reason for Drawdown
    # Load Trades
    df_trades = pd.read_csv(trades_path)
    df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp'])
    
    # Match Buy/Sell to rough PnL (FIFO)
    # Dictionary of queues for each symbol
    positions = {} # sym: [ {qty, price} ]
    closed_trades = []
    
    for _, row in df_trades.iterrows():
        sym = row['symbol']
        action = row['type']
        qty = int(row['qty'])
        price = float(row['price'])
        date = row['timestamp']
        
        if action == 'BUY':
            if sym not in positions: positions[sym] = []
            positions[sym].append({'qty': qty, 'price': price, 'date': date})
        elif action == 'SELL':
            if sym in positions and positions[sym]:
                # Match against oldest buy (FIFO)
                remaining_sell = qty
                pnl_total = 0
                cost_basis = 0
                
                while remaining_sell > 0 and positions[sym]:
                    buy = positions[sym][0]
                    match_qty = min(remaining_sell, buy['qty'])
                    
                    trade_pnl = (price - buy['price']) * match_qty
                    pnl_total += trade_pnl
                    cost_basis += buy['price'] * match_qty
                    
                    buy['qty'] -= match_qty
                    remaining_sell -= match_qty
                    
                    if buy['qty'] == 0:
                        positions[sym].pop(0)
                        
                # Log closed trade result
                pnl_pct = (pnl_total / cost_basis) * 100 if cost_basis > 0 else 0
                closed_trades.append({
                    'symbol': sym,
                    'name': row.get('name', sym),
                    'sell_date': date,
                    'pnl': pnl_total,
                    'pnl_pct': pnl_pct
                })

    df_closed = pd.DataFrame(closed_trades)
    
    print("\n[Trade Analysis]")
    if not df_closed.empty:
        total_realized = df_closed['pnl'].sum()
        win_rate = len(df_closed[df_closed['pnl'] > 0]) / len(df_closed) * 100
        print(f"Total Realized PnL: {total_realized:,.0f} KRW")
        print(f"Win Rate:           {win_rate:.1f}%")
        
        print("\nTop 5 Losing Trades:")
        losers = df_closed.sort_values('pnl').head(5)
        for _, row in losers.iterrows():
            print(f"- {row['name']} ({row['symbol']}): {row['pnl']:,.0f} KRW ({row['pnl_pct']:.2f}%) on {row['sell_date'].date()}")
    else:
        print("No closed trades to analyze.")
        
    # Generate Report
    report_path = PATHS.REPORTS_DIR / "Analysis_Capital_Drawdown.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 📉 Capital Usage & Drawdown Analysis\n\n")
        
        f.write("## 1. Capital Deployment (자본 투입율)\n")
        f.write(f"- **Average Deployment**: {avg_deployment*100:.2f}%\n")
        f.write(f"- **Max Deployment**: {max_deployment*100:.2f}%\n")
        f.write(f"- **Analysis**: ")
        if avg_deployment < 0.3:
            f.write("Average deployment is low (<30%). The system is holding significant cash, possibly due to strict risk controls or lack of buy signals.\n")
        elif avg_deployment > 0.8:
             f.write("Average deployment is high (>80%). The system is fully utilized.\n")
        else:
             f.write("Average deployment is moderate.\n")
             
        f.write("\n## 2. Drawdown Causes (자본 하락 원인)\n")
        f.write(f"- **Max Drawdown**: {max_dd_val:,.0f} KRW ({max_dd_pct:.2f}%) on {max_dd_date}\n")
        
        if not df_closed.empty:
            f.write("\n### Top Realized Losses\n")
            f.write("| Symbol | Name | Sell Date | PnL (KRW) | PnL (%) |\n")
            f.write("|:---|:---|:---|:---|:---|\n")
            for _, row in losers.iterrows():
                f.write(f"| {row['symbol']} | {row['name']} | {row['sell_date'].date()} | {row['pnl']:,.0f} | {row['pnl_pct']:.2f}% |\n")
        
        f.write("\n### Specific Observations\n")
        # Check if drawdown matches a specific bad trade day or gradual bleed
        if max_dd_pct < -5:
            f.write("- Significant drawdown detected. Major losses from specific trades likely contributed.\n")
        else:
            f.write("- Drawdown is within normal variance (<5%). Likely due to slippage or minor stop losses.\n")
            
    print(f"\nAnalysis saved to {report_path}")

if __name__ == "__main__":
    analyze()
