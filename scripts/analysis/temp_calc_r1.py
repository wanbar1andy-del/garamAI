import pandas as pd
df = pd.read_csv('results/champion_v3_r1_top2_1y/trades_by_regime.csv')
r1 = df[df['entry_regime']=='R1_STRONG_UP']
print(f"R1 Trades: {len(r1)}")
if len(r1) > 0:
    print(f"R1 PnL: {r1['pnl'].sum():,.0f}")
    print(f"R1 WinRate: {len(r1[r1['pnl']>0])/len(r1)*100:.1f}%")
    print(f"R1 AvgRet: {r1['return_pct'].mean()*100:.2f}%")
else:
    print("No R1 Trades")
