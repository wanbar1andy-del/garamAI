"""
1-Year Return Projection Simulator (Monte Carlo)
Based on GARAM Strategy Design Targets (Rotation Logic).

Assumptions:
- Capital: 100,000,000 KRW
- Win Rate: 40% (Conservative)
- Avg Win: +2.5% (Trend Following)
- Avg Loss: -1.0% (Tight Cut)
- Trade Frequency: 3 trades/day avg (Rotation Active)
- Avg Holding Period: 5 days
- Max Exposure: 50% (Conservative) ~ 80% (Aggressive)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def run_simulation(capital=100_000_000, days=250, num_sims=1000):
    scenarios = [
        {
            "name": "Conservative (Current)",
            "win_rate": 0.40,
            "avg_win": 0.025,
            "avg_loss": -0.010,
            "trades_per_day": 3,
            "pos_size": 0.10,
            "max_pos": 5
        },
        {
            "name": "Aggressive (User Request: >10 Sym, >90% Exp)",
            "win_rate": 0.40, # Assumes edge scales (optimistic)
            "avg_win": 0.025,
            "avg_loss": -0.010,
            "trades_per_day": 5, # More trades to fill portfolio
            "pos_size": 0.08, # 8% * 12 = 96%
            "max_pos": 12     # Target 10-12 positions
        }
    ]
    
    for sc in scenarios:
        print(f"\n🚀 Running Simulation: {sc['name']}")
        results = []
        
        for sim in range(num_sims):
            equity = [capital]
            current_equity = capital
            active_positions = 0
            
            for day in range(days):
                # Simple Portfolio Logic
                # We try to maintain max_pos
                # Trades entering today:
                slots_available = sc['max_pos'] - active_positions
                
                # New entries (Poisson, but capped by slots)
                potential_entries = np.random.poisson(sc['trades_per_day'])
                entries = min(potential_entries, slots_available)
                
                # Exits (assume 20% turnover per day = 5 day holding)
                exits = np.random.binomial(active_positions, 0.20)
                
                # Update positions
                active_positions = active_positions + entries - exits
                active_positions = max(0, min(active_positions, sc['max_pos']))
                
                # Calculate PnL for ACTIVE positions
                # Each active position has a daily fluctuation
                # We simplify: We only realize PnL on exits, but for equity curve we need daily MTM?
                # Let's stick to the previous simple model: PnL comes from *completed* trades or daily drift?
                # Previous model: "Trade Outcome" was immediate. Let's refine.
                # To match previous logic: We simulate N *completed* trades per day equivalent to the turnover.
                
                # Effective completed trades today approx = active_positions * 0.2
                n_completed = np.random.binomial(active_positions, 0.2)
                
                day_pnl = 0
                for _ in range(n_completed):
                    size = current_equity * sc['pos_size']
                    if np.random.random() < sc['win_rate']:
                        day_pnl += size * sc['avg_win']
                    else:
                        day_pnl += size * sc['avg_loss']
                
                current_equity += day_pnl
                equity.append(current_equity)
                
            results.append(equity)

        # Stats
        final_equities = [r[-1] for r in results]
        median_equity = np.median(final_equities)
        cagr = (median_equity / capital) - 1
        
        # Monthly Return approx
        monthly_r = (1 + cagr) ** (1/12) - 1
        
        print("-" * 60)
        print(f"💰 Result: {sc['name']}")
        print(f"   Expected Final Equity: {median_equity:,.0f} KRW")
        print(f"   CAGR (Median):         {cagr*100:.2f}%")
        print(f"   Monthly Return:        {monthly_r*100:.2f}%")
        print(f"   Avg Exposure:          ~{sc['pos_size']*sc['max_pos']*100:.0f}%")
        print("-" * 60)

if __name__ == "__main__":
    run_simulation()
