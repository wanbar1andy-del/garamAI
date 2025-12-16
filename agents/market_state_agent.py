"""
Market State Agent (Rule-Based Classifier)
Analyzes market conditions and classifies current regime
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

# Import centralized paths
try:
    from garam.config import PATHS
    DEFAULT_BASE_PATH = PATHS.BASE_DIR
except ImportError:
    DEFAULT_BASE_PATH = Path("C:/garam")

logger = logging.getLogger(__name__)


class MarketStateAgent:
    """
    시장 상태 판정 에이전트 v0.1
    
    룰 기반 분류기로 시작.
    나중에 GPT-OSS 보조 판단 추가 가능.
    """
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else DEFAULT_BASE_PATH
        # self.market_state_file = self.base_path / "AgentKit" / "market_state.json"
        
        # [MODIFIED] Store state in GARAM_Data/system to avoid AgentKit dependency
        try:
            from garam.config import PATHS
            self.market_state_file = PATHS.HEALTH_DIR / "market_state.json"
        except:
            self.market_state_file = self.base_path / "GARAM_Data" / "system" / "market_state.json"
        
        logger.info(f"MarketStateAgent initialized: {self.market_state_file}")
    
    def analyze_market_state(
        self,
        current_price: float,
        ohlcv_1m: pd.DataFrame,
        ohlcv_5m: Optional[pd.DataFrame] = None,
        volume_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        시장 데이터를 분석하여 market_state 생성
        
        Args:
            current_price: 현재가
            ohlcv_1m: 1분봉 데이터 (최소 30개 이상)
            ohlcv_5m: 5분봉 데이터 (선택)
            volume_data: 거래량 데이터 (선택)
        
        Returns:
            market_state 딕셔너리
        """
        # 1. 추세 분류
        trend = self._classify_trend(ohlcv_1m, current_price)
        
        # 2. 변동성 분류
        volatility = self._classify_volatility(ohlcv_1m)
        
        # 3. 레인지 체제 분류
        range_regime = self._classify_range_regime(ohlcv_1m)
        
        # 4. 급락 위험 평가
        crash_risk = self._assess_crash_risk(ohlcv_1m)
        
        # 5. AI 발자국 (Phase 3에서 구현, 현재는 더미)
        ai_footprint = "NONE"
        
        # 6. 뉴스 공포 점수 (Phase 3에서 구현, 현재는 더미)
        news_fear_score = 25
        news_event_type = "NONE"
        
        # 7. 신뢰도 계산
        confidence = self._calculate_confidence(ohlcv_1m, trend, volatility)
        
        market_state = {
            "timestamp": datetime.now().isoformat(),
            "trend": trend,
            "volatility": volatility,
            "range_regime": range_regime,
            "crash_risk": crash_risk,
            "ai_footprint": ai_footprint,
            "news_fear_score": news_fear_score,
            "news_event_type": news_event_type,
            "confidence": round(confidence, 2)
        }
        
        return market_state
    
    def _classify_trend(self, ohlcv: pd.DataFrame, current_price: float) -> str:
        """
        추세 분류
        
        Args:
            ohlcv: OHLCV 데이터
            current_price: 현재가
        
        Returns:
            "UP", "DOWN", "SIDEWAYS", "CRASH", "SPIKE"
        """
        if len(ohlcv) < 30:
            return "SIDEWAYS"
        
        # 30분 수익률
        price_30m_ago = ohlcv.iloc[-30]['close']
        ret_30m = (current_price - price_30m_ago) / price_30m_ago * 100
        
        # 5분 수익률
        price_5m_ago = ohlcv.iloc[-5]['close']
        ret_5m = (current_price - price_5m_ago) / price_5m_ago * 100
        
        # 급락/급등 감지
        if ret_5m < -1.5:  # 5분에 -1.5% 이상 하락
            return "CRASH"
        if ret_5m > 1.5:   # 5분에 +1.5% 이상 상승
            return "SPIKE"
        
        # 일반 추세
        if ret_30m > 0.5 and ret_5m > 0.2:
            return "UP"
        if ret_30m < -0.5 and ret_5m < -0.2:
            return "DOWN"
        
        return "SIDEWAYS"
    
    def _classify_volatility(self, ohlcv: pd.DataFrame) -> str:
        """
        변동성 분류
        
        Args:
            ohlcv: OHLCV 데이터
        
        Returns:
            "LOW", "NORMAL", "HIGH", "EXTREME"
        """
        if len(ohlcv) < 30:
            return "NORMAL"
        
        # 최근 30분 고-저 범위 (bp 단위)
        recent_30 = ohlcv.iloc[-30:]
        high_30 = recent_30['high'].max()
        low_30 = recent_30['low'].min()
        mid_30 = (high_30 + low_30) / 2
        
        range_30m_bps = ((high_30 - low_30) / mid_30) * 10000
        
        # 분류
        if range_30m_bps < 50:
            return "LOW"
        if range_30m_bps < 150:
            return "NORMAL"
        if range_30m_bps < 300:
            return "HIGH"
        
        return "EXTREME"
    
    def _classify_range_regime(self, ohlcv: pd.DataFrame) -> str:
        """
        레인지 체제 분류
        
        Args:
            ohlcv: OHLCV 데이터
        
        Returns:
            "BOX", "BREAKOUT", "MEAN_REVERT"
        """
        if len(ohlcv) < 30:
            return "BOX"
        
        recent_30 = ohlcv.iloc[-30:]
        
        # 고가/저가 범위
        high_30 = recent_30['high'].max()
        low_30 = recent_30['low'].min()
        current_close = ohlcv.iloc[-1]['close']
        
        # 현재가가 범위의 어디에 있는지
        position = (current_close - low_30) / (high_30 - low_30) if high_30 > low_30 else 0.5
        
        # 브레이크아웃 감지 (최근 5분)
        recent_5 = ohlcv.iloc[-5:]
        ret_5m = (recent_5.iloc[-1]['close'] - recent_5.iloc[0]['close']) / recent_5.iloc[0]['close']
        
        if abs(ret_5m) > 0.005 and (position > 0.8 or position < 0.2):
            return "BREAKOUT"
        
        # 평균 회귀 패턴 (중앙으로 수렴)
        if 0.4 < position < 0.6:
            return "MEAN_REVERT"
        
        return "BOX"
    
    def _assess_crash_risk(self, ohlcv: pd.DataFrame) -> str:
        """
        급락 위험 평가
        
        Args:
            ohlcv: OHLCV 데이터
        
        Returns:
            "LOW", "MEDIUM", "HIGH"
        """
        if len(ohlcv) < 10:
            return "LOW"
        
        recent_10 = ohlcv.iloc[-10:]
        
        # 최근 10분 최대 낙폭
        max_drop = 0
        for i in range(1, len(recent_10)):
            drop = (recent_10.iloc[i]['close'] - recent_10.iloc[i-1]['close']) / recent_10.iloc[i-1]['close']
            if drop < max_drop:
                max_drop = drop
        
        # 분류
        if max_drop < -0.01:  # -1% 이상 순간 낙폭
            return "HIGH"
        if max_drop < -0.005:  # -0.5% 이상
            return "MEDIUM"
        
        return "LOW"
    
    def _calculate_confidence(
        self,
        ohlcv: pd.DataFrame,
        trend: str,
        volatility: str
    ) -> float:
        """
        판정 신뢰도 계산
        
        Args:
            ohlcv: OHLCV 데이터
            trend: 추세
            volatility: 변동성
        
        Returns:
            신뢰도 (0.0 ~ 1.0)
        """
        confidence = 0.7  # 기본값
        
        # 데이터 충분성
        if len(ohlcv) >= 30:
            confidence += 0.1
        
        # 명확한 추세
        if trend in ["UP", "DOWN"]:
            confidence += 0.1
        
        # 극단 변동성은 신뢰도 감소
        if volatility == "EXTREME":
            confidence -= 0.2
        
        # 급락/급등은 신뢰도 감소
        if trend in ["CRASH", "SPIKE"]:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def update_market_state_file(self, market_state: Dict[str, Any]):
        """
        market_state.json 파일 업데이트
        
        Args:
            market_state: 시장 상태 딕셔너리
        """
        try:
            self.market_state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.market_state_file, 'w', encoding='utf-8') as f:
                json.dump(market_state, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ market_state.json updated: {market_state['trend']}/{market_state['volatility']}")
        
        except Exception as e:
            logger.error(f"Failed to update market_state.json: {e}")
    
    def run_once(self, current_price: float, ohlcv_1m: pd.DataFrame):
        """
        1회 실행 (테스트/수동 실행용)
        
        Args:
            current_price: 현재가
            ohlcv_1m: 1분봉 데이터
        """
        market_state = self.analyze_market_state(current_price, ohlcv_1m)
        self.update_market_state_file(market_state)
        return market_state


# 사용 예시
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 더미 데이터로 테스트
    dummy_ohlcv = pd.DataFrame({
        'open': [100] * 40,
        'high': [101] * 40,
        'low': [99] * 40,
        'close': [100 + i * 0.1 for i in range(40)],  # 상승 추세
        'volume': [1000] * 40
    })
    
    agent = MarketStateAgent()
    market_state = agent.run_once(current_price=104.0, ohlcv_1m=dummy_ohlcv)
    
    print("Market State:")
    print(json.dumps(market_state, indent=2, ensure_ascii=False))
