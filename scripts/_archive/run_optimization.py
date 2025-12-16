import sys
import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime
import logging
import matplotlib.pyplot as plt

# Setup Path
sys.path.append("C:\\garam")
from garam.scripts.run_live_trading import LiveTradingEngine

logging.basicConfig(level=logging.WARNING) # Reduce logs for speed

def run_scenario(name, risk_config, alpha_tweaks=None):
    print(f"\n>>> Running Scenario: {name}")
    
    # 1. Modify Configs
    # Risk Config
    risk_path = Path("C:/garam/garam/risk/account_limits.yaml")
    with open(risk_path, 'r', encoding='utf-8') as f:
        risk_data = yaml.safe_load(f)
    
    risk_data['mode'] = 'ACTIVE'
    risk_data['limits'].update(risk_config)
    
    with open(risk_path, 'w', encoding='utf-8') as f:
        yaml.dump(risk_data, f)
        
    # Alpha Config (if needed)
    if alpha_tweaks:
        alpha_path = Path("C:/garam/garam/config/alpha_catalog.yaml")
        with open(alpha_path, 'r', encoding='utf-8') as f:
            alpha_data = yaml.safe_load(f)
            
        # Apply tweaks (e.g., boost A1 weight)
        # Simplified: We assume alpha_tweaks is a dict of {regime: {alpha_id: weight}}
        # But alpha_catalog structure is list of alphas.
        # We'll just print "Applying Alpha Tweaks" and manually adjust if complex.
        # For now, let's stick to Risk Params first.
        pass

    # 2. Run Simulation
    state_path = f"portfolio_state_{name}.json"
    if Path(state_path).exists():
        Path(state_path).unlink()
        
    engine = LiveTradingEngine("C:/garam/garam/config/profile_champion_v3_weighted_400.yaml", state_path=state_path)
    
    start_date = datetime(2024, 12, 5).date()
    end_date = datetime(2025, 12, 5).date()
    sim_dates = pd.date_range(start=start_date, end=end_date, freq="B")
    
    history = []
    for current_date in sim_dates:
        try:
            engine.run_daily_cycle(target_date=current_date.date())
            history.append({
                "date": current_date,
                "equity": engine.state.get('equity')
            })
        except Exception:
            pass
            
    # 3. Calculate Metrics
    if not history: return 0, 0, []
    
    df = pd.DataFrame(history).set_index('date')
    initial = 100_000_000
    final = df['equity'].iloc[-1]
    pnl = (final - initial) / initial * 100
    
    roll_max = df['equity'].cummax()
    mdd = ((df['equity'] - roll_max) / roll_max).min() * 100
    
    print(f"[{name}] PnL: {pnl:.2f}%, MDD: {mdd:.2f}%")
    return pnl, mdd, df['equity']

def main():
    results = {}
    
    # Scenario 1: Baseline (Current)
    # Daily -3%, Pos 30%
    # pnl, mdd, curve1 = run_scenario("Baseline", {'daily_loss_limit_pct': -3.0, 'max_single_position_pct': 30.0})
    # results['Baseline'] = curve1
    
    # Scenario 2: Loose Risk
    # Daily -10% (Effectively Off), Pos 50%
    pnl, mdd, curve2 = run_scenario("Loose_Risk", {'daily_loss_limit_pct': -10.0, 'max_single_position_pct': 50.0})
    results['Loose_Risk'] = curve2
    
    # Scenario 3: Balanced
    # Daily -5%, Pos 40%
    pnl, mdd, curve3 = run_scenario("Balanced", {'daily_loss_limit_pct': -5.0, 'max_single_position_pct': 40.0})
    results['Balanced'] = curve3
    
    # Plot
    plt.figure(figsize=(12, 6))
    for name, curve in results.items():
        plt.plot(curve.index, curve, label=name)
        
    plt.title("Optimization Scenarios")
    plt.legend()
    plt.grid(True)
    plt.savefig("reports/optimization_result.png")
    print("Saved graph to reports/optimization_result.png")

if __name__ == "__main__":
    main()
