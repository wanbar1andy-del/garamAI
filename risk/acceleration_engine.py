"""
Acceleration Engine for GARAM

Calculates the 'Acceleration Factor' based on 3 core mechanisms:
1. Volatility Compression (Spring Effect)
2. Liquidity Vacuum (Vacuum Effect)
3. Sector Resonance (Resonance Effect)

This factor is used to boost position sizing and aggression for high-conviction setups.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional

logger = logging.getLogger("AccelerationEngine")

class AccelerationEngine:
    def __init__(self):
        pass

    def calculate_acceleration(self, symbol: str, data: pd.DataFrame, 
                             sector_data: Optional[Dict[str, pd.DataFrame]] = None,
                             context: Optional[Dict] = None) -> Dict:
        """
        Calculate acceleration metrics and total factor.
        
        Args:
            symbol: Symbol ticker
            data: OHLCV DataFrame for the symbol (must include 'close', 'high', 'low', 'open', 'volume')
            sector_data: Dictionary of DataFrames for other symbols in the same sector (for Resonance)
            context: Market context (optional)
            
        Returns:
            Dict containing scores and total factor
        """
        if data is None or len(data) < 20:
            return {'factor': 1.0, 'reason': 'Insufficient Data', 'is_accelerated': False}
            
        # 1. Volatility Compression (Spring)
        vol_score = self._check_compression(data)
        
        # 2. Liquidity Vacuum (Vacuum)
        vac_score = self._check_vacuum(data)
        
        # 3. Sector Resonance (Resonance)
        res_score = self._check_resonance(symbol, data, sector_data)
        
        # Total Factor Calculation
        # Base 1.0
        # Max Boost +1.0 (Total 2.0)
        # Weights: Vol 30%, Vac 30%, Res 40%
        
        boost = (vol_score * 0.3) + (vac_score * 0.3) + (res_score * 0.4)
        factor = 1.0 + boost
        
        # Clip to safe limits
        factor = min(2.0, factor)
        
        return {
            'factor': factor,
            'scores': {
                'volatility': vol_score,
                'vacuum': vac_score,
                'resonance': res_score
            },
            'is_accelerated': factor >= 1.2
        }

    def _check_compression(self, data: pd.DataFrame) -> float:
        """
        Check for Volatility Compression (NR7, Band Squeeze)
        Returns 0.0 ~ 1.0
        """
        try:
            # Recent 20 days
            recent = data.iloc[-20:].copy()
            
            # 1. NR7 (Narrowest Range in 7 days)
            # Calculate daily range %
            recent['range_pct'] = (recent['high'] - recent['low']) / recent['close'].shift(1)
            
            last_range = recent['range_pct'].iloc[-1]
            min_7d = recent['range_pct'].iloc[-8:-1].min() # Previous 7 days excluding today
            
            is_nr7 = last_range < min_7d
            
            # 2. Bollinger Band Width Squeeze
            # BB Width = (Upper - Lower) / Middle
            # Compare current width to 20d average width
            # Simplified calculation if BB cols not present
            rolling_std = recent['close'].rolling(20).std()
            rolling_mean = recent['close'].rolling(20).mean()
            upper = rolling_mean + (2 * rolling_std)
            lower = rolling_mean - (2 * rolling_std)
            width = (upper - lower) / rolling_mean
            
            avg_width = width.mean()
            current_width = width.iloc[-1]
            
            is_squeeze = current_width < (avg_width * 0.8)
            
            score = 0.0
            if is_nr7: score += 0.5
            if is_squeeze: score += 0.5
            
            return score
            
        except Exception as e:
            logger.warning(f"Compression check failed: {e}")
            return 0.0

    def _check_vacuum(self, data: pd.DataFrame) -> float:
        """
        Check for Liquidity Vacuum (Gap + Volume)
        Returns 0.0 ~ 1.0
        """
        try:
            # Need intraday data for true vacuum, but using daily proxies
            today = data.iloc[-1]
            prev = data.iloc[-2]
            
            # 1. Gap Up/Down
            # Open > Prev High (Gap Up) or Open < Prev Low (Gap Down)
            is_gap_up = today['open'] > prev['high'] * 1.005 # 0.5% Gap
            is_gap_down = today['open'] < prev['low'] * 0.995
            
            if not (is_gap_up or is_gap_down):
                return 0.0
                
            # 2. Volume Explosion
            # Volume > 20d Avg * 1.5
            avg_vol = data['volume'].iloc[-22:-2].mean()
            vol_ratio = today['volume'] / avg_vol if avg_vol > 0 else 0
            
            is_vol_surge = vol_ratio > 1.5
            
            # 3. Directional Move (Vacuum Confirmation)
            # Close near High (for Gap Up) or Low (for Gap Down)
            # This checks if the gap held and accelerated
            range_len = today['high'] - today['low']
            if range_len == 0: return 0.0
            
            if is_gap_up:
                close_pos = (today['close'] - today['low']) / range_len
                is_holding = close_pos > 0.7 # Closed in top 30%
            else:
                close_pos = (today['close'] - today['low']) / range_len
                is_holding = close_pos < 0.3 # Closed in bottom 30%
                
            score = 0.0
            if (is_gap_up or is_gap_down): score += 0.3
            if is_vol_surge: score += 0.3
            if is_holding: score += 0.4
            
            return score
            
        except Exception as e:
            logger.warning(f"Vacuum check failed: {e}")
            return 0.0

    def _check_resonance(self, symbol: str, data: pd.DataFrame, sector_data: Optional[Dict[str, pd.DataFrame]]) -> float:
        """
        Check for Sector Resonance
        Returns 0.0 ~ 1.0
        """
        if not sector_data or len(sector_data) < 2:
            return 0.0
            
        try:
            # Check how many other symbols in sector are trending in same direction
            # Simple metric: % of sector symbols with > 1% move today
            
            today_date = data.index[-1]
            my_change = (data.iloc[-1]['close'] - data.iloc[-2]['close']) / data.iloc[-2]['close']
            my_dir = 1 if my_change > 0 else -1
            
            concordant_count = 0
            total_count = 0
            
            for other_sym, other_df in sector_data.items():
                if other_sym == symbol: continue
                if today_date not in other_df.index: continue
                
                other_row = other_df.loc[today_date]
                prev_row_idx = other_df.index.get_loc(today_date) - 1
                if prev_row_idx < 0: continue
                
                prev_row = other_df.iloc[prev_row_idx]
                
                other_change = (other_row['close'] - prev_row['close']) / prev_row['close']
                
                # Check for significant move (> 1% or > 1 ATR)
                if abs(other_change) > 0.01:
                    if (other_change * my_dir) > 0: # Same direction
                        concordant_count += 1
                
                total_count += 1
                
            if total_count == 0: return 0.0
            
            # Resonance Score
            # If 2+ others are moving with me -> High Resonance
            if concordant_count >= 2:
                return 1.0
            elif concordant_count == 1:
                return 0.5
            else:
                return 0.0
                
        except Exception as e:
            logger.warning(f"Resonance check failed: {e}")
            return 0.0
