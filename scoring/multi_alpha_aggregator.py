import pandas as pd
import yaml
from pathlib import Path
from garam.alphas.a2_intraday_trend import A2IntradayTrend
from garam.alphas.a7_intraday_reversal import A7IntradayReversal
from garam.alphas.a3_box_meanrev import A3BoxMeanRev
from garam.alphas.a4_liquidity_shock import A4LiquidityShock
from garam.alphas.a5_vol_breakout import A5VolBreakout
from garam.alphas.a6_volume_shock import A6VolumeShock
from garam.alphas.a8_bb_channel_mr import A8BBChannelMR

class MultiAlphaAggregator:
    def __init__(self, catalog_path: str):
        self.catalog_path = Path(catalog_path)
        self.alphas = {}
        self.catalog = {}
        self._load_catalog()
        
    def _load_catalog(self):
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.catalog = {item['id']: item for item in data.get('alphas', [])}
            
        # Initialize Alpha Objects
        for alpha_id, config in self.catalog.items():
            if config.get('state') not in ['ACTIVE', 'EXPERIMENT']:
                continue
                
            if alpha_id == 'A2_intraday_trend':
                self.alphas[alpha_id] = A2IntradayTrend(alpha_id, config)
            elif alpha_id == 'A7_intraday_reversal':
                self.alphas[alpha_id] = A7IntradayReversal(alpha_id, config)
            elif alpha_id == 'A3_box_meanrev':
                self.alphas[alpha_id] = A3BoxMeanRev(alpha_id, config)
            elif alpha_id == 'A4_liquidity_shock':
                self.alphas[alpha_id] = A4LiquidityShock(alpha_id, config)
            elif alpha_id == 'A5_vol_breakout':
                self.alphas[alpha_id] = A5VolBreakout(alpha_id, config)
            elif alpha_id == 'A6_volume_shock':
                self.alphas[alpha_id] = A6VolumeShock(alpha_id, config)
            elif alpha_id == 'A8_narrow_bb_mr':
                self.alphas[alpha_id] = A8BBChannelMR(alpha_id, config)

    def precompute_all_alphas(self, market_data: dict, universe: list) -> dict:
        """
        Pre-compute raw scores for all alphas.
        Returns: {alpha_id: pd.DataFrame}
        """
        raw_scores = {}
        for alpha_id, alpha_obj in self.alphas.items():
            # print(f"Pre-computing {alpha_id}...")
            scores = alpha_obj.compute_scores(market_data, universe)
            raw_scores[alpha_id] = scores
        return raw_scores

    def aggregate_daily_score(self, date, current_regime: str, raw_scores: dict, external_score_row: pd.Series = None) -> pd.Series:
        """
        Aggregate scores for a specific date based on regime weights and priority rules.
        """
        # 1. Collect all raw scores for this date
        daily_scores = {}
        
        # A1 (External)
        if 'A1_trend_mom_6m' in self.catalog and external_score_row is not None:
             daily_scores['A1_trend_mom_6m'] = external_score_row.fillna(0)

        # Dynamic Alphas
        for alpha_id, df_scores in raw_scores.items():
            if alpha_id not in self.catalog: continue
            if date in df_scores.index:
                # Align to universe (using external_score_row index as universe proxy if avail)
                s = df_scores.loc[date]
                if external_score_row is not None:
                    s = s.reindex(external_score_row.index).fillna(0)
                daily_scores[alpha_id] = s
        
        # 2. Resolve Conflicts based on Regime
        resolved_scores = self.resolve_conflicts(current_regime, daily_scores)
        
        # 3. Apply Weights and Sum
        total_score = pd.Series(0.0, index=external_score_row.index if external_score_row is not None else [])
        
        for alpha_id, score_series in resolved_scores.items():
            cfg = self.catalog.get(alpha_id, {})
            weight = cfg.get('regime_weights', {}).get(current_regime, 0.0)
            
            if weight > 0:
                # Optional: Risk Cap (Max Exposure per Alpha)
                # This is a simplified implementation. Real risk cap requires portfolio-level view.
                # Here we just ensure the raw score doesn't explode.
                score_series = score_series.clip(-3.0, 3.0)
                
                total_score = total_score.add(score_series * weight, fill_value=0)
                
        return total_score

    def resolve_conflicts(self, regime: str, daily_scores: dict) -> dict:
        """
        Apply priority rules to resolve conflicts between alphas.
        
        Logic:
        - R1/R2 (Trend): A5 (Trend) > A7 (Reversal). 
          If A5 is Strong Long (>1.0) and A7 is Short (<0), suppress A7.
        - R3/R7 (Chop/Crash): A7/A6 (Reversal) > A5 (Trend).
          If A7 is Active (abs>1.0), suppress A5.
        
        Phase 5 Update (A8 Narrow):
        - A8 is now a pure mean reversion signal.
        - In R3 (Up-Box), we might want to prioritize Longs, but A8 score handles direction.
        - Conflict with A5? A8 is MR, A5 is Trend.
        - In R3/R4, A8/A6/A7 are primary. A5 is already suppressed by weights (0.0).
        """
        # Copy to avoid mutating original
        final_scores = daily_scores.copy()
        
        a5 = final_scores.get('A5_vol_breakout')
        a7 = final_scores.get('A7_intraday_reversal')
        a6 = final_scores.get('A6_volume_shock')
        a8 = final_scores.get('A8_narrow_bb_mr')
        
        # Rule 1: Trend Regime (R1, R2) - Trend is King
        if regime in ['R1_STRONG_UP', 'R2_UP']:
            if a5 is not None and a7 is not None:
                # If A5 is Bullish, ignore A7 Bearish signal
                # (Don't short the dip in a strong trend)
                mask_conflict = (a5 > 0.5) & (a7 < -0.5)
                final_scores['A7_intraday_reversal'] = a7.mask(mask_conflict, 0.0)
                
        # Rule 2: Mean Reversion Regime (R3, R7) - Reversal is King
        elif regime in ['R3_UP_BOX', 'R7_CRASH', 'R4_BOX']:
            if a7 is not None and a5 is not None:
                # If A7 is Active (Strong Reversal Signal), ignore A5 Trend Signal
                # (Trend signals in chop/crash are often false breakouts)
                mask_active_a7 = (a7.abs() > 1.0)
                final_scores['A5_vol_breakout'] = a5.mask(mask_active_a7, 0.0)
                
            if a6 is not None and a5 is not None:
                # Same for A6 (Volume Shock)
                mask_active_a6 = (a6.abs() > 1.0)
                final_scores['A5_vol_breakout'] = final_scores['A5_vol_breakout'].mask(mask_active_a6, 0.0)
        
        # Rule 3: A8 Directional Bias (R3, R5)
        # With Narrow BB, we trust the signal more.
        # But in R3 (Up-Box), maybe suppress Short signals if they are weak?
        # Let's keep it simple for now and trust the weights.
        if a8 is not None:
            if regime == 'R3_UP_BOX':
                # Long Only bias: Suppress Short signals (A8 < 0)
                final_scores['A8_narrow_bb_mr'] = a8.mask(a8 < 0, 0.0)
            elif regime == 'R5_DOWN_BOX':
                # Short/Avoid Only bias: Suppress Long signals (A8 > 0)
                final_scores['A8_narrow_bb_mr'] = a8.mask(a8 > 0, 0.0)
                
        return final_scores
