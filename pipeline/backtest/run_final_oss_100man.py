"""
GARAM OSS 최종 백테스트 (Dynamic AI-Driven Parameters)
- OSS (Optimal Strategy Selector) 통합
- 매 순간 AI가 최적 파라미터 결정
- 401개 종목, 100만원 투자
"""

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import glob
import torch

# Add parent to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from scripts.neural_brain import GaramNeuralBrain
    HAS_OSS = True
except:
    print("[WARNING] OSS Brain not found, using fallback logic")
    HAS_OSS = False

print("="*70)
print("🧠 GARAM OSS 최종 백테스트 (AI-Driven Dynamic Parameters)")
print("="*70)

# Load Data
data_dir = Path("c:/garam/garam/GARAM_Data/history/minute")
print(f"\n[Step 1] 데이터 로딩: {data_dir}")

files = glob.glob(str(data_dir / "*.csv"))
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
                print(f"  ... {loaded}개 로딩")
    except:
        pass

closes = pd.DataFrame(closes)
volumes = pd.DataFrame(volumes)

print(f"\n✅ {len(closes.columns)}개 종목 로딩 완료")
print(f"   기간: {closes.index[0]} ~ {closes.index[-1]}")

# Initialize OSS Brain
if HAS_OSS:
    brain = GaramNeuralBrain(input_size=5, mode="CUSTOM_45")
    print("✅ OSS Neural Brain 활성화")
else:
    brain = None
    print("⚠️  Fallback Mode (Static Parameters)")

# Calculate Market Features (for OSS input)
print("\n[Step 2] 시장 특성 계산...")
returns = closes.pct_change()
volatility = returns.rolling(20).std()
ma_fast = closes.rolling(5).mean()
ma_slow = closes.rolling(20).mean()
trend = (ma_fast - ma_slow) / (ma_slow + 1e-9)

# Generate AlphaGenius Signals
print("\n[Step 3] AlphaGenius V3 신호 생성...")
from run_alpha_robust import AlphaGenius_V2

alpha = AlphaGenius_V2()
signals = alpha.calculate_signals(closes, volumes)
exhaustion = alpha.calculate_exhaustion(closes, volumes)

print(f"   신호 수: {(signals > 0).sum().sum():,}개")
print(f"   최고 점수: {signals.max().max():.1f}")

# OSS Dynamic Parameter Function
def get_oss_params(idx, market_vol, market_trend):
    """
    OSS 개입: 현재 시장 상황에 맞는 최적 파라미터 반환
    """
    if not HAS_OSS or brain is None:
        # Fallback: Static
        return 7.5, 0.035, 0.05
    
    # Feature Vector: [Vol_Avg, Trend_Avg, Time_of_Day_Normalized, etc.]
    hour = (idx % 390) / 390  # Normalize time within trading day
    
    features = np.array([
        market_vol,
        market_trend,
        hour,
        0.0,  # Placeholder
        0.0   # Placeholder
    ], dtype=np.float32)
    
    # Normalize
    features = (features - np.mean(features)) / (np.std(features) + 1e-5)
    
    # Inference
    inp = torch.tensor(features).unsqueeze(0).to(brain.device)
    brain.eval()
    with torch.no_grad():
        out = brain.net(inp).cpu().numpy()[0]
    
    # Map outputs to params
    # Out[0] -> Threshold (7.0 ~ 9.0)
    # Out[1] -> Stop (2% ~ 6%)
    # Out[2] -> Target (4% ~ 10%)
    
    th = 7.0 + (1 / (1 + np.exp(-out[0]))) * 2.0  # Sigmoid to 7~9
    stop = 0.02 + (1 / (1 + np.exp(-out[1]))) * 0.04  # 2~6%
    target = 0.04 + (1 / (1 + np.exp(-out[2]))) * 0.06  # 4~10%
    
    return th, stop, target

# Simulation
print("\n[Step 4] 시뮬레이션 실행...")

capital = 1_000_000
cash = capital
position = {}
trades = []
equity_curve = []
oss_param_log = []

SLIPPAGE = 0.00125

