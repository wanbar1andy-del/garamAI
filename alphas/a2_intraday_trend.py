import pandas as pd
import numpy as np
from .base_alpha import BaseAlpha

class A2IntradayTrend(BaseAlpha):
    """
    A2: Intraday Trend Alpha
    Filters for stocks with consistent intraday buying pressure.
    Logic:
    1. q_t = sign(r_m) * min(|r_m|, |r_a|)  (Trend Quality)
    2. Q_t = EMA_3(q_t) (3-day smoothed trend)
    3. Score = Q_t * RangePos * VolPressure
    """
    
    def compute_scores(self, market_data: dict, universe: list) -> pd.DataFrame:
        # 1. Load Features
        # Expecting wide-format DataFrames (Index=Date, Columns=Symbol)
        q = market_data.get('intraday_trend_q')
        range_pos = market_data.get('intraday_range_pos')
        vol_rel = market_data.get('intraday_vol_rel')
        
        if q is None or range_pos is None or vol_rel is None:
            # print("A2: Missing intraday features.")
            return pd.DataFrame()
            
        # Align with universe
        # Note: market_data might contain more symbols than universe
        # We should align to the universe that exists in the data
        valid_cols = [c for c in universe if c in q.columns]
        q = q[valid_cols]
        range_pos = range_pos[valid_cols]
        vol_rel = vol_rel[valid_cols]
        
        # 2. Calculate Q_t (3-day EMA)
        # Shift 1 day because we use t-1 data for t execution?
        # Standard practice: Alpha for day T is based on data up to T-1.
        # If the input dataframe index is T-1 (data date), then we don't shift if we map by date.
        # But simulation loop asks for score at date D (Trading Day).
        # We should have score available at D based on D-1 data.
        # Usually, we compute scores on data index (D-1), then shift(1) to align with Trading Day D.
        # Let's assume standard behavior: compute on data date, then shift.
        
        Q_t = q.ewm(span=3, adjust=False).mean()
        
        # 3. Scaling
        # Q_tilde = Q_t * (0.5 + range_pos/2) * (0.5 + vol_rel/3)
        # vol_rel clipped to 3
        
        scale_range = 0.5 + (range_pos / 2.0)
        scale_vol = 0.5 + (vol_rel.clip(0, 3.0) / 3.0)
        
        raw_score = Q_t * scale_range * scale_vol
        
        # 4. Cross-sectional Z-score
        # Mean/Std across universe per day
        daily_mean = raw_score.mean(axis=1)
        daily_std = raw_score.std(axis=1).replace(0, np.nan)
        
        z_score = raw_score.sub(daily_mean, axis=0).div(daily_std, axis=0)
        
        # 5. Clip and Fill
        final_score = z_score.clip(-3.0, 3.0).fillna(0.0)
        
        # Shift by 1 day to align with trading day?
        # If the index is "Data Date", we need to shift to "Trading Date".
        # The simulation loop does: daily_alpha = df_scores.loc[date]
        # If 'date' is Trading Date, then we need to shift.
        # Let's check A3/A5 implementation.
        # A3 uses z_score_5d which is computed on close prices.
        # If we use today's close, we can't trade on it today (unless MOC).
        # We trade at Open. So we need yesterday's score.
        # The Aggregator/Simulation usually handles the lookback or the data is already shifted?
        # In `run_champion_rule_v3.py`:
        # `daily_scores = aggregator.aggregate_daily_score(d, ...)`
        # `daily_alpha = df_scores.loc[date]`
        # If `df_scores` index is Data Date (e.g. 2024-12-02), and we trade on 2024-12-03 using 12-02 data...
        # Then `loc[2024-12-03]` would fail if index is 12-02.
        # So we MUST shift the scores forward by 1 day (or reindex).
        
        return final_score.shift(1)
