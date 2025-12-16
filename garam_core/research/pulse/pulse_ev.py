# garam_core/research/pulse/pulse_ev.py
import numpy as np
import pandas as pd

def compute_ev(df: pd.DataFrame, cost_per_trade: float = 0.0031) -> tuple[float, float]:
    """
    Computes Expected Value (EV) of a pulse strategy, adjusted for costs.
    cost_per_trade: Roundtrip cost (e.g., 0.31% for KRW stock).
    
    Strategy: Enter at Pulse Bar Close, Exit at Next Bar Close.
    (Simple 1-bar holding assumption per user example).
    """
    df = df.copy()
    
    # Signal at T
    sig = df["pulse_signal"]
    
    # Return at T+1 (Trade Result)
    # entry at close[t], exit at close[t+1]
    # ret = close[t+1]/close[t] - 1 = return1[t+1]
    next_ret = df["return1"].shift(-1).fillna(0)
    
    # Gross Return per trade
    # If sig=1, ret. If sig=-1, -ret.
    gross_ret = sig * next_ret
    
    # Cost (applied only if trade occurred)
    # Cost is absolute deduction? Or relative? 
    # Usually cost is subtracted from return.
    # If Trade: Net = Gross - Cost
    
    # Filter trades
    trades_mask = sig != 0
    trade_returns = gross_ret[trades_mask]
    
    if len(trade_returns) == 0:
        return 0.0, 0.0

    net_returns = trade_returns - cost_per_trade
    
    ev = net_returns.mean()
    win_rate = (net_returns > 0).mean()
    
    return ev, win_rate
