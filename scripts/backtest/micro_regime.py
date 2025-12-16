"""
Micro Regime Logic Module
Shared by Analysis, Backtest, and Live Trading.
"""

import pandas as pd
import numpy as np

def classify_micro_regime(one_day_ret: float, five_day_ret: float, atr_pct: float) -> str:
    """
    Rule-based micro-regime classification.
    """
    # 1) Direction (5-day)
    if five_day_ret > 0.03:
        direction = "UP"
    elif five_day_ret < -0.03:
        direction = "DOWN"
    else:
        direction = "FLAT"

    # 2) Volatility (ATR%)
    if atr_pct < 0.015:
        vol = "LOWVOL"
    elif atr_pct > 0.03:
        vol = "HIGHVOL"
    else:
        vol = "MIDVOL"

    # 3) Combination
    if direction == "UP" and vol in ("LOWVOL", "MIDVOL"):
        micro = "MR_UP_DRIFT"
    elif direction == "UP" and vol == "HIGHVOL":
        micro = "MR_UP_SPIKE"
    elif direction == "DOWN" and vol == "HIGHVOL":
        micro = "MR_PANIC_DOWN"
    elif direction == "DOWN" and vol != "HIGHVOL":
        micro = "MR_GRIND_DOWN"
    elif direction == "FLAT" and vol == "LOWVOL":
        micro = "MR_FLAT_BOX"
    elif direction == "FLAT" and vol == "HIGHVOL":
        micro = "MR_FLAT_NOISY"
    else:
        micro = "MR_MISC"

    return micro

def calculate_micro_regime_for_date(daily_df: pd.DataFrame, target_date: pd.Timestamp) -> str:
    """
    Calculate Micro Regime for a specific date using historical data up to that date.
    """
    # We need at least 5 days of history + ATR period (14)
    # Ensure data is sorted
    
    # Locate target date index
    if target_date not in daily_df.index:
        # If exact date missing, try previous valid date? 
        # For strictness, return UNKNOWN
        return "MR_UNKNOWN"
        
    idx = daily_df.index.get_loc(target_date)
    
    # Need enough history
    if idx < 20: # Arbitrary buffer for MA/ATR
        return "MR_UNKNOWN"
        
    # Slice up to target date (inclusive)
    # Actually, for "Today's Regime", do we use Today's Close?
    # In Live Trading (Morning), we use Yesterday's Close.
    # In Backtest (Morning), we use Yesterday's Close.
    # So we should look at the row BEFORE target_date.
    
    # Wait, the analysis script used 'row' values which implies current day.
    # But for trading decision at Open, we only know Yesterday's data.
    # So we should pass 'yesterday' as target_date, or handle the shift here.
    # Let's assume the caller passes the "Decision Date" (Today), and we look at Yesterday.
    
    # Actually, let's look at the implementation in micro_regime_analysis.py
    # It used `row['ret_1d']` etc. where `row` is the current day.
    # And it tagged trades with `entry_time` mapped to that day's regime.
    # If entry is at 09:00, we can't know Today's Close.
    # So the analysis script was technically using "Lookahead" if it used Today's Close for Today's Entry.
    # HOWEVER, `tag_trades_with_regimes.py` usually maps Entry Date -> Regime of THAT Date.
    # If Regime is defined by Close, then it is lookahead.
    # We must fix this for Live/Backtest: Use Yesterday's Regime for Today's Entry.
    
    # Let's adjust: The caller should provide the "Data Snapshot" available at decision time.
    # Usually that means the DataFrame ends at Yesterday.
    # So we calculate the regime of the LAST ROW in the dataframe.
    
    row = daily_df.iloc[idx] # This is the target date's row.
    # If we want Yesterday's regime, we should look at idx-1.
    
    # But wait, the user wants to reproduce the analysis.
    # If the analysis used Lookahead, we have a problem.
    # Let's check `micro_regime_analysis.py` again.
    # `trades["entry_micro_regime"] = trades["entry_date_str"].map(micro_map)`
    # `micro_map` is built from `market_daily`.
    # `market_daily` has `ret_1d` calculated from Close.
    # So yes, the analysis used Today's Close to tag Today's Trade.
    # This is a common backtest bias.
    # BUT, for "Regime", it's often acceptable to use "Market State" which might be defined by the day's action?
    # No, for execution, we must use Yesterday.
    
    # CORRECT APPROACH for Live/Backtest:
    # Use Yesterday's Micro-Regime to decide Today's Entry.
    # So if Today is T, we check Regime(T-1).
    
    # Let's implement `calculate_latest_micro_regime(df)` which uses the last available row.
    pass

def calculate_latest_micro_regime(history_df: pd.DataFrame) -> str:
    """
    Calculate the micro regime based on the latest available data (Yesterday's Close).
    """
    if len(history_df) < 20:
        return "MR_UNKNOWN"
        
    df = history_df.copy()
    
    # Calculate necessary columns if missing
    # We need last row's ret_1d, ret_5d, atr_pct
    
    # 1. Returns
    close = df['close']
    ret_1d = close.pct_change(1).iloc[-1]
    ret_5d = close.pct_change(5).iloc[-1]
    
    # 2. ATR
    # TR = Max(H-L, |H-Cp|, |L-Cp|)
    high = df['high']
    low = df['low']
    prev_close = close.shift(1)
    
    tr = np.maximum(high - low, np.maximum(abs(high - prev_close), abs(low - prev_close)))
    atr = tr.rolling(14).mean()
    atr_pct = (atr / close).iloc[-1]
    
    if pd.isna(ret_1d) or pd.isna(ret_5d) or pd.isna(atr_pct):
        return "MR_UNKNOWN"
        
    return classify_micro_regime(ret_1d, ret_5d, atr_pct)
