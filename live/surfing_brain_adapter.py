import logging
from typing import Dict, Any, Optional
from pathlib import Path
from garam.live.ai_adapter import AIAdapter, AIAdapterConfig
from garam.config import PATHS

logger = logging.getLogger(__name__)

class SurfingBrainAdapter:
    """
    Adapter for SurfingBrain Strategy Logic.
    Decides BUY/SELL/HOLD based on computed features.
    Now with AI "Soul" integration.
    """
    
    def __init__(self):
        logger.info("SurfingBrainAdapter initialized.")
        
        # Initialize AI Adapter
        # Path to models: GARAM_Data/models/ai/v1
        model_path = PATHS.DATA_DIR / "models" / "ai" / "v1"
        self.ai_adapter = None
        
        if model_path.exists():
            try:
                config = AIAdapterConfig(model_root=model_path)
                self.ai_adapter = AIAdapter(config)
                logger.info("AI Adapter loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to init AI Adapter: {e}")
        else:
            logger.warning(f"AI Model path not found: {model_path}")

    def decide(self, features: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a trading decision based on features and config.
        Returns: 
            Dict with keys:
            - signal: 1 (BUY), -1 (SELL), 0 (HOLD)
            - strategy_id: ID of the triggering strategy
            - reason: Explanation
            - ai_confidence: (Optional) AI Score
            - ai_adjustment: (Optional) AI Action
        """
        # Extract key features
        close = features.get('close')
        symbol = features.get('symbol', 'unknown') # Need symbol for AI
        
        result = {
            'signal': 0,
            'strategy_id': 'none',
            'reason': 'No signal'
        }
        
        if not close:
            return result
            
        # Default Config
        if not config:
            config = {'strategy_id': 'TrendFollow_MA', 'params': {'fast': 20, 'slow': 60}}
            
        strategy_id = config.get('strategy_id', 'TrendFollow_MA')
        params = config.get('params', {})
        
        signal = 0
        reason = ""
        
        # Strategy Dispatch
        if strategy_id == 'TrendFollow_MA':
            fast_period = params.get('fast', 20)
            slow_period = params.get('slow', 60)
            
            # Construct keys based on params
            ma_fast_key = f"ma_{int(fast_period)}"
            ma_slow_key = f"ma_{int(slow_period)}"
            
            ma_fast = features.get(ma_fast_key) 
            ma_slow = features.get(ma_slow_key)
            
            if ma_fast and ma_slow:
                # Uptrend
                if ma_fast > ma_slow:
                    if close > ma_fast:
                        signal = 1
                        reason = f"MA Cross Up ({ma_fast:.1f} > {ma_slow:.1f})"
                    elif close < ma_fast:
                        signal = -1 # Or Exit
                        reason = f"Price dropped below Fast MA"
                # Downtrend
                elif ma_fast < ma_slow:
                    signal = -1
                    reason = f"MA Cross Down ({ma_fast:.1f} < {ma_slow:.1f})"
                    
        elif strategy_id == 'MeanReversion_RSI':
            period = params.get('period', 14)
            overbought = params.get('overbought', 70)
            oversold = params.get('oversold', 30)
            
            rsi = features.get('rsi')
            if rsi:
                if rsi < oversold:
                    signal = 1
                    reason = f'RSI Oversold ({rsi:.1f})'
                elif rsi > overbought:
                    signal = -1
                    reason = f'RSI Overbought ({rsi:.1f})'

        # --- AI Overlay ---
        if self.ai_adapter and signal != 0:
            # Get Regime from config or context
            regime = config.get('regime', 'unknown') if config else 'unknown'
            
            # We need symbol in features, usually it's not there by default in StreamProcessor?
            # ShadowTrader passes features which comes from StreamProcessor.
            # StreamProcessor features usually don't have 'symbol'.
            # But ShadowTrader knows the symbol.
            # Wait, `decide` signature is `decide(features, config)`.
            # We don't have `symbol` explicitly unless it's in features.
            # Let's assume features might have it or we can't use it.
            # Actually, `ShadowTrader` calls `self.brain.decide(features, config)`.
            # We should probably inject symbol into features in ShadowTrader if missing.
            # For now, let's use 'unknown' symbol if missing, AI might still work based on technicals.
            
            p_good = self.ai_adapter.score_signal(
                regime=regime,
                symbol=symbol,
                strategy_id=strategy_id,
                signal=signal,
                features=features
            )
            
            if p_good is not None:
                adj = self.ai_adapter.adjust_risk(
                    base_signal=signal,
                    base_risk_multiplier=1.0, # Default base
                    p_good=p_good
                )
                
                # Apply adjustment
                signal = adj['final_signal']
                
                if adj['ai_adjustment'] != 'none':
                    reason += f" | AI:{adj['ai_adjustment']}({p_good:.2f})"
                
                result['ai_confidence'] = p_good
                result['ai_adjustment'] = adj['ai_adjustment']

        result['signal'] = signal
        result['strategy_id'] = strategy_id
        result['reason'] = reason if reason else 'No signal'
        
        return result
