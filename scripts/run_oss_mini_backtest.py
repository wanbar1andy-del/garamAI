"""
OSS Brain Mini-Backtest Runner
- 8192-Node Brain 실전 성능 검증
- 31bp 거래 비용 적용
- 마지막 1개월 데이터 (Validation Period) 대상
"""
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Setup Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from garam_core.backtest.engine_unified import run_backtest_unified
from garam_core.strategy.oss_brain_strategy import OSSBrainStrategy

def run_mini_backtest():
    print("=" * 70)
    print("🚀 Garam OSS Mini-Backtest: Harmony & Efficiency Check")
    print("=" * 70)
    
    # 1. 데이터 로드
    cache_path = PROJECT_ROOT / "cache" / "market_matrix_8m.pkl"
    print(f"🔄 데이터 로딩: {cache_path}")
    cached = pd.read_pickle(cache_path)
    closes = cached['closes']
    volumes = cached['volumes']
    
    # 백테스트 대상 심볼 선택 (대표 심볼 005930 또는 데이터가 가장 많은 것)
    # 여기서는 Samsung Electronics (005930) 또는 첫 번째 심볼 사용
    symbol = "005930" if "005930" in closes.columns else closes.columns[0]
    print(f"📊 대상 심볼: {symbol}")
    
    df = pd.DataFrame({
        'close': closes[symbol],
        'volume': volumes[symbol]
    }).dropna()
    
    # 마지막 1개월(약 20,000분 봉) 데이터로 제한
    # 8개월 데이터 중 마지막 12.5%가 약 1개월
    test_size = int(len(df) * 0.125)
    df_test = df.tail(test_size).copy()
    print(f"🗓️ 테스트 기간: {len(df_test)} bars (약 1개월)")
    
    # 2. 전략 초기화
    # Threshold 0.1% (디버깅을 위한 하향 조정)
    strategy = OSSBrainStrategy(threshold=0.001)
    
    # 3. 백테스트 구동
    print(f"🔥 백테스트 시작 (비용: 31bp)...")
    results = run_backtest_unified(strategy, df_test, cost_per_trade=0.0031)
    
    # 3.5 예측값 통계 확인 (디버깅)
    signals = results['signals']
    print(f"📈 신호 발생: {signals.sum()} bars (전체 {len(signals)} 중 {signals.mean():.2%})")
    
    # 4. 결과 출력
    print("\n" + "=" * 50)
    print("          BACKTEST RESULT           ")
    print("=" * 50)
    print(f"심볼         : {symbol}")
    print(f"총 수익률    : {results['roi']:.2%}")
    print(f"MDD         : {results['max_drawdown']:.2%}")
    print(f"거래 횟수    : {results['trades']}")
    print(f"승률         : {results['win_rate']:.1%}")
    print(f"Profit Factor: {results['profit_factor']:.2f}")
    print(f"총 지불 비용 : {results['cost_paid_total']:.4f}")
    print("=" * 50)
    
    # 6. Markdown Report 저장
    report_path = PROJECT_ROOT / "reports/oss_backtest_harmony_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Garam OSS Mini-Backtest Harmony Report\n\n")
        f.write(f"- **대상 심볼**: {symbol}\n")
        f.write(f"- **총 수익률**: {results['roi']:.2%}\n")
        f.write(f"- **MDD**: {results['max_drawdown']:.2%}\n")
        f.write(f"- **거래 횟수**: {results['trades']}\n")
        f.write(f"- **승률**: {results['win_rate']:.1%}\n")
        f.write(f"- **Profit Factor**: {results['profit_factor']:.2f}\n")
        f.write(f"- **총 지불 비용**: {results['cost_paid_total']:.4f}\n\n")
        f.write(f"![Harmony Chart](backtest_harmony_result.png)\n")
    print(f"✅ 리포트 저장 완료: {report_path}")
    
    return results

if __name__ == "__main__":
    try:
        run_mini_backtest()
    except Exception as e:
        print(f"❌ 백테스트 중단: {e}")
        import traceback
        traceback.print_exc()
