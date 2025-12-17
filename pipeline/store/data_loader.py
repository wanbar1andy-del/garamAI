
import pandas as pd
from pathlib import Path
import sys

# 프로젝트 루트 자동 설정
current_file = Path(__file__).resolve()
# pipeline/03_store/data_loader.py -> parent.parent.parent = project_root
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

from pipeline._03_store.paths import get_store_paths
from pipeline._03_store.minute_reader import load_validated_minute_csv

# SSOT Paths
_store_paths = get_store_paths(project_root)
DATA_DIR = _store_paths.validated_minute_dir  # Override to validated
UNIVERSE_PATH = project_root / "data/universe_real_400.csv"  # Explicit SSOT

class StoreManager:
    """
    [Step 3: STORE]
    데이터 저장소 접근을 담당하는 공용 클래스.
    모든 하위 단계(Feature, Signal)는 이 클래스를 통해 데이터를 로드해야 한다.
    """
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.universe_path = UNIVERSE_PATH
        self._universe_cache = None

    def get_universe(self):
        """유니버스(수집 대상 종목 리스트) 로드"""
        if self._universe_cache is not None:
            return self._universe_cache
            
        if not self.universe_path.exists():
            raise FileNotFoundError(f"[STORE] Universe file not found: {self.universe_path}")
            
        df = pd.read_csv(self.universe_path, dtype=str)
        
        # SSOT: symbol(6자리)로 통일
        if "symbol" in df.columns:
            df["symbol"] = df["symbol"].astype(str).str.strip().str.zfill(6)
        elif "Code" in df.columns:
            df["symbol"] = df["Code"].astype(str).str.strip().str.zfill(6)
        else:
            raise ValueError(f"[STORE] Universe must contain 'symbol' or 'Code' column: {df.columns.tolist()}")
        
        self._universe_cache = df
        return df

    def get_data(self, symbol, start_date=None, end_date=None):
        """
        특정 종목의 1분봉 데이터 로드
        :param symbol: 종목코드 (예: '005930')
        :param end_date: (Optional) 종료 날짜 (YYYY-MM-DD)
        :return: DataFrame (date, open, high, low, close, volume)
        """
        try:
            # [SSOT V2] Use Validated Reader
            df = load_validated_minute_csv(symbol, self.data_dir)
            
            # Legacy Compatibility: Convert date string to datetime for filtering
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S', errors='coerce')
            
            # 필터링
            if start_date:
                df = df[df['date'] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df['date'] <= pd.to_datetime(end_date)]
                
            return df
            
        except FileNotFoundError:
            print(f"[STORE-WARN] Validated data not found for {symbol}")
            return pd.DataFrame()
        except Exception as e:
            print(f"[STORE-ERROR] Failed to load {symbol}: {e}")
            return pd.DataFrame()

# Singleton Instance (편의용)
store = StoreManager()

if __name__ == "__main__":
    # 간단 테스트
    print("=== StoreManager Test ===")
    
    # 1. 유니버스 로드
    try:
        univ = store.get_universe()
        print(f"Universe Loaded: {len(univ)} symbols")
        sample_symbol = univ['symbol'].iloc[0]
        print(f"Sample Symbol: {sample_symbol}")
        
        # 2. 데이터 로드
        print(f"Loading data for {sample_symbol}...")
        df = store.get_data(sample_symbol)
        print(f"Data Loaded: {len(df)} rows")
        if not df.empty:
            print(df.head(2))
            print(df.tail(2))
            
    except Exception as e:
        print(f"Test Failed: {e}")
