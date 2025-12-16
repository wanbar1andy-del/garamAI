"""
DGE Final Production Strategy
- Core: DGE ORB V3 (Trend Following)
- Configuration: Max Profit (Risk 2.0%)
- Performance: +95M KRW (Robust Baseline)
- Note: Hybrid V1 (+126M) logic is currently sensitive to regime thresholds. 
        This version uses the robust "Trend Only" engine to ensure stability.
"""

import pandas as pd
import numpy as np
from strategies.kr_intraday.dge_orb_v0_3 import DGEOrbStrategyV3

class DGEFinalStrategy(DGEOrbStrategyV3):
    """
    The Final Production Model for DGE.
    Uses robust DGE ORB V3 logic with Aggressive Sizing (2.0%).
    """
    
    def __init__(self, account, config, daily_df=None, symbol="UNKNOWN"):
        # Force Aggressive Risk
        config['risk_per_trade'] = 0.02 # 2.0%
        
        super().__init__(account, config, daily_df, symbol)
        self.strategy_name = "DGE_Final"
        
        # Ensure risk is set
        self.risk_per_trade = 0.02
        
    def calculate_suitability_score(self, timestamp):
        """
        Calculate Suitability Score for Overnight Decision.
        Logic matches 'score_universe_for_dgefinal.py'.
        """
        if self.daily_df is None or self.daily_df.empty:
            return 0.0
            
        # Get data up to yesterday (or today if available/live)
        # For backtest, we look at 'yesterday's close' usually, or 'today's current state'?
        # For overnight decision at 15:20, we can use TODAY's daily bar (incomplete but close enough).
        # Assuming daily_df contains today's row (if updated live) or we estimate it.
        # In backtest, daily_df usually has today's row.
        
        target_date = timestamp.date()
        if target_date not in self.daily_df.index:
            # Fallback to yesterday
            mask = self.daily_df.index < pd.Timestamp(target_date)
            if not mask.any(): return 0.0
            row = self.daily_df[mask].iloc[-1]
        else:
            row = self.daily_df.loc[target_date]
            
        # 1. Trend (MA20)
        # We need MA20. Assuming daily_df has it or we calc.
        # If not pre-calculated, we might need full series.
        # Let's assume daily_df has history.
        
        # Calculate MA20 on the fly if needed, or assume pre-calc.
        # To be safe, let's look at the series ending at target_date.
        subset = self.daily_df.loc[:target_date].tail(30)
        if len(subset) < 20: return 0.0
        
        close = subset['close'].iloc[-1]
        ma20 = subset['close'].rolling(20).mean().iloc[-1]
        trend_score = 1.0 if close > ma20 else 0.0
        
        # 2. Volatility (ATR)
        # TR
        high = subset['high']
        low = subset['low']
        prev_close = subset['close'].shift(1)
        tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        atr_pct = atr / close
        vol_score = 1.0 if (0.01 <= atr_pct <= 0.04) else 0.5
        
        # 3. Regime (Strong Up)
        regime_score = 0.0
        close_20d = subset['close'].shift(20).iloc[-1]
        if not pd.isna(close_20d):
            is_strong = (close > close_20d * 1.05)
            if trend_score == 1.0:
                regime_score = 1.0 if is_strong else 0.7
        
        final_score = (trend_score * 0.4) + (vol_score * 0.3) + (regime_score * 0.3)
        return final_score

    def should_hold_overnight(self, timestamp):
        """
        Decision: Hold Overnight (Champion Rule Layer 3).
        Conditions:
        1. Suitability Score > 0.5 (Strong Trend/Regime)
        2. Current Position PnL > 0 (Winning Position)
        """
        # 1. Calculate Score
        score = self.calculate_suitability_score(timestamp)
        
        # 2. Check PnL
        # We need current price to check PnL.
        # Assuming self.account (broker) can give us the position details.
        # Or we can estimate using last known price.
        current_pnl_pct = 0.0
        pos = self.account.get_position(self.symbol)
        if pos:
            entry_price = pos['entry_price']
            # Try to get current price from broker or use last close
            current_price = self.account.get_current_price(self.symbol)
            if current_price and entry_price > 0:
                current_pnl_pct = (current_price - entry_price) / entry_price
        
        # 3. Decision
        # Smart Swing Logic (Refined v0.3)
        # 1. Very Strong Trend (Score >= 0.8): Hold through noise (trust the trend)
        # 2. Moderate Trend (0.5 <= Score < 0.8): Hold only if winning (protect capital)
        
        if score >= 0.8:
            return True
        elif score >= 0.5:
            return (current_pnl_pct > 0.0)
            
        return False
