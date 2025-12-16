# garam_core/research/pulse/regime.py
import pandas as pd

def get_regime(df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """
    Classifies market regime based on Trend over window.
    BULL: Trend > 1%
    BEAR: Trend < -1%
    RANGE: Between -1% and 1%
    """
    df = df.copy()
    
    # 60-bar return
    df["trend_60"] = df["close"].pct_change(window).fillna(0)
    
    df["regime"] = "range"
    df.loc[df["trend_60"] > 0.01, "regime"] = "bull"
    df.loc[df["trend_60"] < -0.01, "regime"] = "bear"
    
    return df
