
import pandas as pd
import numpy as np
import sys
from pathlib import Path

LOG_DIR = Path("C:/garam/garam/logs/phase4_sim")

def analyze():
    eq_file = LOG_DIR / "equity.csv"
    tr_file = LOG_DIR / "trades.csv"
    
    if not eq_file.exists(): return
    
    # Equity Stats
    df_eq = pd.read_csv(eq_file)
    df_eq['date'] = pd.to_datetime(df_eq['date'])
    df_eq.set_index('date', inplace=True)
    
    initial = 100_000_000
    final = df_eq['equity'].iloc[-1]
    ret = (final - initial) / initial
    
    # MDD
    roll_max = df_eq['equity'].cummax()
    dd = (df_eq['equity'] - roll_max) / roll_max
    mdd = dd.min()
    
    # Scenario Stats
    if 'scenario' in df_eq.columns:
        scen_grp = df_eq.groupby('scenario')['equity'].apply(lambda x: (x.iloc[-1] - x.iloc[0]) / x.iloc[0] if len(x)>0 else 0)
    else:
        scen_grp = {}
        
    print(f"=== Phase 4 Sim Report ===")
    print(f"Period: {df_eq.index[0].date()} ~ {df_eq.index[-1].date()}")
    print(f"Return: {ret*100:.2f}%")
    print(f"MDD: {mdd*100:.2f}%")
    
    # Trade Stats
    if tr_file.exists():
        df_tr = pd.read_csv(tr_file)
        # Hero Contribution
        heroes = df_tr[df_tr['reason'].str.contains('Hero', na=False)]
        
        # Approximate Hero PnL
        # Need to match Buy/Sell? Or just use Realized PnL from trades log (if recorded)
        # My Sim logged PnL on Sell.
        
        realized = df_tr[df_tr['side'] == 'SELL']
        if not realized.empty:
            total_rlz = realized['pnl'].sum()
            hero_sells = realized[realized['reason'].str.contains('Hero|Harvest', na=False)] 
            # Note: Harvest might be selling loser to fund hero. 
            # Strictly "Hero Trades" are those where we exited a Hero?
            # Or just sum PnL of all trades?
            pass
            
            # Win Rate
            wins = len(realized[realized['pnl'] > 0])
            total = len(realized)
            wr = wins / total if total else 0
            print(f"Win Rate: {wr*100:.1f}% ({wins}/{total})")
            
            # Hero Specifics
            # Tickers that were Heroes
            hero_entries = df_tr[df_tr['reason'].str.contains('HeroEntry', na=False)]
            hero_tickers = hero_entries['ticker'].unique()
            print(f"Heroes Cultivated: {len(hero_tickers)}")
            if len(hero_tickers) > 0:
                print(f"Top Heroes: {hero_tickers[:5]}")
                
            # Calculate Total PnL for checks
            print(f"Realized PnL: {total_rlz:,.0f} KRW")

if __name__ == "__main__":
    analyze()
