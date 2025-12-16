#!/usr/bin/env python3
"""9월 하락 구간 분석"""
import pandas as pd

df = pd.read_csv('logs/daily_backtest_log.csv')
df['date'] = pd.to_datetime(df['date'])

# 9/19 고점부터 9/29까지
dd_period = df[(df['date'] >= '2025-09-19') & (df['date'] <= '2025-09-30')]

print("="*70)
print("9월 하락 구간 상세 분석 (9/19 고점 ~ 9/30)")
print("="*70)
print()

peak = dd_period.iloc[0]['equity']

for idx, row in dd_period.iterrows():
    dd = ((row['equity'] - peak) / peak) * 100
    ret_pct = row['daily_return'] * 100
    date_str = row['date'].strftime('%m/%d')
    equity_m = row['equity'] / 1e6
    pos = int(row['positions_count'])
    
    # 하락일 강조
    marker = "📉" if ret_pct < -1 else "📈" if ret_pct > 2 else "  "
    
    print(f"{marker} {date_str}: Equity {equity_m:6.1f}M ({ret_pct:+6.2f}%) "
          f"DD:{dd:+6.2f}% Pos:{pos}")

print()
print(f"고점 (9/19): {peak/1e6:.1f}M")
print(f"저점 (9/26): {dd_period['equity'].min()/1e6:.1f}M")
print(f"종가 (9/30): {dd_period.iloc[-1]['equity']/1e6:.1f}M")
print(f"최대 낙폭: {((dd_period['equity'].min() - peak) / peak * 100):.2f}%")
print(f"기간 낙폭: {((dd_period.iloc[-1]['equity'] - peak) / peak * 100):.2f}%")
print()
print(f"2종목 유지 일수: {(dd_period['positions_count'] == 2).sum()} / {len(dd_period)} 일")
