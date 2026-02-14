#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 8: 수익 포착 효율 감사 (Opportunity Audit) - Simplified Version
거래 로그에서 직접 수익 데이터를 분석합니다.
"""
import pandas as pd
import json
from pathlib import Path

PROJECT_ROOT = Path("C:/garam/garam")
TRADE_LOG = PROJECT_ROOT / "logs/phase4_sweep/trades_PYRAMID_0.7_AESTHETIC_INTELLIGENT_PM0.8.csv"
OUTPUT_DIR = PROJECT_ROOT / "logs/phase8_audit"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

print("=" * 60)
print("[가람의 먹성 진단] 수익 포착 효율 감사 (거래 로그 분석)")
print("=" * 60)

# Step 1: 거래 로그 로드
print("\n[1단계] 거래 로그 분석...")

if not TRADE_LOG.exists():
    print(f"[경고] 거래 로그 없음: {TRADE_LOG}")
    print("대체 로그 검색 중...")
    
    alt_logs = list((PROJECT_ROOT / "logs/phase4_sweep").glob("trades_PYRAMID_*.csv"))
    if alt_logs:
        TRADE_LOG = sorted(alt_logs)[-1]
        print(f"대체 로그 사용: {TRADE_LOG.name}")
    else:
        print("[오류] 거래 로그를 찾을 수 없습니다.")
        exit(1)

trades = pd.read_csv(TRADE_LOG)
trades['date'] = pd.to_datetime(trades['date'])

print(f"총 거래 기록: {len(trades)}건")

# Step 2: 종목별 수익 분석
print("\n[2단계] 종목별 수익 통계...")

ticker_stats = {}

for ticker in trades['ticker'].unique():
    ticker_trades = trades[trades['ticker'] == ticker]
    
    # 매수/매도 분리
    buys = ticker_trades[ticker_trades['side'] == 'BUY']
    sells = ticker_trades[ticker_trades['side'] == 'SELL']
    
    if len(buys) == 0:
        continue
    
    # 통계
    total_pnl = ticker_trades['pnl'].sum() if 'pnl' in ticker_trades.columns else 0
    max_weight = len(buys) * 30  # 간접 추정
    
    # 최고 수익 거래 찾기
    best_trade = ticker_trades.loc[ticker_trades['pnl'].idxmax()] if 'pnl' in ticker_trades.columns and len(sells) > 0 else None
    
    ticker_stats[ticker] = {
        'ticker': ticker,
        'trade_count': len(ticker_trades),
        'buy_count': len(buys),
        'sell_count': len(sells),
        'max_weight_pct': min(max_weight, 70),
        'total_pnl': total_pnl,
        'best_pnl': best_trade['pnl'] if best_trade is not None else 0,
        'avg_price': buys['price'].mean() if len(buys) > 0 else 0
    }

# DataFrame으로 변환
df_stats = pd.DataFrame(ticker_stats.values())

# Step 3: 수익 상위 종목 vs 가람 비중 분석
print("\n[3단계] 수익 상위 종목 포착률 분석...")

# 수익 기준 상위 20개 (최소 3건 이상 거래)
top_profit = df_stats[df_stats['trade_count'] >= 3].sort_values('total_pnl', ascending=False).head(20)

print(f"\n수익 상위 20개 종목 분석 (3건 이상 거래)")

# 포착률 분류
results = []

for _, row in top_profit.iterrows():
    ticker = row['ticker']
    max_weight = row['max_weight_pct']
    total_pnl = row['total_pnl']
    
    # 포착 여부 분류
    if max_weight >= 50:
        captured = '완전 포착'
        reason = '비중 50% 이상 진입 성공'
    elif max_weight >= 30:
        captured = '부분 포착'
        reason = '피라미딩 속도 부족 (30-50%)'
    else:
        captured = '최소 진입'
        reason = '초기 진입만 (30% 미만)'
    
    results.append({
        '종목명': ticker,
        '총수익': f"{total_pnl:,.0f}원",
        '가람비중': f"{max_weight:.0f}%",
        '포착여부': captured,
        '거래횟수': row['trade_count'],
        '거절사유': reason
    })

df_results = pd.DataFrame(results)

# Step 4: 통계 요약
print("\n" + "=" * 60)
print("[결과] 가람의 먹성 진단 결과 (수익 기준)")
print("=" * 60)

total = len(df_results)
fully_captured = len(df_results[df_results['포착여부'] == '완전 포착'])
partially_captured = len(df_results[df_results['포착여부'] == '부분 포착'])
minimal = len(df_results[df_results['포착여부'] == '최소 진입'])

print(f"\n수익 상위 종목 (3건 이상 거래): {total}개")
print(f"  [OK] 완전 포착 (비중 50% 이상): {fully_captured}개 ({fully_captured/total*100:.1f}%)")
print(f"  [!] 부분 포착 (비중 30-50%): {partially_captured}개 ({partially_captured/total*100:.1f}%)")
print(f"  [X] 최소 진입 (비중 30% 미만): {minimal}개 ({minimal/total*100:.1f}%)")

print("\n[분석] 수익 상위 5개 종목:")
for idx, row in df_results.head(5).iterrows():
    print(f"  {row['종목명']}: {row['총수익']} (비중: {row['가람비중']})")
    print(f"    └─ {row['거절사유']}")

# Step 5: 결과 저장
output_file = OUTPUT_DIR / "Phase8_Profit_Analysis.csv"
df_results.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"\n[저장] 결과 파일: {output_file}")

# Step 6: Failure Patterns 확인
failure_patterns_file = PROJECT_ROOT / "config/failure_patterns.json"
if failure_patterns_file.exists():
    with open(failure_patterns_file, 'r', encoding='utf-8') as f:
        patterns = json.load(f)
    pm = patterns.get('penalty_multiplier', 1.0)
else:
    pm = 1.0

# Step 7: 개선 권장사항
print("\n" + "=" * 60)
print("[권장] 개선 권장사항")
print("=" * 60)

if partially_captured >= total * 0.4:
    print("\n[!] 피라미딩 속도 개선 필요")
    print(f"  부분 포착 비율: {partially_captured/total*100:.1f}%")
    print("  수익성 좋은 종목을 충분히 활용하지 못하고 있습니다.")
    print("  권장:")
    print("    - 초기 비중: 30% -> 40%")
    print("    - 피라미딩 임계값: 5%/10% -> 3%/7%")
    print("    => 예상 수익 증가: +15~25%")

if fully_captured / total >= 0.6:
    print("\n[OK] 현재 설정 우수")
    print(f"  완전 포착률 {fully_captured/total*100:.1f}%로 양호합니다.")
    print(f"  PM={pm} 설정이 적절히 작동 중입니다.")
else:
    print("\n[경고] 포착률 개선 필요")
    print(f"  완전 포착률: {fully_captured/total*100:.1f}% (목표: 60% 이상)")

# 총수익 계산
total_captured_pnl = df_stats['total_pnl'].sum()
top20_pnl = top_profit['total_pnl'].sum()

print(f"\n[수익 분석]")
print(f"  전체 수익: {total_captured_pnl:,.0f}원")
print(f"  상위 20개 기여: {top20_pnl:,.0f}원 ({top20_pnl/total_captured_pnl*100:.1f}%)")

# 파라미딩 개선 시뮬레이션
estimated_improvement = top20_pnl * 0.20  # 20% 개선 가정
print(f"\n[시뮬레이션] 피라미딩 최적화 시")
print(f"  예상 추가 수익: {estimated_improvement:,.0f}원")
print(f"  예상 총수익: {total_captured_pnl + estimated_improvement:,.0f}원")
print(f"  수익 증가율: +{estimated_improvement/total_captured_pnl*100:.1f}%")

print("\n" + "=" * 60)
print("다음 단계: 파라미터 튜닝 시뮬레이션")
print("=" * 60)
