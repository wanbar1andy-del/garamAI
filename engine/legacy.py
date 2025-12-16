from typing import Dict, Any, List
import pandas as pd
import numpy as np
import logging
from .base import BaseEngine
try:
    from garam.core.alpha_aggregator import AlphaAggregator
except ImportError:
    from core.alpha_aggregator import AlphaAggregator

logger = logging.getLogger("LegacyEngine")

class LegacyEngine(BaseEngine):
    """
    Engine 1: Legacy (Technical & Alpha-Based)
    
    Role:
    - The "Ground Force".
    - Uses the existing AlphaAggregator to score 400+ stocks based on 
      Technical (Trend, MeanRev) and Fundamental signals.
    - Aggressive stock selection.
    """
    def __init__(self, use_volatility_sizing: bool = False, use_volatility_filter: bool = False):
        self.aggregator = AlphaAggregator()
        self.use_volatility_sizing = use_volatility_sizing
        self.use_volatility_filter = use_volatility_filter
        logger.info(f"LegacyEngine (Engine 1) Initialized. VolSizing={self.use_volatility_sizing}, VolFilter={self.use_volatility_filter}")

    def get_name(self) -> str:
        return "Engine 1 (Legacy)"

    def analyze(self, date: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Alpha Aggregation logic.
        """
        market_data = context.get('market_data')
        universe = context.get('universe', [])
        regime = context.get('regime', 'R4_BOX')
        
        if not market_data or not universe:
            logger.warning("LegacyEngine: Missing market_data or universe.")
            return {'signals': {}, 'meta': {}, 'directives': {}}

        try:
            # 1. Compute Alpha Scores
            final_scores, _ = self.aggregator.compute_final_score(market_data, universe, regime)
            
            if final_scores.empty:
                # logger.warning("LegacyEngine: Aggregator returned empty scores! Utilizing Fallback (Quality Score).")
                daily_scores = self._fallback_selection(market_data, universe)
            else:
                daily_scores = final_scores.iloc[-1].to_dict()
            
            # --- VOLATILITY INTEGRATION ---
            if self.use_volatility_sizing:
                # [Strategy B] Risk Parity Sizing (Defensive)
                valid_scores = {k: v for k, v in daily_scores.items() if pd.notna(v) and v > 0}
                top_candidates = sorted(valid_scores.items(), key=lambda x: x[1], reverse=True)[:20]
                top_symbols = [x[0] for x in top_candidates]
                
                if not top_symbols:
                     return {'signals': {}, 'meta': {}, 'directives': {}}

                from .volatility_engine import VolatilityFactorEngine, VolatilitySizer
                
                candidate_data = [] 
                
                for sym in top_symbols:
                    try:
                        cols = {'open': market_data['open'][sym], 'high': market_data['high'][sym], 'low': market_data['low'][sym], 'close': market_data['close'][sym]}
                        df = pd.DataFrame(cols)
                        df.dropna(inplace=True)
                        if len(df) < 20: continue
                        
                        df_slice = df.iloc[-100:].copy()
                        enriched = VolatilityFactorEngine.calculate_factors(df_slice)
                        last_row = enriched.iloc[-1]
                        
                        candidate_data.append({
                            'symbol': sym,
                            'atr_pct': last_row['atr_pct'],
                            'vol_accel': last_row['vol_accel'],
                            'quality_score': last_row['quality_score']
                        })
                    except: continue
                
                risk_weights = VolatilitySizer.calculate_risk_parity_weights(candidate_data)
                final_signals = {k: v * 100.0 for k, v in risk_weights.items()}

            elif self.use_volatility_filter: 
                # [Strategy C] Lite Filter (Aggressive + Safety Cut)
                from .volatility_engine import VolatilityFactorEngine
                filtered_signals = {}
                
                for sym, score in daily_scores.items():
                    if pd.isna(score) or score <= 0: continue
                    try:
                        if sym not in market_data['close'].columns: continue
                        
                        cols = {'close': market_data['close'][sym]}
                        if 'high' in market_data: cols['high'] = market_data['high'].get(sym, cols['close'])
                        if 'low' in market_data: cols['low'] = market_data['low'].get(sym, cols['close'])
                        if 'open' in market_data: cols['open'] = market_data['open'].get(sym, cols['close'])
                        
                        df = pd.DataFrame(cols)
                        if 'high' not in df.columns: df['high'] = df['close']
                        if 'low' not in df.columns: df['low'] = df['close']
                        
                        df.dropna(inplace=True)
                        if len(df) < 30: continue
                        
                        df_slice = df.iloc[-60:].copy()
                        enriched = VolatilityFactorEngine.calculate_factors(df_slice)
                        last_row = enriched.iloc[-1]
                        
                        # [FILTER] Reject Extreme Volatility (VolAccel > 2.0)
                        if last_row.get('vol_accel', 1.0) > 2.0:
                            continue
                            
                        filtered_signals[sym] = score
                    except: continue
                
                final_signals = filtered_signals # Keep original scores, just subset keys

            else:
                # [Strategy A] Standard
                final_signals = {k: v for k, v in daily_scores.items() if pd.notna(v)}
                
            return {
                'signals': final_signals,
                'meta': {
                    'source': 'AlphaAggregator', 
                    'regime_used': regime,
                    'sizing_method': 'RiskParity' if self.use_volatility_sizing else ('VolFilter' if self.use_volatility_filter else 'ScoreWeighted')
                },
                'directives': {}
            }

        except Exception as e:
            logger.error(f"LegacyEngine Analysis Failed: {e}", exc_info=True)
            return {'signals': {}, 'meta': {'error': str(e)}, 'directives': {}}

    def _fallback_selection(self, market_data: Dict[str, Any], universe: list) -> Dict[str, float]:
        """
        Fallback Score Calculation: Vectorized Quality Score (Return / Risk).
        Faster than iterating stocks.
        """
        scores = {}
        try:
            # market_data['close'] is DF (index=date, cols=symbols)
            closes = market_data.get('close')
            if closes is None or closes.empty: return {}
            
            # 1. Slice data for calculation
            df_slice = closes.iloc[-150:] 
            
            if len(df_slice) < 60: return {}
            
            # 2. Calculate Return (6M)
            p_now = df_slice.iloc[-1]
            p_6m = df_slice.iloc[-126] if len(df_slice) >= 126 else df_slice.iloc[0]
            
            ret_6m = (p_now / p_6m) - 1.0
            
            # 3. Calculate Risk (Volatility of Returns)
            daily_ret = df_slice.pct_change(fill_method=None).iloc[-60:]
            vol_60 = daily_ret.std() * np.sqrt(252)
            
            # 4. Quality Score
            vol_60 = vol_60.replace(0, np.inf)
            qual_score = ret_6m / vol_60
            
            # 5. Filter Universe
            valid = qual_score.dropna()
            valid_uni = valid.index.intersection(universe)
            final_series = valid.loc[valid_uni]
            
            if len(final_series) > 0:
                ranks = final_series.rank(pct=True) * 100.0
                scores = ranks.to_dict()
            
        except Exception as e:
            logger.error(f"Fallback Vectorized Failed: {e}")
            return {}
            
        return scores
