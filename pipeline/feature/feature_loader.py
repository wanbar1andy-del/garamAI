
import pandas as pd
from pathlib import Path
import sys

# 프로젝트 루트 경로 설정 (pipeline/04_feature/feature_loader.py -> c:\garam\garam)
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from pipeline.store.data_loader import store
from pipeline.feature.factory import FeatureFactory
from pipeline.monitor.log_manager import LogManager

logger = LogManager.get_logger("FeatureLoader")

class FeatureLoader:
    """
    [Step 4: FEATURE]
    데이터 로드(Store)와 지표 계산(Factory)을 연결하는 Facade 클래스.
    """
    
    def __init__(self):
        self.factory = FeatureFactory()
        
    def get_features(self, symbol, start_date=None, end_date=None, 
                     feature_config=None):
        """
        특정 종목의 데이터 로드 + 지표 계산 완료된 DataFrame 반환
        :param symbol: 종목코드
        :param feature_config: 지표 설정 리스트 (None이면 기본값 사용)
        """
        # 1. Load Step (from STORE)
        df = store.get_data(symbol, start_date, end_date)
        
        if df.empty:
            return df
            
        # 2. Compute Step (from FACTORY)
        if feature_config is None:
            # 기본 지표 세트
            feature_config = [
                'ma_trend', 
                'rsi', 
                'bollinger', 
                'atr'
            ]
            
        df_features = self.factory.compute_features(df, feature_config)
        
        # 3. Post-Process (Optional: Drop NaN from lookback periods)
        # df_features.dropna(inplace=True)
        
        return df_features

features = FeatureLoader()

if __name__ == "__main__":
    logger.info("=== FeatureLoader Test ===")
    sample_symbol = "005930"
    
    logger.info(f"Calculating features for {sample_symbol}...")
    df = features.get_features(sample_symbol)
    
    if not df.empty:
        logger.info(f"Result Shape: {df.shape}")
        logger.info(f"Columns: {df.columns.tolist()}")
        logger.info(f"Tail(2):\n{df.tail(2)}")
    else:
        logger.warning("No data found.")
