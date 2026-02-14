
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, Optional

class ShortSqueezeHunter:
    """
    [Short Squeeze Hunter Module]
    가람 특수 전략 오퍼레이터: 숏 스퀴즈 포착 및 신호 생성
    
    Logic:
    1. Short Ratio (공매도 비중) 확인 (상위 5% or 절대 비중 > Threshold)
    2. Price Trigger: 공매도 세력 평균단가보다 3% 이상 상승 (3% Buffer Rule)
    3. Volume Accel: 거래량 폭발 (평소 대비 1.5배 이상)
    """
    
    def __init__(self):
        self.name = "ShortSqueezeHunter"
        # Parameters
        self.min_short_ratio = 5.0      # 공매도 거래비중 5% 이상 (일별) or 잔고비중
        self.price_buffer = 1.03        # 공매도 평단가 대비 3% 여유
        self.vol_mult = 1.5             # 거래량 급증 기준
        self.hero_score_boost = 15      # 가중치 부여
        self.target_weight = 0.50       # 공격적 비중 (50%)

    def analyze(self, 
                current_price: float, 
                current_vol: float,
                avg_vol: float,
                short_avg_price: float, 
                short_ratio: float,
                days_to_cover: float = 0.0) -> Dict[str, any]:
        
        """
        실시간(또는 1분봉) 데이터와 일별 공매도 데이터를 결합하여 신호 생성
        """
        
        # 1. 공매도 과열 상태인가?
        is_short_heavy = short_ratio >= self.min_short_ratio
        
        # 2. 고무줄 효과 (압축) -> 폭발 (Price Trigger)
        # 공매도 세력이 손실 구간으로 진입했는가? (평단가 돌파)
        is_breakout = current_price >= (short_avg_price * self.price_buffer)
        
        # 3. 에너지 폭발 (Volume Acceleration)
        is_vol_spike = current_vol >= (avg_vol * self.vol_mult)
        
        sig_type = "NONE"
        score = 0
        
        if is_short_heavy and is_breakout and is_vol_spike:
            sig_type = "SQUEEZE_EXPLOSION"
            score = self.hero_score_boost
            
        return {
            "module": self.name,
            "signal": sig_type,
            "score_boost": score,
            "target_weight": self.target_weight if score > 0 else 0.0,
            "details": {
                "short_heavy": is_short_heavy,
                "breakout": is_breakout,
                "vol_spike": is_vol_spike,
                "p_gap": (current_price / short_avg_price) - 1.0
            }
        }

    def simulate_hlb_scenario(self):
        """
        HLB 1월 시나리오 시뮬레이션 (Mock Data Verification)
        가정: 공매도 잔고 많음, 박스권 돌파 시점
        """
        # Mock Data: HLB 1월 중순 상황 가정
        mock_data = {
            "date": "2025-01-15",
            "price": 52000,
            "short_avg_price": 49500, # 공매도 평단
            "short_ratio": 8.5,       # 공매도 비중 높음
            "vol_5d_avg": 500000,
            "curr_vol": 1200000       # 거래량 터짐
        }
        
        result = self.analyze(
            current_price=mock_data['price'],
            current_vol=mock_data['curr_vol'],
            avg_vol=mock_data['vol_5d_avg'],
            short_avg_price=mock_data['short_avg_price'],
            short_ratio=mock_data['short_ratio']
        )
        
        return result
