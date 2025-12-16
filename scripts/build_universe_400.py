# scripts/build_universe_400.py
"""
Phase 21: 유니버스 생성 스크립트
전일 기준 거래대금/변동률 상위 400 종목 선정

TODO: 프로젝트 데이터 소스에 맞춰 구현 필요
현재는 스켈레톤 (구조만 제공)
"""
import sys
import argparse
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).resolve().parents[1]))

# from garam_core.data.loader import load_ohlcv, LoadSpec
# from garam_core.health.gate import gate_environment


def build_universe_from_turnover(method: str, top_n: int, date: str = None) -> pd.DataFrame:
    """
    거래대금/변동률 기준 상위 N개 종목 선정
    
    Args:
        method: 'turnover' (거래대금), 'volatility' (변동률), 'volume' (거래량)
        top_n: 상위 N개
        date: 기준일 (YYYYMMDD, None이면 전일)
    
    Returns:
        DataFrame with columns: symbol, rank, value (거래대금/변동률 etc)
    
    TODO: 실제 구현
    - KRX 전체 종목 일봉 데이터 로드
    - 전일 거래대금/변동률 계산
    - 정렬 및 상위 N개 추출
    """
    
    # 스켈레톤 (실제 데이터 소스 연결 필요)
    print(f"[유니버스 생성] 방식: {method} | 상위: {top_n}개")
    print(f"[경고] 현재는 더미 유니버스 생성 중 (실제 구현 필요)")
    
    # 더미 데이터 (TOP 10만 예시)
    # 실제로는 KRX 전체 종목 스캔 필요
    dummy_symbols = [
        "005930", "000660", "373220", "207940", "005380",
        "000270", "005490", "035420", "006400", "051910"
    ]
    
    # top_n만큼 복제 (더미)
    symbols = (dummy_symbols * (top_n // len(dummy_symbols) + 1))[:top_n]
    
    df = pd.DataFrame({
        "symbol": symbols,
        "rank": range(1, top_n + 1),
        "value": [100000 - i*1000 for i in range(top_n)]  # 더미 거래대금
    })
    
    return df


def main():
    parser = argparse.ArgumentParser(description="Phase 21: 유니버스 생성")
    parser.add_argument("--method", type=str, choices=["turnover", "volatility", "volume"], 
                        default="turnover",
                        help="선정 기준 (turnover=거래대금, volatility=변동률, volume=거래량)")
    parser.add_argument("--top_n", type=int, default=400,
                        help="상위 N개")
    parser.add_argument("--date", type=str, default=None,
                        help="기준일 (YYYYMMDD, None=전일)")
    parser.add_argument("--out", type=str, default="data/universe_400.csv",
                        help="출력 파일 경로")
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"  유니버스 생성: {args.method.upper()} 상위 {args.top_n}개")
    print(f"{'='*60}\n")
    
    # 유니버스 생성
    df_universe = build_universe_from_turnover(args.method, args.top_n, args.date)
    
    # 저장
    out_path = Path(args.out)
    out_path.parent.mkdir(exist_ok=True, parents=True)
    
    # 히어로 스캐너용으로는 symbol 컬럼만 필요
    df_universe[["symbol"]].to_csv(out_path, index=False)
    
    print(f"[출력] 유니버스 저장: {out_path}")
    print(f"[완료] {len(df_universe)}개 종목 선정\n")
    print(df_universe.head(20))


if __name__ == "__main__":
    main()
