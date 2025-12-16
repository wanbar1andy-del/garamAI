from typing import Dict, Any
import logging
from datetime import datetime
from .base import BaseEngine
# from garam.engines.mss_engine import MarketSensingEngine
from .sentiment import SentimentEngine

class MarketSensingEngine:
    """Mock MSS Engine for Compatibility"""
    def update_context(self, context): pass
    def get_decision_modifier(self): return {'score': 80.0} # Default to Favorable for Turbo testing

logger = logging.getLogger("AdvancedEngine")

class AdvancedEngine(BaseEngine):
    """
    Engine 2: Advanced (Market Sensing System)
    
    Role:
    - The "Navigator" & "Traffic Control".
    - Uses MarketSensingEngine (MSS) to analyze Macro, HMM, and Sentiment.
    - Generates 'Turbo' (Speed Up) and 'ABS' (Brake) directives.
    - Also contributes a top-down 'Market Signal' if configured (currently primarily a Modifier).
    """
    
    def __init__(self, use_sentiment: bool = True, use_volatility_timing: bool = True):
        self.mss_model = MarketSensingEngine()
        self.sentiment_engine = SentimentEngine() # MOCK for now
        self.use_sentiment = use_sentiment
        self.use_volatility_timing = use_volatility_timing
        self.name = "AdvancedEngine (MSS)"
        logger.info(f"AdvancedEngine (Engine 2) Initialized with Sentiment. VolTiming={self.use_volatility_timing}")

    def get_name(self) -> str:
        return self.name

    def analyze(self, date: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute MSS logic with Sentiment Integration.
        """
        # 1. Get Market Data from Context
        daily_df = context.get('market_data')
        mss_context = context.get('mss_context', {})
        
        # 2. Score Calculation
        # MSS Score: 0 (Crash) to 100 (Boom)
        # Note: We use MSS to calculate base macro score. 
        # Ideally mss.calculate_score() would take daily_df directly or use internal data.
        # Assuming mss.calculate_score(daily_df) exists or we use modifier logic.
        
        # Update MSS
        self.mss_model.update_context(mss_context)
        
        # Get Base Score (0-100) from MSS logic
        # Since MSS.get_decision_modifier() returns a dict with 'score', we use that.
        modifier = self.mss_model.get_decision_modifier()
        mss_score_raw = modifier.get('score', 50.0)
        
        # 3. [NEW] Sentiment Score (-1.0 to 1.0)
        sent_score = self.sentiment_engine.analyze_market_sentiment(daily_df)
        
        # 4. Fusion Logic
        # New Fusion Score = (MSS_Score * 0.7) + (Sentiment_Score_Normalized * 0.3)
        # Map Sentiment (-1 to 1) to (0 to 100) -> (s + 1) * 50
        sent_score_100 = (sent_score + 1.0) * 50.0
        
        final_score = (mss_score_raw * 0.7) + (sent_score_100 * 0.3)
        
        # 5. Volatility Timing Logic
        vol_mode = self._check_volatility_regime(daily_df)
        
        # 6. Determine Mode based on Score + Sentiment + Volatility
        mode = "NORMAL"
        size_multiplier = 1.0
        force_liquidate = False
        
        if self.use_volatility_timing:
            # ABS Trigger: Low Score OR Extreme Fear Sentiment OR Volatility Spike
            if final_score < 30 or sent_score < -0.8 or vol_mode == 'VOL_PANIC':
                mode = "ABS"
                size_multiplier = 0.5 # Default brake
                if sent_score < -0.9 or vol_mode == 'VOL_PANIC': # Panic
                    mode = "EMERGENCY"
                    force_liquidate = True
                    logger.warning(f"🚨 AdvancedEngine: VOLATILITY PANIC DETECTED (Mode={vol_mode})")
            # TURBO Trigger: High Score AND Positive Sentiment AND Stable Vol
            elif final_score > 70 and sent_score > 0.1 and vol_mode == 'STABLE':
                mode = "TURBO"
                size_multiplier = 1.5 
        else:
            # Standard Logic (No Volatility Timing)
            # ABS Trigger: Low Score OR Extreme Fear Sentiment
            if final_score < 30 or sent_score < -0.8:
                mode = "ABS"
                size_multiplier = 0.5
                if sent_score < -0.9:
                    mode = "EMERGENCY"
                    force_liquidate = True
            
            # TURBO Trigger: High Score AND Positive Sentiment
            elif final_score > 70 and sent_score > 0.1:
                mode = "TURBO"
                size_multiplier = 1.5
            
        # logger.info(f"[AdvancedEngine] MSS={mss_score_raw:.1f}, Sent={sent_score:.2f} -> Final={final_score:.1f} | Mode={mode}")
        
        directives = {
            'mode': mode,
            'score': final_score,
            'sentiment': sent_score,
            'vol_mode': vol_mode,
            'size_multiplier': size_multiplier,
            'force_liquidate': force_liquidate
        }
        
        return {
            'signals': {}, 
            'meta': {
                'mss_score': final_score,
                'sentiment': sent_score,
                'vol_mode': vol_mode
            },
            'directives': directives
        }

    def _check_volatility_regime(self, market_data: Dict[str, Any]) -> str:
        """
        Quick check of Market Volatility Acceleration.
        Constructs an equal-weight index from market_data['close'] and checks Vol Accel.
        """
        try:
            if not market_data or 'close' not in market_data:
                return "UNKNOWN"
                
            closes = market_data['close']
            # Proxy Index: Mean price or Mean Return?
            # Mean Return is better for volatility
            returns = closes.pct_change(fill_method=None).mean(axis=1) # Market Daily Return
            
            if len(returns) < 60: return "UNKNOWN"
            
            # Calc ATR-equivalent (Std Dev of returns)
            # Vol Accel needs ATR (High-Low) ideally, but we only have Closes conveniently here?
            # market_data usually has High/Low frames too.
            # Let's use Std Dev Acceleration as proxy.
            
            std_5 = returns.rolling(5).std()
            std_60 = returns.rolling(60).std()
            
            curr_std_5 = std_5.iloc[-1]
            curr_std_60 = std_60.iloc[-1]
            
            if curr_std_60 == 0: return "UNKNOWN"
            
            vol_accel = curr_std_5 / curr_std_60
            
            if vol_accel > 1.8:
                return "VOL_PANIC"
            elif vol_accel > 1.4:
                return "VOL_WARNING"
            else:
                return "STABLE"
                
        except Exception as e:
            logger.warning(f"Vol Check failed: {e}")
            return "UNKNOWN"
