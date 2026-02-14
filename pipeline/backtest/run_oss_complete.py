"""
OSS 집중 학습 및 백테스트 (Complete Pipeline)
1. OSS 학습 (유전 알고리즘 + Neural Network)
2. 학습된 OSS로 401개 종목 백테스트
3. 100만원 투자 최종 결과
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
import copy

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

print("="*80)
print("🧠 GARAM OSS 집중 학습 및 백테스트 시스템")
print("="*80)

# Phase 1: OSS 학습
print("\n[Phase 1] OSS 학습 (Genetic Algorithm + Neural Network)")
print("-"*80)

try:
    from scripts.neural_brain import GaramNeuralBrain
    # [FIX] GaramNeuralBrain.__init__ does not take hidden_size
    brain = GaramNeuralBrain(input_size=5, mode="MAX")
    print("✅ Neural Brain 초기화 완료 (MAX 하드웨어 모드)")
except Exception as e:
    print(f"⚠️  Neural Brain 초기화 실패: {e}")
    import traceback
    traceback.print_exc()
    brain = None

# OSS Genome (전략 유전자)
class OSSGenome:
    def __init__(self):
        self.entry_threshold = 7.5
        self.stop_loss = 0.035
        self.take_profit = 0.055
        self.position_size = 0.2
        self.max_positions = 5
    
    def mutate(self):
        import random
        g = copy.deepcopy(self)
        g.entry_threshold *= random.uniform(0.9, 1.1)
        g.stop_loss *= random.uniform(0.9, 1.1)
        g.take_profit *= random.uniform(0.9, 1.1)
        return g

# 간단한 백테스트 함수 (OSS Fitness 평가용)
def evaluate_oss(genome, closes, volumes, signals):
    """OSS Genome의 성능 평가"""
    capital = 1_000_000
    cash = capital
    position = {}
    equity_curve = []
    
    for idx, ts in enumerate(closes.index):
        if idx < 100: continue
        
        current_prices = closes.loc[ts]
        current_signals = signals.loc[ts]
        
        equity = cash
        for sym, qty in list(position.items()):
            curr_px = current_prices.get(sym, 0)
            if pd.isna(curr_px) or curr_px == 0:
                continue
            equity += qty * curr_px
            
            # Exit
            entry_info = position[sym]
            ret = (curr_px / entry_info['entry_px']) - 1.0
            
            if ret < -genome.stop_loss or ret > genome.take_profit:
                cash += qty * curr_px * 0.9975
                del position[sym]
        
        # Entry
        if len(position) < genome.max_positions and cash > 100000:
            top_sig = current_signals[current_signals > genome.entry_threshold].sort_values(ascending=False)
            
            for sym in top_sig.index[:1]:
                if sym in position: continue
                px = current_prices.get(sym, 0)
                if pd.isna(px) or px == 0: continue
                
                invest = min(cash * genome.position_size, cash)
                qty = int(invest / (px * 1.00125))
                if qty > 0:
                    cash -= qty * px * 1.00125
                    position[sym] = {'entry_px': px, 'qty': qty}
                    break
        
        equity_curve.append(equity)
    
    if not equity_curve:
        return -999
    
    final = equity_curve[-1]
    ret = (final / capital - 1) * 100
    
    # MDD
    peak = capital
    mdd = 0
    for eq in equity_curve:
        if eq > peak: peak = eq
        dd = (eq / peak - 1)
        if dd < mdd: mdd = dd
    
    # Fitness = Return - MDD/2
    fitness = ret - abs(mdd * 100 * 0.5)
    return fitness

# Phase 2: 데이터 로드
print("\n[Phase 2] 데이터 로드")
print("-"*80)

import glob
data_dir = Path("c:/garam/garam/GARAM_Data/history/minute")
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
            if loaded % 100 == 0:
                print(f"  ... {loaded}개 로딩")
    except:
        pass

closes = pd.DataFrame(closes)
volumes = pd.DataFrame(volumes)
print(f"✅ {len(closes.columns)}개 종목 로딩 완료")

# Phase 3: Signal 생성
print("\n[Phase 3] AlphaGenius 신호 생성")
print("-"*80)

from run_alpha_robust import AlphaGenius_V2
alpha = AlphaGenius_V2()
signals = alpha.calculate_signals(closes, volumes)
print(f"✅ 신호 생성 완료: {(signals > 0).sum().sum():,}개")

# Phase 4: OSS 진화
print("\n[Phase 4] OSS 진화 (Genetic Algorithm)")
print("-"*80)

pop_size = 20
generations = 5

population = [OSSGenome() for _ in range(pop_size)]

# Diversity seed
for i, g in enumerate(population):
    g.entry_threshold = 6.0 + (3.0 * i / pop_size)
    g.stop_loss = 0.02 + (0.04 * i / pop_size)
    g.take_profit = 0.03 + (0.07 * i / pop_size)

best_genome = None
best_fitness = -999

for gen in range(generations):
    print(f"\n[Generation {gen+1}/{generations}]")
    
    # Parallel evaluation
    fitness_scores = []
    for genome in population:
        score = evaluate_oss(genome, closes, volumes, signals)
        fitness_scores.append((genome, score))
    
    fitness_scores.sort(key=lambda x: x[1], reverse=True)
    winner = fitness_scores[0]
    
    print(f"  🏆 Best Fitness: {winner[1]:.2f}")
    print(f"     Params: Th={winner[0].entry_threshold:.2f}, Stop={winner[0].stop_loss*100:.1f}%, Target={winner[0].take_profit*100:.1f}%")
    
    if winner[1] > best_fitness:
        best_fitness = winner[1]
        best_genome = copy.deepcopy(winner[0])
    
    # Evolve
    new_pop = [copy.deepcopy(winner[0])]
    for _ in range(pop_size - 1):
        new_pop.append(winner[0].mutate())
    population = new_pop

# Save Best OSS
config_path = PROJECT_ROOT / "config/oss_trained_params.json"
config_path.parent.mkdir(exist_ok=True, parents=True)

with open(config_path, 'w') as f:
    json.dump({
        'entry_threshold': best_genome.entry_threshold,
        'stop_loss': best_genome.stop_loss,
        'take_profit': best_genome.take_profit,
        'position_size': best_genome.position_size,
        'max_positions': best_genome.max_positions,
        'fitness': best_fitness
    }, f, indent=4)

print(f"\n✅ OSS 학습 완료! 저장: {config_path}")

# Phase 5: 최종 백테스트
print("\n" + "="*80)
print("[Phase 5] 학습된 OSS로 최종 백테스트")
print("="*80)

final_fitness = evaluate_oss(best_genome, closes, volumes, signals)

# 상세 시뮬레이션
capital = 1_000_000
cash = capital
position = {}
trades = []
equity_curve = []

for idx, ts in enumerate(closes.index):
    if idx < 100: continue
    
    current_prices = closes.loc[ts]
    current_signals = signals.loc[ts]
    
    equity = cash
    for sym, qty in list(position.items()):
        curr_px = current_prices.get(sym, 0)
        if pd.isna(curr_px) or curr_px == 0:
            continue
        equity += qty * curr_px
        
        entry_info = position[sym]
        ret = (curr_px / entry_info['entry_px']) - 1.0
        
        if ret < -best_genome.stop_loss or ret > best_genome.take_profit:
            exit_px = curr_px * 0.9975
            cash += qty * exit_px
            trades.append({'pnl': ret})
            del position[sym]
    
    if len(position) < best_genome.max_positions and cash > 100000:
        top_sig = current_signals[current_signals > best_genome.entry_threshold].sort_values(ascending=False)
        
        for sym in top_sig.index[:1]:
            if sym in position: continue
            px = current_prices.get(sym, 0)
            if pd.isna(px) or px == 0: continue
            
            invest = min(cash * best_genome.position_size, cash)
            qty = int(invest / (px * 1.00125))
            if qty > 0:
                cash -= qty * px * 1.00125
                position[sym] = {'entry_px': px, 'qty': qty}
                break
    
    equity_curve.append({'ts': ts, 'equity': equity})

final_eq = equity_curve[-1]['equity']
final_ret = (final_eq / capital - 1) * 100

print(f"\n💰 최종 결과:")
print(f"   초기 자본: 1,000,000원")
print(f"   최종 자산: {final_eq:,.0f}원")
print(f"   수익률:    {final_ret:+.2f}%")
print(f"   순수익:    {final_eq - capital:+,.0f}원")

wins = [t for t in trades if t['pnl'] > 0]
if trades:
    print(f"\n🎯 거래 통계:")
    print(f"   총 거래: {len(trades)}회")
    print(f"   승률: {len(wins)/len(trades)*100:.1f}%")

print(f"\n🧬 OSS 최종 DNA:")
print(f"   진입 임계치: {best_genome.entry_threshold:.2f}")
print(f"   손절: {best_genome.stop_loss*100:.1f}%")
print(f"   익절: {best_genome.take_profit*100:.1f}%")

print("\n" + "="*80)
print("✅ OSS 학습 및 백테스트 완료!")
print("="*80)
