
import pandas as pd
from pathlib import Path
import sys

# 프로젝트 루트 자동 설정
current_file = Path(__file__).resolve()
# pipeline/03_store/data_loader.py -> parent.parent.parent = project_root
project_root = current_file.parent.parent.parent

# 데이터 경로 상수
DATA_DIR = project_root / "garamdata/history/minute"
UNIVERSE_PATH = project_root / "GARAM_Data/real_universe_400.csv"

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
            
        df = pd.read_csv(self.universe_path)
        # 종목코드 6자리 포맷팅
        if 'Code' in df.columns:
            df['Code'] = df['Code'].astype(str).str.zfill(6)
        
        self._universe_cache = df
        return df

    def get_data(self, symbol, start_date=None, end_date=None):
        """
        특정 종목의 1분봉 데이터 로드
        :param symbol: 종목코드 (예: '005930')
        :param start_date: (Optional) 시작 날짜 (YYYY-MM-DD)
        :param end_date: (Optional) 종료 날짜 (YYYY-MM-DD)
        :return: DataFrame (date, open, high, low, close, volume)
        """
        csv_path = self.data_dir / f"{symbol}_1m.csv"
        
        if not csv_path.exists():
            print(f"[STORE-WARN] Data not found for {symbol}")
            return pd.DataFrame()
            
        try:
            # CSV 읽기 (중복 컬럼 자동 처리: .1, .2 등)
            df = pd.read_csv(csv_path)
            
            # [DEBUG]
            # print(f"DEBUG: Initial Columns: {df.columns.tolist()}")
            
            # 컬럼 이름의 공백 제거
            df.columns = df.columns.str.strip()

            # Robust Mapping Strategy (Coalesce)
            # 영문 컬럼과 한글 컬럼이 혼재된 경우, 데이터를 병합(Coalesce)하여 복구 시도
            # 예: 'date'가 NaN이고 '체결시간'에 값이 있으면 '체결시간' 값 사용
            
            mapping = {
                'date': ['date', '체결시간'],
                'open': ['open', '시가'],
                'high': ['high', '고가'],
                'low': ['low', '저가'],
                'close': ['close', '현재가', '종가'],
                'volume': ['volume', '거래량']
            }
            
            for target_col, candidates in mapping.items():
                # 후보 컬럼 중 DataFrame에 존재하는 것들 찾기
                existing_candidates = [c for c in candidates if c in df.columns]
                
                if not existing_candidates:
                    print(f"[STORE-WARN] No candidates for {target_col} in {symbol}")
                    continue
                    
                # 첫 번째 후보를 기준으로 시작, 나머지 후보들의 값으로 결측치 채우기 (Coalesce)
                # s = df[existing_candidates[0]]
                # for candidate in existing_candidates[1:]:
                #     s = s.combine_first(df[candidate])
                
                # 위 방식보다 더 명시적으로:
                # 존재하는 모든 후보 컬럼의 데이터를 하나로 합침 (우선순위: 앞쪽 후보)
                combined_series = df[existing_candidates[0]].copy()
                for candidate in existing_candidates[1:]:
                    combined_series = combined_series.fillna(df[candidate])
                
                df[target_col] = combined_series

            # 필요한 표준 컬럼만 선택
            final_cols = list(mapping.keys())
            if not all(col in df.columns for col in final_cols):
                 # 복구 실패 시
                 print(f"[STORE-WARN] Failed to recover required columns for {symbol}")
                 return pd.DataFrame()

            df = df[final_cols]
            
            # 날짜 파싱 (속도를 위해 fastpath 사용 가능하지만 일단 안전하게)
            # 다양한 포맷 대응: YYYYMMDDHHMMSS, YYYY-MM-DD ...
            # errors='coerce'로 파싱 불가능한 가비지 데이터(헤더 반복 등)를 NaT로 변환 후 제거
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S', errors='coerce')
            df.dropna(subset=['date'], inplace=True)
            
            # 데이터 타입 변환 (숫자형)
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df.dropna(subset=numeric_cols, inplace=True) # 숫자 변환 실패 행 제거
            
            # [Fix] 키움 데이터의 음수 가격(하락)을 양수로 변환
            price_cols = ['open', 'high', 'low', 'close']
            for col in price_cols:
                df[col] = df[col].abs()
            
            # 필터링
            if start_date:
                df = df[df['date'] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df['date'] <= pd.to_datetime(end_date)]
                
            # 정렬 (오름차순: 과거 -> 현재)
            df.sort_values('date', ascending=True, inplace=True)
            df.reset_index(drop=True, inplace=True)
            
            return df
            
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
        sample_symbol = univ['Code'].iloc[0]
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
