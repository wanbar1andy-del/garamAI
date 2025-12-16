
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """
    모든 전략의 기본 클래스.
    각 전략은 이 클래스를 상속받아 generate_signals를 구현해야 함.
    """
    def __init__(self, name):
        self.name = name
        
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        입력: feature가 계산된 DataFrame
        출력: 'signal' 컬럼이 추가된 DataFrame (1: Buy, -1: Sell, 0: Hold/Neutral)
        """
        pass

class TurboStrategy(BaseStrategy):
    """
    [Turbo Exit Strategy]
    - 기본: 매수 유지
    - 매도 조건: 일일 수익률 < -Threshold (손절/회피)
    - 재진입 조건: 3일 후 + 낙폭의 50% 회복 시
    """
    def __init__(self, exit_threshold=0.03):
        super().__init__("TurboStrategy")
        self.exit_threshold = exit_threshold
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        [Turbo Signal Logic]
        1. Calculate Daily Return (intraday)
        2. Signal = -2 (Panic Sell) if Daily Return <= -Threshold
        3. Signal = 1 (Buy) if Normal Condition (simplified)
        """
        df = df.copy()
        
        # 1. 일일 수익률 계산 (약식: 현재가 / 당일 시가 - 1)
        # 당일 시가를 구하기 위해 'date' 컬럼을 활용
        # (주의: 실제로는 09:00 데이터가 필요하지만, 여기서는 첫 번째 봉을 시가로 가정하거나
        #  Grouper를 사용해야 함. 성능을 위해 'open' 컬럼 사용하되,
        #  정확한 'Day Open'을 위해서는 별도 로직 필요.)
        
        # 간단한 구현: shift 하지 않고 현재 봉의 open 대비 close 등락률 (1분 수익률 아님!)
        # 정확한 구현: df.groupby(df['date'].dt.date)['open'].transform('first')
        
        df['day_open'] = df.groupby(df['date'].dt.date)['open'].transform('first')
        df['daily_return'] = (df['close'] - df['day_open']) / df['day_open']
        
        # 2. 신호 생성
        # 기본: 0 (Hold)
        # 매수: 시가 대비 상승이면 매수 (단순화) -> 실제로는 별도 Alpha 필요
        df['signal'] = 0
        
        # Turbo Exit (Panic Sell: -2)
        df.loc[df['daily_return'] <= -self.exit_threshold, 'signal'] = -2
        
        return df
