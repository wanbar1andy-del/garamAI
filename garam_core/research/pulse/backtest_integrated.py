# garam_core/research/pulse/backtest_integrated.py
import pandas as pd
import numpy as np

# Feature matrix needed for prediction
from garam_core.research.pulse.features_ml import make_feature_matrix

def backtest_ml_pulse(df: pd.DataFrame, model, cost_per_trade: float = 0.0031) -> pd.Series:
    """
    Backtests the ML model on the dataframe.
    Strategy:
      - Predict signal using Model (on features).
      - If Signal +1 -> Buy -> Hold 1 bar -> Sell.
      - If Signal -1 -> Short -> Hold 1 bar -> Cover.
      - Cost applied on each trade.
    """
    df = df.copy()
    
    # generate features
    X = make_feature_matrix(df)
    
    # Predict
    # Note: sklearn predict is usually fast enough for batch.
    df["ml_pred"] = model.predict(X)
    
    # Logic: Signal at T triggers Entry at Close[T]? 
    # Usually "Predict" uses info up to T.
    # Entry at Close[T] is possible (MOC).
    # Return is realized at Close[T+1].
    
    equity = [1.0]
    pos = 0     # 0, 1, -1
    entry_price = 0.0
    
    closes = df["close"].values
    signals = df["ml_pred"].values
    
    # Iterate
    # Need to be careful with indexing. 
    # signals[i] corresponds to df.iloc[i]
    
    for i in range(len(df)-1):
        signal = signals[i]
        curr_close = closes[i]
        next_close = closes[i+1]
        
        # At step i (Close):
        # We can enter/exit.
        
        # If we held a position from i-1:
        if pos != 0:
            # We exit now at Close[i] (Wait, loop logic usually handles transition)
            # User snippet:
            # if pos != 0:
            #    pnl = (price_next - entry_price) ...
            #    equity.append(...)
            #    pos = 0
            
            # This implies 1-bar hold exactly. 
            # We entered at T=i. We exit at T=i+1?
            # User loop:
            # i counts 0..N-2.
            # signal = pred[i]. price_next = closes[i+1].
            # if pos==0 and signal!=0: pos=signal, entry=price_next?
            # WAIT. entry=price_next means we enter at i+1?? Then we miss the return from i to i+1.
            # Usually: Signal i -> Enter Close i. Get return Close i+1.
            # User snippet says: `entry_price = price_next`. 
            # This means Signal[i] triggers Entry at Close[i+1].
            # This is "Next Open" or "Next Close" entry. One bar delay.
            # If so, return is from i+1 to i+2.
            # Let's check logic carefully.
            
            # User Snippet:
            # signal = df["ml_pred"].iloc[i]
            # price_next = df["close"].iloc[i+1]
            # if pos == 0:
            #    if signal == 1: pos=1; entry_price=price_next
            # This places Entry at i+1. Value is Close[i+1].
            
            # Then loop continues to i+1.
            # At i+1: signal = pred[i+1]. price_next = closes[i+2].
            # if pos != 0 (it is 1):
            #    pnl = (price_next - entry_price)/entry...
            # This uses Close[i+2] - Close[i+1].
            # So holding period is from T+1 to T+2.
            # Signal was at T.
            # Total delay = 1 bar.
            # This is conservative and realistic (Signal at Close T -> Enter Open T+1/Close T+1).
            # I will follow this exact logic.
            pass
            
        # Re-implementing User Loop Logic exactly
        
        # But we need to handle the state inside loop correctly.
        # "if pos==0" checks current state.
        
    # Re-writing loop to be cleaner but logically identical to request
    
    equity_curve = [1.0]
    pos = 0
    entry_price = 0.0
    
    for i in range(len(df)-1):
        signal = signals[i]
        price_next_bar = closes[i+1] # This is price at T+1
        
        if pos != 0:
            # Check exit
            # We held from T (determined in previous iter) to T+1 (now).
            # Wait, if we set entry_price = price_next_bar in PREVIOUS iteration...
            # Then in THIS iteration, we are at next step?
            # No, user loop structure:
            
            # for i in range(len(df)-1):
            #    process i.
            #    if pos != 0: 
            #       calc pnl using price_next (i+1). 
            #       pos=0.
            
            # This implies if we enter at T, we exit at T+1?
            # Let's trace:
            # i=0. pos=0. signal=1. -> pos=1. entry=price_next (Close[1]).
            # i=1. pos=1. -> pnl = (Close[2] - Close[1]). 
            #       Calculated at i=1 step.
            #       So we captured Return(1->2).
            #       Signal was at 0.
            #       Delay: Signal 0 -> Entry 1 -> Exit 2.
            #       This is valid.
            
            pnl = (price_next_bar - entry_price) / entry_price * pos
            net_pnl = pnl - cost_per_trade # Cost per trade (roundtrip on exit?)
            # Or is it cost per side? User prompt: "0.31% roundtrip".
            # Usually applied once.
            
            equity_curve.append(equity_curve[-1] * (1 + net_pnl))
            pos = 0
            entry_price = 0.0
            
            # Can we enter again immediately?
            # User snippet has "elif pos != 0: ... pos=0; entry=0".
            # Then loop ends for 'i'.
            # So cannot enter at 'i' if we just exited at 'i'.
            # Means we skip signal at 'i'.
            # We wait for i+1.
            
        elif pos == 0:
            # Check entry
            if signal == 1:
                pos = 1
                entry_price = price_next_bar # Enter at Close[i+1]
                equity_curve.append(equity_curve[-1])
            elif signal == -1:
                pos = -1
                entry_price = price_next_bar
                equity_curve.append(equity_curve[-1])
            else:
                pos = 0
                equity_curve.append(equity_curve[-1])
    
    return pd.Series(equity_curve, index=df.index[:len(equity_curve)])
