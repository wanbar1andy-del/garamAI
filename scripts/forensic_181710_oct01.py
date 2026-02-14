"""
Phase X-2: Forensic Single-Stock Verification
Symbol: 181710 | Date: 2025-10-01

Compare:
  A) Current Logic: Breakout Signal (close >= 30-high, vol > 2x MA) -> Next Bar Entry
  B) Pullback Logic: Breakout confirmed -> Wait for Pullback (-1%+) -> Re-entry

Goal: Prove that (B) avoids "buying at peak" problem.
"""
import pandas as pd
import numpy as np

def load_data():
    df = pd.read_csv('GARAM_Data/60day_replay_kst/181710.csv', parse_dates=['ts'])
    df = df[df['ts'].dt.date == pd.Timestamp('2025-10-01').date()].reset_index(drop=True)
    return df

def compute_signals(df):
    """Compute current breakout signals"""
    df = df.copy()
    df['vol_ma'] = df['volume'].rolling(20).mean()
    df['high_30'] = df['high'].rolling(30).max()
    
    # Current Signal: At bar close, check if close >= prev 30-high AND vol > 2x MA
    df['breakout_signal'] = (
        (df['close'] >= df['high_30'].shift(1)) & 
        (df['volume'] > df['vol_ma'].shift(1) * 2)
    )
    
    # Pullback Signal: After breakout, wait for -1% pullback from recent high
    df['recent_high'] = df['high'].cummax()  # Running high
    df['pullback_pct'] = (df['close'] - df['recent_high']) / df['recent_high']
    
    # Mark "in breakout mode" after first breakout signal
    df['in_breakout_mode'] = df['breakout_signal'].cumsum() > 0
    
    # Pullback signal: In breakout mode AND pullback >= -1% AND starting to recover (close > prev close)
    df['pullback_signal'] = (
        df['in_breakout_mode'] & 
        (df['pullback_pct'] <= -0.01) & 
        (df['close'] > df['close'].shift(1))
    )
    
    return df

def simulate_strategy_A(df):
    """Current Strategy: Enter on breakout signal at NEXT bar open"""
    entry_price = None
    entry_time = None
    trades = []
    
    for i in range(1, len(df)):
        if df.loc[i-1, 'breakout_signal'] and entry_price is None:
            # Signal fired at i-1, enter at i (next bar open)
            entry_price = df.loc[i, 'open']
            entry_time = df.loc[i, 'ts']
            print(f"[A] Entry at {entry_time}: {entry_price}")
            
        if entry_price is not None:
            # Check stop (-1%) or take profit (+5%)
            pnl = (df.loc[i, 'close'] - entry_price) / entry_price
            if pnl <= -0.01:
                exit_price = df.loc[i, 'close']
                trades.append({'entry': entry_price, 'exit': exit_price, 'pnl': pnl, 'type': 'stop'})
                print(f"[A] STOP at {df.loc[i, 'ts']}: {exit_price} (PnL: {pnl:.2%})")
                entry_price = None
            elif pnl >= 0.05:
                exit_price = df.loc[i, 'close']
                trades.append({'entry': entry_price, 'exit': exit_price, 'pnl': pnl, 'type': 'tp'})
                print(f"[A] TP at {df.loc[i, 'ts']}: {exit_price} (PnL: {pnl:.2%})")
                entry_price = None
    
    # Force exit at EOD if still holding
    if entry_price is not None:
        exit_price = df.iloc[-1]['close']
        pnl = (exit_price - entry_price) / entry_price
        trades.append({'entry': entry_price, 'exit': exit_price, 'pnl': pnl, 'type': 'eod'})
        print(f"[A] EOD Exit: {exit_price} (PnL: {pnl:.2%})")
    
    return trades

def simulate_strategy_B(df):
    """Pullback Strategy: Enter on PULLBACK after breakout confirmed"""
    entry_price = None
    entry_time = None
    trades = []
    
    for i in range(1, len(df)):
        if df.loc[i-1, 'pullback_signal'] and entry_price is None:
            # Pullback signal fired at i-1, enter at i (next bar open)
            entry_price = df.loc[i, 'open']
            entry_time = df.loc[i, 'ts']
            print(f"[B] Entry at {entry_time}: {entry_price}")
            
        if entry_price is not None:
            # Check stop (-1%) or take profit (+5%)
            pnl = (df.loc[i, 'close'] - entry_price) / entry_price
            if pnl <= -0.01:
                exit_price = df.loc[i, 'close']
                trades.append({'entry': entry_price, 'exit': exit_price, 'pnl': pnl, 'type': 'stop'})
                print(f"[B] STOP at {df.loc[i, 'ts']}: {exit_price} (PnL: {pnl:.2%})")
                entry_price = None
            elif pnl >= 0.05:
                exit_price = df.loc[i, 'close']
                trades.append({'entry': entry_price, 'exit': exit_price, 'pnl': pnl, 'type': 'tp'})
                print(f"[B] TP at {df.loc[i, 'ts']}: {exit_price} (PnL: {pnl:.2%})")
                entry_price = None
    
    # Force exit at EOD if still holding
    if entry_price is not None:
        exit_price = df.iloc[-1]['close']
        pnl = (exit_price - entry_price) / entry_price
        trades.append({'entry': entry_price, 'exit': exit_price, 'pnl': pnl, 'type': 'eod'})
        print(f"[B] EOD Exit: {exit_price} (PnL: {pnl:.2%})")
    
    return trades

def main():
    print("="*60)
    print("FORENSIC REPLAY: 181710 @ 2025-10-01")
    print("="*60)
    
    df = load_data()
    df = compute_signals(df)
    
    # Show signal times
    breakout_times = df[df['breakout_signal']]['ts'].tolist()
    pullback_times = df[df['pullback_signal']]['ts'].tolist()
    
    print(f"\nBreakout Signals: {len(breakout_times)}")
    for t in breakout_times[:5]: print(f"  - {t}")
    
    print(f"\nPullback Signals: {len(pullback_times)}")
    for t in pullback_times[:5]: print(f"  - {t}")
    
    print("\n" + "="*60)
    print("STRATEGY A: Current (Breakout -> Next Bar Entry)")
    print("="*60)
    trades_A = simulate_strategy_A(df)
    
    print("\n" + "="*60)
    print("STRATEGY B: Pullback (Breakout Confirmed -> Pullback -> Entry)")
    print("="*60)
    trades_B = simulate_strategy_B(df)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    pnl_A = sum(t['pnl'] for t in trades_A) if trades_A else 0
    pnl_B = sum(t['pnl'] for t in trades_B) if trades_B else 0
    print(f"Strategy A (Breakout): {len(trades_A)} trades, Total PnL: {pnl_A:.2%}")
    print(f"Strategy B (Pullback): {len(trades_B)} trades, Total PnL: {pnl_B:.2%}")
    
    if pnl_B > pnl_A:
        print("\n✓ Pullback Strategy OUTPERFORMS Breakout Strategy")
    else:
        print("\n✗ Pullback Strategy did NOT outperform (investigate further)")

if __name__ == "__main__":
    main()
