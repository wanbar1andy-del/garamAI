"""
GARAM 최종 실전 백테스트 (100만원 투자 결과)
- 데이터: history/minute 401개 종목
- 기간: 2025.06.01 ~ 2026.02.06
- 자본: 100만원
- 슬리피지: 0.25% (현실)
- 전략: AlphaGenius V3 (Prophet Mode)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import glob
from datetime import datetime

print("="*60)
print("🚀 GARAM 최종 실전 백테스트 (100만원 투자)")
print("="*60)

# 1. 데이터 로드
data_dir = Path("c:/garam/garam/GARAM_Data/history/minute")
print(f"\n[Step 1] 데이터 로딩 중: {data_dir}")

files = glob.glob(str(data_dir / "*.csv"))
symbols = [Path(f).stem for f in files if Path(f).stem != "desktop"]

closes = {}
volumes = {}
s_dt = pd.to_datetime("20250601")
e_dt = pd.to_datetime("20260206")

loaded = 0
for f in files:
    try:
        sym = Path(f).stem
        if sym == "desktop": continue
        
        df = pd.read_csv(f)
        df.columns = [c.lower() for c in df.columns]
        
        if "date" in df.columns:
            df["dt"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d%H%M%S", errors='coerce')
            if df["dt"].isnull().all():
                df["dt"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d%H%M", errors='coerce')
        
        df = df.dropna(subset=["dt"]).set_index("dt").sort_index()
        mask = (df.index >= s_dt) & (df.index <= e_dt)
        df = df.loc[mask]
        
        if not df.empty and "close" in df.columns and "volume" in df.columns:
            closes[sym] = df["close"]
            volumes[sym] = df["volume"]
            loaded += 1
            if loaded % 50 == 0:
                print(f"  ... {loaded}개 종목 로딩 완료")
    except:
        pass

closes = pd.DataFrame(closes)
volumes = pd.DataFrame(volumes)

print(f"\n✅ 총 {len(closes.columns)}개 종목 로딩 완료")
print(f"   기간: {closes.index[0]} ~ {closes.index[-1]}")
print(f"   총 {len(closes)} 개 분봉 데이터")

# 2. 시장 진단
print("\n" + "="*60)
print("[Step 2] 시장 분석 (2025.06 ~ 2026.02)")
print("="*60)

# 종목별 수익률
returns = (closes.iloc[-1] / closes.iloc[0]) - 1.0
returns = returns.sort_values(ascending=False)

# 시장 평균 (Equal Weight)
market_avg = returns.mean()

print(f"\n📊 시장 통계:")
print(f"   전체 평균 수익률: {market_avg*100:+.2f}%")
print(f"   중간값: {returns.median()*100:+.2f}%")
print(f"   상위 25%: {returns.quantile(0.75)*100:+.2f}%")
print(f"   하위 25%: {returns.quantile(0.25)*100:+.2f}%")

print(f"\n🏆 Top 10 히어로 종목:")
for i, (sym, ret) in enumerate(returns.head(10).items(), 1):
    start_px = closes[sym].iloc[0]
    end_px = closes[sym].iloc[-1]
    print(f"   {i:2d}. {sym}: {start_px:>8,.0f} → {end_px:>8,.0f} ({ret*100:+6.1f}%)")

print(f"\n💀 Bottom 10 최악 종목:")
for i, (sym, ret) in enumerate(returns.tail(10).items(), 1):
    start_px = closes[sym].iloc[0]
    end_px = closes[sym].iloc[-1]
    print(f"   {i:2d}. {sym}: {start_px:>8,.0f} → {end_px:>8,.0f} ({ret*100:+6.1f}%)")

# 3. 벤치마크: 삼성전자 Buy & Hold
print("\n" + "="*60)
print("[Step 3] 벤치마크: 삼성전자(005930) 단순 보유")
print("="*60)

if "005930" in closes.columns:
    samsung_start = closes["005930"].iloc[0]
    samsung_end = closes["005930"].iloc[-1]
    samsung_ret = (samsung_end / samsung_start) - 1.0
    
    capital = 1_000_000
    shares = int(capital / (samsung_start * 1.00125))  # 0.125% 매수 수수료
    invest = shares * samsung_start * 1.00125
    final = shares * samsung_end * 0.99875  # 0.125% 매도 수수료
    net_ret = (final / capital) - 1.0
    
    print(f"   시작가: {samsung_start:,.0f} 원")
    print(f"   종가:   {samsung_end:,.0f} 원")
    print(f"   총 수익률: {samsung_ret*100:+.2f}%")
    print(f"\n   💰 100만원 투자 결과:")
    print(f"      매수: {shares:,}주 x {samsung_start:,.0f}원 = {invest:,.0f}원")
    print(f"      매도: {shares:,}주 x {samsung_end:,.0f}원 = {final:,.0f}원")
    print(f"      순수익: {final - capital:+,.0f}원 ({net_ret*100:+.2f}%)")

# 4. AlphaGenius V3 전략
print("\n" + "="*60)
print("[Step 4] AlphaGenius V3 전략 실행 중...")
print("="*60)

from run_alpha_robust import AlphaGenius_V2

alpha = AlphaGenius_V2()
signals = alpha.calculate_signals(closes, volumes)
exhaustion = alpha.calculate_exhaustion(closes, volumes)

print(f"   생성된 신호 수: {(signals > 0).sum().sum():,}개")
print(f"   최고 확신 점수: {signals.max().max():.1f}점")

# 간단한 시뮬레이션
capital = 1_000_000
cash = capital
position = {}  # {symbol: qty}
trades = []
equity_curve = []

SLIPPAGE = 0.00125  # 0.125% (편도)
STOP_LOSS = 0.03
TAKE_PROFIT = 0.05

for idx, ts in enumerate(closes.index):
    if idx % 10000 == 0:
        print(f"   진행: {idx}/{len(closes)} ({idx/len(closes)*100:.1f}%)")
    
    current_prices = closes.loc[ts]
    current_signals = signals.loc[ts]
    current_exhaust = exhaustion.loc[ts]
    
    # 현재 순자산 계산
    equity = cash
    for sym, qty in list(position.items()):
        curr_px = current_prices.get(sym, 0)
        if pd.isna(curr_px) or curr_px == 0:
            continue
        equity += qty * curr_px
        
        # Exit 조건
        entry_px = [t for t in trades if t['symbol'] == sym and t['type'] == 'BUY']
        if entry_px:
            entry_px = entry_px[-1]['price']
            ret = (curr_px / entry_px) - 1.0
            
            # Stop Loss or Take Profit
            if ret < -STOP_LOSS or ret > TAKE_PROFIT or current_exhaust.get(sym, False):
                exit_px = curr_px * (1 - SLIPPAGE)
                cash += qty * exit_px
                trades.append({'ts': ts, 'symbol': sym, 'type': 'SELL', 'price': exit_px, 'qty': qty, 'pnl': ret})
                del position[sym]
    
    # Entry 조건
    if len(position) < 5 and cash > 100000:  # 최대 5개 동시 보유
        # 가장 높은 점수 종목 선택
        top_signals = current_signals[current_signals > 7.0].sort_values(ascending=False)
        
        for sym in top_signals.index[:1]:  # 한 번에 1개만
            if sym in position:
                continue
            
            px = current_prices.get(sym, 0)
            if pd.isna(px) or px == 0:
                continue
            
            # 20% 자본 투자
            invest = min(cash * 0.2, cash)
            qty = int(invest / (px * (1 + SLIPPAGE)))
            
            if qty > 0:
                cost = qty * px * (1 + SLIPPAGE)
                cash -= cost
                position[sym] = qty
                trades.append({'ts': ts, 'symbol': sym, 'type': 'BUY', 'price': px, 'qty': qty})
                break
    
    equity_curve.append({'ts': ts, 'equity': equity})

final_equity = equity_curve[-1]['equity']
final_ret = (final_equity / capital) - 1.0

print(f"\n✅ 시뮬레이션 완료!")
print(f"   총 거래 횟수: {len([t for t in trades if t['type'] == 'BUY'])}회")

# 5. 최종 보고서
print("\n" + "="*60)
print("📈 GARAM 최종 투자 결과 (2025.06 ~ 2026.02)")
print("="*60)

print(f"\n💰 투자 성과:")
print(f"   초기 자본:  1,000,000 원")
print(f"   최종 자산:  {final_equity:,.0f} 원")
print(f"   순수익:     {final_equity - capital:+,.0f} 원")
print(f"   수익률:     {final_ret*100:+.2f}%")

if "005930" in closes.columns:
    print(f"\n📊 벤치마크 비교:")
    print(f"   삼성전자 Buy & Hold: {net_ret*100:+.2f}%")
    print(f"   AlphaGenius V3:      {final_ret*100:+.2f}%")
    if final_ret > net_ret:
        print(f"   ✅ 벤치마크 초과 달성: +{(final_ret - net_ret)*100:.2f}%p")
    else:
        print(f"   ⚠️  벤치마크 미달: {(final_ret - net_ret)*100:.2f}%p")

print(f"\n🎯 거래 통계:")
exits = [t for t in trades if t.get('pnl') is not None]
if exits:
    wins = [t for t in exits if t['pnl'] > 0]
    win_rate = len(wins) / len(exits) * 100 if exits else 0
    avg_win = np.mean([t['pnl'] for t in wins]) * 100 if wins else 0
    avg_loss = np.mean([t['pnl'] for t in exits if t['pnl'] <= 0]) * 100 if len(exits) > len(wins) else 0
    
    print(f"   총 거래: {len(exits)}회")
    print(f"   승률: {win_rate:.1f}%")
    print(f"   평균 수익: {avg_win:+.2f}%")
    print(f"   평균 손실: {avg_loss:+.2f}%")

# 6. 그래프 생성
print("\n[Step 5] 그래프 생성 중...")

eq_df = pd.DataFrame(equity_curve).set_index('ts')

plt.figure(figsize=(14, 8))
plt.style.use('dark_background')

# Equity Curve
plt.subplot(2, 1, 1)
plt.plot(eq_df.index, eq_df['equity'], linewidth=2, color='cyan', label='AlphaGenius V3')
plt.axhline(y=capital, color='red', linestyle='--', alpha=0.5, label='원금 (100만원)')

if "005930" in closes.columns:
    # Samsung Benchmark
    samsung_equity = (closes["005930"] / samsung_start) * capital
    samsung_equity = samsung_equity * 0.9975  # 슬리피지 반영
    plt.plot(samsung_equity.index, samsung_equity, linewidth=2, color='yellow', alpha=0.7, label='삼성전자 (BuyHold)')

plt.title('GARAM 100만원 투자 결과 (2025.06~2026.02)', fontsize=16, fontweight='bold')
plt.ylabel('자산 (원)', fontsize=12)
plt.legend(loc='upper left', fontsize=10)
plt.grid(alpha=0.3)

# Drawdown
plt.subplot(2, 1, 2)
running_max = eq_df['equity'].cummax()
drawdown = (eq_df['equity'] / running_max - 1) * 100
plt.fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.3)
plt.plot(drawdown.index, drawdown, color='red', linewidth=1.5)
plt.title('Drawdown', fontsize=14)
plt.ylabel('낙폭 (%)', fontsize=12)
plt.xlabel('날짜', fontsize=12)
plt.grid(alpha=0.3)

plt.tight_layout()
output_path = "c:/garam/garam/GARAM_final_100man_result.png"
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
plt.close()

print(f"✅ 그래프 저장 완료: {output_path}")

print("\n" + "="*60)
print("🏁 GARAM 최종 백테스트 완료")
print("="*60)
