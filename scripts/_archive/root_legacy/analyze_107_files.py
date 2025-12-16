# -*- coding: utf-8 -*-
"""107개 분 데이터 상세 분석"""
import pandas as pd
from pathlib import Path
from datetime import datetime

files = list(Path('garamdata/history/minute').glob('*_1m.csv'))
print(f"="*60)
print(f"107개 분 데이터 상세 분석")
print(f"="*60)

total_rows = 0
date_ranges = []
symbols = []

for i, file in enumerate(files):
    try:
        df = pd.read_csv(file)
        df['date'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
        
        symbols.append(file.stem.replace('_1m', ''))
        total_rows += len(df)
        
        dates = df['date'].dropna()
        if len(dates) > 0:
            date_ranges.append({
                'symbol': file.stem.replace('_1m', ''),
                'rows': len(df),
                'start': dates.min(),
                'end': dates.max(),
                'days': (dates.max() - dates.min()).days
            })
        
        if (i+1) % 20 == 0:
            print(f"  처리중... {i+1}/{len(files)}")
    except Exception as e:
        print(f"  오류 {file.name}: {e}")

print(f"\n{'='*60}")
print(f"전체 통계")
print(f"{'='*60}")
print(f"종목 수: {len(symbols)}")
print(f"총 행 수: {total_rows:,}")
print(f"평균 행/종목: {total_rows/len(symbols):,.0f}")

if date_ranges:
    df_ranges = pd.DataFrame(date_ranges)
    print(f"\n기간 분석:")
    print(f"  최소 일수: {df_ranges['days'].min()}일")
    print(f"  최대 일수: {df_ranges['days'].max()}일")
    print(f"  평균 일수: {df_ranges['days'].mean():.1f}일")
    print(f"  전체 기간: {df_ranges['start'].min()} ~ {df_ranges['end'].max()}")
    
    print(f"\n상위 5개 (행 수 기준):")
    for idx, row in df_ranges.nlargest(5, 'rows').iterrows():
        print(f"  {row['symbol']}: {row['rows']:,} rows ({row['days']}일)")
    
    print(f"\n하위 5개 (행 수 기준):")
    for idx, row in df_ranges.nsmallest(5, 'rows').iterrows():
        print(f"  {row['symbol']}: {row['rows']:,} rows ({row['days']}일)")

print(f"\n{'='*60}")
print("분석 완료!")
print(f"{'='*60}")
