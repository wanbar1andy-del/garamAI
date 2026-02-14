import numpy as np
import pandas as pd

def simulate_growth():
    print("::: REALISTIC WEALTH SIMULATION: 1M -> 100B KRW :::")
    print("Conditions: Decreasing ROI + Limited Reinvestment + Drawdowns")
    
    # Configuration for Capital Stages
    # Stages match the training curriculum
    stages = [
        {
            "name": "GUERRILLA",
            "max_cap": 10_000_000,          # Up to 10M
            "daily_roi": 0.03,              # 3% per winning day (High volatility)
            "win_rate": 0.60,               # 60% Win rate
            "invest_ratio": 1.00,           # 100% Capital Deployment
            "drawdown_prob": 0.10,          # 10% chance of major slip
        },
        {
            "name": "SNIPER",
            "max_cap": 100_000_000,         # Up to 100M
            "daily_roi": 0.02,              # 2% (AlphaGenius V2 Standard)
            "win_rate": 0.68,               # 68% Win rate (Validated in training)
            "invest_ratio": 1.00,           # 100% Standard
            "drawdown_prob": 0.05,
        },
        {
            "name": "DIVISION",
            "max_cap": 1_000_000_000,       # Up to 1B
            "daily_roi": 0.012,             # 1.2% (Slippage impact)
            "win_rate": 0.65,
            "invest_ratio": 0.80,           # Only invest 80% of equity
            "drawdown_prob": 0.05,
        },
        {
            "name": "SOVEREIGN",
            "max_cap": 10_000_000_000,      # Up to 10B
            "daily_roi": 0.008,             # 0.8% (Market Impact)
            "win_rate": 0.60,
            "invest_ratio": 0.50,           # Only invest 50% (Liquidity Trap)
            "drawdown_prob": 0.03,
        },
        {
            "name": "FLEET",
            "max_cap": float('inf'),        # 100B Target
            "daily_roi": 0.004,             # 0.4% (Institutional Alpha)
            "win_rate": 0.55,
            "invest_ratio": 0.30,           # Only invest 30% (Defensive)
            "drawdown_prob": 0.02,
        }
    ]
    
    equity = 1_000_000.0
    target = 10_000_000_000.0
    days = 0
    history = []
    
    current_stage_idx = 0
    
    # Daily Simulation Loop
    while equity < target:
        days += 1
        
        # Identify Stage
        stage = stages[-1]
        for s in stages:
            if equity < s["max_cap"]:
                stage = s
                break
        
        # Apply Constraints
        investable_capital = equity * stage["invest_ratio"]
        
        # Outcome Determination (Monte Carlo)
        # 1. Check for Crash/Drawdown first
        if np.random.random() < stage["drawdown_prob"]:
            # Fat tail loss: -3% to -7%
            loss_pct = np.random.uniform(0.03, 0.07)
            pnl = -investable_capital * loss_pct
            result = "DRAWDOWN"
        else:
            # Normal Trading
            if np.random.random() < stage["win_rate"]:
                # Win
                pnl = investable_capital * stage["daily_roi"]
                result = "WIN"
            else:
                # Loss (Small)
                loss_pct = stage["daily_roi"] * 0.5 # Stop loss usually tighter than target
                pnl = -investable_capital * loss_pct
                result = "LOSS"
                
        equity += pnl
        
        # Log Milestones
        if days % 150 == 0:
            print(f"Year {days/250:.1f}: {equity:,.0f} KRW [{stage['name']}]")
            
        if days % 20 == 0 or equity >= target: # Monthly log
             history.append({
                 "day": days,
                 "equity": equity,
                 "stage": stage["name"],
                 "invested": investable_capital
             })
             
        # Safety break for infinite loop
        if days > 10000: # ~40 years
            print("(!) Simulation stopped: Exceeded 40 years.")
            break
            
    # Reporting
    years = days / 250.0 # Trading days
    print(f"\n{'='*50}")
    print(f"💰 SIMULATION COMPLETE")
    print(f"Goal: 10,000,000,000 KRW")
    print(f"Time Required: {years:.1f} Years ({days} Trading Days)")
    print(f"{'='*50}")
    
    print(f"\n[Stage Analysis]")
    df = pd.DataFrame(history)
    for s_name in [s["name"] for s in stages]:
        stage_data = df[df["stage"] == s_name]
        if not stage_data.empty:
            start_day = stage_data.iloc[0]["day"]
            end_day = stage_data.iloc[-1]["day"]
            duration = end_day - start_day
            print(f"Stage {s_name:10}: {duration} days ({(duration/250):.1f} years)")
            
    return days

if __name__ == "__main__":
    simulate_growth()