for idx, ts in enumerate(closes.index):
    if idx < 20: continue  # Warmup
    if idx % 10000 == 0:
        print(f"   진행: {idx}/{len(closes)} ({idx/len(closes)*100:.0f}%)")
    
    # Market State
    market_vol = volatility.loc[ts].mean()
    market_trend = trend.loc[ts].mean()
    
    # OSS Intervention
    opt_th, opt_stop, opt_target = get_oss_params(idx, market_vol, market_trend)
    oss_param_log.append({'ts': ts, 'th': opt_th, 'stop': opt_stop, 'target': opt_target})
    
    current_prices = closes.loc[ts]
    current_signals = signals.loc[ts]
    current_exhaust = exhaustion.loc[ts]
    
    # Equity
    equity = cash
    for sym, qty in list(position.items()):
        curr_px = current_prices.get(sym, 0)
        if pd.isna(curr_px) or curr_px == 0:
            continue
        equity += qty * curr_px
        
        # Exit Logic (OSS-driven dynamic stop/target)
        entry = [t for t in trades if t['symbol'] == sym and t['type'] == 'BUY']
        if entry:
            entry_px = entry[-1]['price']
            ret = (curr_px / entry_px) - 1.0
            
            # Dynamic Stop/Target from OSS
            if ret < -opt_stop or ret > opt_target or current_exhaust.get(sym, False):
                exit_px = curr_px * (1 - SLIPPAGE)
                cash += qty * exit_px
                trades.append({'ts': ts, 'symbol': sym, 'type': 'SELL', 'price': exit_px, 'qty': qty, 'pnl': ret})
                del position[sym]
    
    # Entry Logic (OSS-driven dynamic threshold)
    if len(position) < 5 and cash > 100000:
        # Use OSS Threshold
        top_signals = current_signals[current_signals > opt_th].sort_values(ascending=False)
        
        for sym in top_signals.index[:1]:
            if sym in position:
                continue
            
            px = current_prices.get(sym, 0)
            if pd.isna(px) or px == 0:
                continue
            
            invest = min(cash * 0.2, cash)
            qty = int(invest / (px * (1 + SLIPPAGE)))
            
            if qty > 0:
                cost = qty * px * (1 + SLIPPAGE)
                cash -= cost
                position[sym] = qty
                trades.append({'ts': ts, 'symbol': sym, 'type': 'BUY', 'price': px, 'qty': qty})
                break
    
    equity_curve.append({'ts': ts, 'equity': equity})

# Results
final_equity = equity_curve[-1]['equity']
final_ret = (final_equity / capital) - 1.0

print("\n" + "="*70)
print("📈 OSS 최종 결과")
print("="*70)
print(f"초기 자본: 1,000,000원")
print(f"최종 자산: {final_equity:,.0f}원")
print(f"수익률:    {final_ret*100:+.2f}%")
print(f"순수익:    {final_equity - capital:+,.0f}원")

# OSS Adaptation Stats
oss_df = pd.DataFrame(oss_param_log)
print(f"\n🧠 OSS 적응 통계:")
print(f"   Threshold - 평균: {oss_df['th'].mean():.2f} (범위: {oss_df['th'].min():.2f} ~ {oss_df['th'].max():.2f})")
print(f"   Stop Loss - 평균: {oss_df['stop'].mean()*100:.1f}% (범위: {oss_df['stop'].min()*100:.1f}% ~ {oss_df['stop'].max()*100:.1f}%)")
print(f"   Target    - 평균: {oss_df['target'].mean()*100:.1f}% (범위: {oss_df['target'].min()*100:.1f}% ~ {oss_df['target'].max()*100:.1f}%)")

# Trade Stats
exits = [t for t in trades if t.get('pnl') is not None]
if exits:
    wins = [t for t in exits if t['pnl'] > 0]
    win_rate = len(wins) / len(exits) * 100
    print(f"\n🎯 거래 통계:")
    print(f"   총 거래: {len(exits)}회")
    print(f"   승률: {win_rate:.1f}%")

# Graph
print("\n[Step 5] 시각화 생성...")
eq_df = pd.DataFrame(equity_curve).set_index('ts')

plt.figure(figsize=(16, 10))
plt.style.use('dark_background')

# Equity
plt.subplot(3, 1, 1)
plt.plot(eq_df.index, eq_df['equity'], linewidth=2, color='cyan', label='OSS V3')
plt.axhline(y=capital, color='red', linestyle='--', alpha=0.5, label='원금')
plt.title('GARAM OSS 100만원 투자 결과 (Dynamic AI Parameters)', fontsize=16, weight='bold')
plt.ylabel('자산 (원)', fontsize=12)
plt.legend()
plt.grid(alpha=0.3)

# OSS Threshold Adaptation
plt.subplot(3, 1, 2)
plt.plot(oss_df['ts'], oss_df['th'], color='yellow', linewidth=1.5, alpha=0.8)
plt.title('OSS 동적 진입 임계치 (AI Adaptation)', fontsize=14)
plt.ylabel('Threshold', fontsize=12)
plt.grid(alpha=0.3)

# OSS Stop/Target
plt.subplot(3, 1, 3)
plt.plot(oss_df['ts'], oss_df['stop']*100, color='red', linewidth=1.5, alpha=0.8, label='Stop Loss')
plt.plot(oss_df['ts'], oss_df['target']*100, color='green', linewidth=1.5, alpha=0.8, label='Take Profit')
plt.title('OSS 동적 손절/익절 (AI Adaptation)', fontsize=14)
plt.ylabel('비율 (%)', fontsize=12)
plt.xlabel('날짜', fontsize=12)
plt.legend()
plt.grid(alpha=0.3)

plt.tight_layout()
output_path = "c:/garam/garam/GARAM_OSS_100man_result.png"
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
print(f"✅ 그래프 저장: {output_path}")

print("\n" + "="*70)
print("🏁 OSS 백테스트 완료")
print("="*70)
