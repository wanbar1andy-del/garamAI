"""
Robust Minute Data Loader (정렬 자동 보정)

목적: bad_order_asc 문제 해결
- CSV가 오름차순/내림차순 혼재해도 자동 보정
- 항상 "최신 N행" 또는 "특정 기간" 정확히 선택
- 데이터 품질 리포트 자동 생성
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Tuple, Dict


class MinuteDataLoader:
    """분봉 데이터 로더 (정렬/품질 자동 보정)"""
    
    def __init__(self, minute_dir: Path):
        self.minute_dir = Path(minute_dir)
        self.quality_stats = []
    
    def load_symbol(
        self,
        symbol: str,
        lookback_days: int = 365,
        tail_rows: int = None,
        validate: bool = True
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        종목 분봉 로드 (자동 정렬 보정)
        
        Returns:
            (df, quality_report)
        """
        csv_path = self.minute_dir / f"{symbol}.csv"
        
        if not csv_path.exists():
            return pd.DataFrame(), {
                "symbol": symbol,
                "status": "file_not_found",
                "error": str(csv_path)
            }
        
        try:
            # Load raw
            df = pd.read_csv(csv_path, dtype={"date": "string"})
            
            # Normalize columns
            df = self._normalize_columns(df)
            
            if "date" not in df.columns or "close" not in df.columns:
                return pd.DataFrame(), {
                    "symbol": symbol,
                    "status": "missing_columns",
                    "columns": list(df.columns)
                }
            
            # Parse date
            df["date"] = df["date"].astype(str).str.zfill(14)
            df["dt"] = pd.to_datetime(df["date"], format="%Y%m%d%H%M%S", errors="coerce")
            df = df.dropna(subset=["dt"])
            
            if df.empty:
                return pd.DataFrame(), {
                    "symbol": symbol,
                    "status": "empty_after_parse"
                }
            
            # Detect sort order
            is_descending = df["dt"].iloc[0] > df["dt"].iloc[-1]
            
            # Force sort to ascending (oldest first)
            df = df.sort_values("dt").reset_index(drop=True)
            
            # Quality check
            quality = self._check_quality(symbol, df, is_descending)
            
            # Filter by lookback
            if lookback_days:
                cutoff = datetime.now() - timedelta(days=lookback_days)
                df = df[df["dt"] >= cutoff]
            
            # Get latest N rows (after sort)
            if tail_rows and len(df) > tail_rows:
                df = df.iloc[-tail_rows:]
            
            # Prepare output
            df = df[["date", "dt", "open", "close", "volume"]].copy()
            df["open"] = pd.to_numeric(df["open"], errors="coerce")
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
            
            # Final validation
            if validate:
                df = df.dropna(subset=["close"])
                df = df[df["close"] > 0]
            
            quality["final_rows"] = len(df)
            quality["status"] = "ok" if len(df) > 0 else "empty_after_filter"
            
            self.quality_stats.append(quality)
            
            return df, quality
            
        except Exception as e:
            return pd.DataFrame(), {
                "symbol": symbol,
                "status": "load_error",
                "error": str(e)
            }
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """컬럼명 표준화"""
        rename_map = {
            "체결시간": "date",
            "현재가": "close",
            "거래량": "volume",
            "timestamp": "date"
        }
        
        for old, new in rename_map.items():
            if old in df.columns and new not in df.columns:
                df = df.rename(columns={old: new})
        
        return df
    
    def _check_quality(self, symbol: str, df: pd.DataFrame, was_descending: bool) -> Dict:
        """데이터 품질 검사"""
        
        # Duplicates
        dup_count = df["dt"].duplicated().sum()
        
        # Gaps (expected: 1 min)
        time_diffs = df["dt"].diff().dt.total_seconds() / 60
        gap_count = (time_diffs > 5).sum()  # 5분 이상 gap
        
        # Latest date
        latest_date = df["dt"].max()
        days_ago = (datetime.now() - latest_date).days
        
        # Coverage (trading days)
        unique_days = df["dt"].dt.date.nunique()
        
        # Invalid close
        invalid_close = (df["close"] <= 0).sum() + df["close"].isna().sum()
        
        return {
            "symbol": symbol,
            "raw_rows": len(df),
            "was_descending": was_descending,
            "duplicates": int(dup_count),
            "gaps_5min": int(gap_count),
            "latest_date": latest_date.strftime("%Y-%m-%d"),
            "days_ago": int(days_ago),
            "unique_days": int(unique_days),
            "invalid_close": int(invalid_close),
            "freshness": "good" if days_ago <= 3 else "stale"
        }
    
    def get_quality_summary(self) -> pd.DataFrame:
        """품질 통계 요약"""
        if not self.quality_stats:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.quality_stats)
        
        print("\n=== DATA QUALITY SUMMARY ===")
        print(f"Total symbols: {len(df)}")
        print(f"OK: {(df['status'] == 'ok').sum()}")
        print(f"Was descending: {df['was_descending'].sum()}")
        print(f"Duplicates total: {df['duplicates'].sum()}")
        print(f"Fresh (<=3 days): {(df['freshness'] == 'good').sum()}")
        print(f"Stale (>3 days): {(df['freshness'] == 'stale').sum()}")
        print("="*30)
        
        return df


def test_loader():
    """테스트"""
    loader = MinuteDataLoader(Path("GARAM_Data/history/minute"))
    
    # Test 10 symbols
    symbols = ["005930", "000660", "035720", "051910", "006400",
               "035420", "000270", "105560", "055550", "096770"]
    
    for sym in symbols:
        df, quality = loader.load_symbol(sym, lookback_days=365, tail_rows=20000)
        print(f"{sym}: {len(df)} rows, status={quality['status']}, "
              f"descending={quality.get('was_descending', 'N/A')}")
    
    # Summary
    summary = loader.get_quality_summary()
    summary.to_csv("results/data_quality_check.csv", index=False)
    print(f"\nSaved: results/data_quality_check.csv")


if __name__ == "__main__":
    test_loader()
