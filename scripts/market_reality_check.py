"""
Market Reality Check: Actual vs Predicted
- 8192-Node Brain이 예측한 -15% 하락이 실제 시장과 일치하는지 검증
"""
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def check_reality():
    cache_path = PROJECT_ROOT / "cache" / "market_matrix_8m.pkl"
    print(f"🔄 Loading data: {cache_path}")
    cached = pd.read_pickle(cache_path)
    closes = cached['closes']
    
    symbol = "005930" # Samsung Electronics
    data = closes[symbol].dropna()
    
    # 마지막 10% (백테스트 구간)
    test_size = int(len(data) * 0.1)
    test_data = data.tail(test_size)
    
    start_price = test_data.iloc[0]
    end_price = test_data.iloc[-1]
    max_price = test_data.max()
    min_price = test_data.min()
    
    total_ret = (end_price / start_price - 1) * 100
    max_drawdown = (min_price / start_price - 1) * 100
    max_runup = (max_price / start_price - 1) * 100
    
    print(f"\n📊 [Reality Check] {symbol} (Last 10% Period)")
    print(f"   - Start Price: {start_price:,.0f}")
    print(f"   - End Price:   {end_price:,.0f}")
    print(f"   - Actual Return: {total_ret:+.2f}%")
    print(f"   - Period Max Return: {max_runup:+.2f}%")
    print(f"   - Period Max Drawdown: {max_drawdown:+.2f}%")
    
    if total_ret < -5:
        print("\n✅ 시장이 실제로 좋지 않았습니다. 모델의 하락 예측(-15%)은 방향성 측면에서 '정답'이었습니다.")
    elif total_ret > 5:
        print("\n❌ 시장은 상승했습니다. 모델의 하락 예측은 오답(Hallucination)입니다.")
    else:
        print("\n⚠️ 시장은 횡보했습니다. 모델의 과도한 하락 예측은 비관론적 편향(Bearish Bias)일 수 있습니다.")

if __name__ == "__main__":
    check_reality()
