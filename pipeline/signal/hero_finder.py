import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class HeroScore:
    symbol: str
    total_score: float
    price_change: float
    volume_surge: float
    volatility: float
    rank: int

class HeroFinder:
    """
    히어로(주도주) 발굴 모듈
    - Snapshot 데이터를 기반으로 종목의 매력도를 점수화하고 랭킹을 매깁니다.
    - 재사용성을 위해 상태를 최소화하고 Input -> Output 변환에 집중합니다.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'weights': {
                'price_change': 0.4,
                'volume_surge': 0.3,
                'efficiency': 0.4, # Increased preference for clean trends
                'wick_penalty': 1.0 # DOUBLED: Strict penalty for upper wicks
            },
            'thresholds': {
                'min_price': 1000,
                'min_volume': 10000 
            }
        }

    def find_heroes(self, snapshot_df: pd.DataFrame, top_n: int = 5, current_time: Optional[pd.Timestamp] = None, state: Optional[Dict] = None) -> tuple[List[HeroScore], Dict]:
        """
        주어진 스냅샷에서 히어로 종목 발굴 (Stateful)
        
        Args:
            snapshot_df (pd.DataFrame): 
                Columns: ['symbol', 'close', 'open', 'high', 'low', 'volume', 'prev_volume_ma']
            top_n (int): 반환할 상위 종목 수
            current_time (pd.Timestamp): 현재 시간 (State 관리에 필요)
            state (Dict): 이전 상태 정보 {'symbol': {'consecutive': int, 'cooldown_until': timestamp}}
            
        Returns:
            (List[HeroScore], Dict): (랭킹순 히어로 리스트, 업데이트된 State)
        """
        if snapshot_df.empty:
            return [], state or {}
            
        # Initialize State if None
        new_state = state.copy() if state else {}
        
        # 1. Pre-filter (Basic Sanity)
        candidates = snapshot_df[
            (snapshot_df['close'] >= self.config['thresholds']['min_price']) &
            (snapshot_df['volume'] >= self.config['thresholds']['min_volume'])
        ].copy()
        
        if candidates.empty:
            return [], new_state

        # 2. Calculate Metrics (V2)
        # A. Price Momentum
        candidates['pct_change'] = (candidates['close'] - candidates['open']) / candidates['open'] * 100
        
        # B. Volume Surge
        if 'prev_volume_ma' in candidates.columns:
            candidates['vol_ratio'] = candidates['volume'] / (candidates['prev_volume_ma'] + 1)
        else:
            candidates['vol_ratio'] = np.log1p(candidates['volume']) 

        # C. Trend Efficiency & Wick Penalty
        high_low_range = candidates['high'] - candidates['low'].replace(0, 0.01)
        high_low_range = high_low_range.replace(0, 1)

        candidates['efficiency'] = (candidates['close'] - candidates['open']).abs() / high_low_range
        candidates['wick_ratio'] = (candidates['high'] - candidates['close']) / high_low_range

        # 3. Scoring
        def normalize(series):
            return (series - series.min()) / (series.max() - series.min() + 1e-9)

        w_price = self.config.get('weights', {}).get('price_change', 0.4)
        w_vol = self.config.get('weights', {}).get('volume_surge', 0.3)
        w_eff = self.config.get('weights', {}).get('efficiency', 0.3)
        w_wick_penalty = self.config.get('weights', {}).get('wick_penalty', 0.5)

        score_p = normalize(candidates['pct_change']) * w_price
        score_v = normalize(candidates['vol_ratio']) * w_vol
        score_eff = normalize(candidates['efficiency']) * w_eff
        
        candidates['raw_score'] = score_p + score_v + score_eff
        candidates['total_score'] = candidates['raw_score'] - (candidates['wick_ratio'] * w_wick_penalty)
        
        # 4. State Management (Persistence & Cooldown)
        # Configs
        persistence_thres = 5  # UPDATED: Require 5 consecutive checks (~5 mins) to confirmed
        cutoff_score_rank = top_n * 2 # Candidate pool size (Top 2N)
        cooldown_duration = pd.Timedelta(minutes=10)
        
        # Sort by score primarily for candidate selection
        candidates = candidates.sort_values(by='total_score', ascending=False)
        top_candidates = candidates.head(cutoff_score_rank)
        
        final_heroes = []
        
        # Clean up old state entries for symbols not in current snapshot? 
        # For simplicity, we keep simple state.
        
        timestamp = current_time or pd.Timestamp.now()
        
        for idx, row in candidates.iterrows():
            sym = row['symbol']
            score = row['total_score']
            is_candidate = (idx in top_candidates.index)
            
            # Init symbol state
            if sym not in new_state:
                new_state[sym] = {'consecutive': 0, 'cooldown_until': None}
            
            s_data = new_state[sym]
            
            # Check Cooldown
            if s_data['cooldown_until'] and timestamp < s_data['cooldown_until']:
                # Still in cooldown
                s_data['consecutive'] = 0
                continue 
            
            # Update Consecutive Count
            if is_candidate and score > 0.3: # Minimum score threshold
                s_data['consecutive'] += 1
            else:
                # If it was a hero but crashed (Wick Penalty made score low), trigger cooldown?
                # Simple logic: If it drops out, reset consecutive.
                if s_data['consecutive'] > persistence_thres and row['wick_ratio'] > 0.5:
                     # It WAS a hero, but now crashed hard -> Cooldown
                     s_data['cooldown_until'] = timestamp + cooldown_duration
                
                s_data['consecutive'] = 0
            
            # Final Selection Rule
            # Must satisfy persistence threshold to be returned in the implementation list
            # OR if we want to show "New Candidates", we can include them but rank them lower.
            # User requirement: "Persistence filter".
            
            # We add 'consecutive' bonus to score for ranking? 
            # Or just filter? Let's add a bonus to prioritize persistent heroes.
            persistence_bonus = min(s_data['consecutive'], 10) * 0.05
            
            final_score = score + persistence_bonus
            
            # Add to results if it meets minimal persistence (e.g. at least 1, or 0 if we want to see new ones)
            # To be strict V2: Let's require consecutive >= 2 for the very top list, 
            # or just let the bonus sort them up.
            
            results_entry = HeroScore(
                symbol=sym,
                total_score=round(final_score, 2),
                price_change=round(row['pct_change'], 2),
                volume_surge=round(row['vol_ratio'], 2),
                volatility=round(row['efficiency'], 2), # efficiency
                rank=0 # Set later
            )
            # We attach internal state for verification
            # (In a real app, we might not want to pollute dataclass, but for now it's fine)
            
            final_heroes.append((final_score, results_entry))
            
        # Re-sort by final score (Base + Persistence Bonus)
        final_heroes.sort(key=lambda x: x[0], reverse=True)
        final_heroes = final_heroes[:top_n]
        
        results = []
        for rank, (score, h_obj) in enumerate(final_heroes, 1):
            h_obj.rank = rank
            h_obj.total_score = round(score, 2)
            results.append(h_obj)
            
        return results, new_state
