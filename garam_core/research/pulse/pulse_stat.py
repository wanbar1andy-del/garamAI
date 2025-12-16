# garam_core/research/pulse/pulse_stat.py
import pandas as pd
import numpy as np

def detect_pulses(df: pd.DataFrame, alpha: float = 2.0, beta: float = 1.2, gamma: float = 1.2) -> pd.DataFrame:
    """
    Detects pulse events using rule-based thresholds.
    
    Conditions:
    1. Abs(Return) > alpha * Vol20(prev)  (Spike relative to recent volatility)
    2. VolRatio (Vol20/Vol20_prev) > beta (Volatility expansion)
    3. VolPressure > gamma (Volume surge)
    """
    df = df.copy()
    
    # Pre-calc required metrics if not present (though enhance_features should have them)
    if "vol_ratio" not in df.columns:
        # Vol20 growth. Need careful shifting.
        # Vol20 is rolling std including current bar? Usually yes.
        # Shift(1) is prev bar.
        v20 = df["vol20"]
        v20_prev = v20.shift(1).replace(0, np.nan) 
        df["vol_ratio"] = v20 / v20_prev
        df["vol_ratio"] = df["vol_ratio"].fillna(1.0)

    condition = (
        (df["return1"].abs() > alpha * df["vol20"].shift(1)) &
        (df["vol_ratio"] > beta) &
        (df["vol_pressure"] > gamma)
    )
    
    df["pulse_signal"] = 0
    df.loc[condition & (df["return1"] > 0), "pulse_signal"] = 1
    df.loc[condition & (df["return1"] < 0), "pulse_signal"] = -1
    
    return df

def pulse_stats(df: pd.DataFrame) -> dict:
    """
    Computes statistics for detected pulses.
    """
    # Filter only pulse bars
    pulses = df[df["pulse_signal"] != 0]
    
    if len(pulses) == 0:
        return {
            "freq": 0.0,
            "count": 0,
            "mean_ret": 0.0,
            "std_ret": 0.0,
            "win_rate": 0.0
        }

    freq = len(pulses) / len(df)
    mean_ret = pulses["return1"].mean()
    std_ret = pulses["return1"].std()
    
    # Win Rate: defined as "Next Bar Return direction matches Pulse direction"?
    # Or "Pulse Bar itself was profitable"? 
    # Usually "Pulse" is a signal to enter? 
    # User prompt: "win_rate = (df["pulse_signal"].shift(-1) * df["return1"] > 0).mean()"
    # This implies: Signal at t -> Action at t+1. 
    # If Signal(t) is +1, we want Return(t+1) > 0.
    # The snippet `df["pulse_signal"].shift(-1) * df["return1"]` aligns Signal(t) with Return(t). 
    # Wait. 
    # If we shift Signal BACKWARDS (-1)? 
    # `signal.shift(1)` is Next row's signal at Current row? No.
    # `shift(1)` moves T to T+1. (Previous value appears at current).
    # `shift(-1)` moves T to T-1. (Next value appears at current).
    
    # User snippet: `(df["pulse_signal"].shift(-1) * df["return1"] > 0).mean()`
    # If we align `signal[t+1]` with `return[t]`. Meaningless.
    
    # Let's assume standard backtest logic:
    # Signal at T -> Return at T+1.
    # We want to check `Signal[T] * Return[T+1] > 0`.
    # `Signal[T]` is `df["pulse_signal"]`.
    # `Return[T+1]` is `df["return1"].shift(-1)`? 
    # `return1` at T is (Close[T]-Close[T-1])/Close[T-1].
    # So `return1[T+1]` is return from T to T+1.
    # Yes.
    
    # Correct logic:
    # signals = df["pulse_signal"] (at T)
    # next_ret = df["return1"].shift(-1) (at T, looking at T+1) -- Wait, shift(-1) brings T+1 data to T row?
    # Yes.
    # So `signals * next_ret > 0` checks if future return matches signal direction.
    
    # User snippet was: `df["pulse_signal"].shift(-1) * df["return1"]`
    # This means `Signal[T+1] * Return[T]`. This looks like "Did the pulse bar itself follow the next signal?" 
    # Or maybe user meant `shift(1)` (Signal at T-1 vs Return at T).
    # I will use the logical standard: `Signal[T] * Return[T+1]`.
    
    next_ret = df["return1"].shift(-1)
    
    # Filter where signal was present at T
    mask = df["pulse_signal"] != 0
    wins = (df.loc[mask, "pulse_signal"] * next_ret.loc[mask]) > 0
    win_rate = wins.mean()
    
    return {
        "freq": freq,
        "count": len(pulses),
        "mean_ret": mean_ret, # Return of the pulse bar itself
        "std_ret": std_ret,
        "win_rate": win_rate  # Predictive win rate for next bar
    }
