import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
import matplotlib.pyplot as plt

# Setup Path
sys.path.append("C:\\garam")

from garam.scripts.run_live_trading import LiveTradingEngine
from garam.config import PATHS

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MSS_Verify")

class MSSVerificationEngine(LiveTradingEngine):
    def _fetch_mss_context(self, date):
        d = pd.Timestamp(date)
        score_bias = 0.0
        # Turbo Phase (Mar-May)
        if datetime(2025, 3, 1) <= d < datetime(2025, 6, 1):
            score_bias = 0.8 
        # ABS Phase (Jun-Aug)
        elif datetime(2025, 6, 1) <= d < datetime(2025, 9, 1):
            score_bias = -0.6 
            
        return {
            'exchange_rate_trend': score_bias,
            'interest_rate_spread': score_bias,
            'kospi_trend': score_bias, 
            'market_breadth': score_bias,
            'volatility_vix': -score_bias,
            'semiconductor_cycle': score_bias,
            'foreign_flow': score_bias
        }

    # Override to force Regime
    def run_daily_cycle(self, target_date=None):
        # We need to monkeypatch or override how regime is determined inside the parent method
        # But parent method is long. Easier to mock the method `calculate_latest_micro_regime` globally?
        # Or just let the underlying data flow?
        # Let's try to set self.market_history to favor the regime we want?
        # No, simpler to just run the parent, then post-process? No, allocation happens inside.
        
        # Strategy: Use a context manager to mock the regime function?
        # Or just copy-paste the method and modify? (Messy)
        # Cleaner: Modify LiveTradingEngine to accept an override?
        # Let's just monkeypatch `garam.scripts.run_live_trading.calculate_latest_micro_regime`
        
        d = pd.Timestamp(target_date)
        
        # Turbo Phase -> R4_BOX (to keep base signals consistent, testing Multiplier only)
        if datetime(2025, 3, 1) <= d < datetime(2025, 6, 1):
            forced_regime = "R4_BOX"
        # ABS Phase -> R4_BOX 
        elif datetime(2025, 6, 1) <= d < datetime(2025, 9, 1):
            forced_regime = "R4_BOX"
        else:
            forced_regime = "R4_BOX"

        # Mock the function in the module namespace of the base class
        import garam.scripts.run_live_trading as base_module
        original_func = base_module.calculate_latest_micro_regime
        base_module.calculate_latest_micro_regime = lambda x: forced_regime
        
        try:
            res = super().run_daily_cycle(target_date)
        finally:
            base_module.calculate_latest_micro_regime = original_func
            
        return res


def main():
    print("=== Running MSS Verification Simulation (Turbo/ABS Test) ===")
    
    config_path = "C:/garam/garam/config/profile_champion_v2_1_restored.yaml"
    state_path = "portfolio_state_mss_test.json"
    
    if Path(state_path).exists():
        Path(state_path).unlink()
        
    engine = MSSVerificationEngine(config_path, state_path=state_path)
    
    # Define Period (1 Year)
    start_date = datetime(2024, 12, 5).date()
    end_date = datetime(2025, 12, 5).date()
    sim_dates = pd.date_range(start=start_date, end=end_date, freq="B")
    
    history = []
    
    for current_date in sim_dates:
        target_date = current_date.date()
        if current_date.day == 1:
            print(f">>> Simulating Month: {current_date.strftime('%Y-%m')}")
            
        try:
            # Run Cycle
            target_weights = engine.run_daily_cycle(target_date=target_date)
            
            # Capture Metrics
            # Calculate Gross Exposure
            equity = engine.state.get('equity', 0)
            cash = engine.state.get('cash', 0)
            exposure_val = equity - cash
            exposure_pct = (exposure_val / equity * 100) if equity > 0 else 0
            
            # Capture MSS Mode (Private access for verification)
            mss_mode = engine.mss.current_mode
            mss_score = engine.mss.current_score
            
            history.append({
                "date": target_date,
                "equity": equity,
                "exposure_pct": exposure_pct,
                "mss_mode": mss_mode,
                "mss_score": mss_score
            })
            
        except Exception as e:
            logger.error(f"Error on {target_date}: {e}")
            
    # Generate Report
    if not history:
        print("No history.")
        return
        
    df = pd.DataFrame(history)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    print("\n=== MSS Verification Results ===")
    print(df.groupby('mss_mode')[['exposure_pct']].mean())
    
    # Detailed Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    
    # Ax1: Equity
    ax1.plot(df.index, df['equity'], label='Equity', color='blue')
    ax1.set_title("Equity Curve (MSS Active)")
    ax1.set_ylabel("Equity (KRW)")
    ax1.grid(True)
    
    # Highlight Periods
    # Turbo (Mar-May)
    ax1.axvspan(datetime(2025, 3, 1), datetime(2025, 6, 1), color='green', alpha=0.1, label='Turbo Zone')
    # ABS (Jun-Aug)
    ax1.axvspan(datetime(2025, 6, 1), datetime(2025, 9, 1), color='red', alpha=0.1, label='ABS Zone')
    ax1.legend()
    
    # Ax2: Exposure vs Score
    ax2.plot(df.index, df['exposure_pct'], label='Gross Exposure %', color='orange')
    ax2.set_ylabel("Exposure %")
    ax2.set_ylim(0, 160) # Allow >100% for Turbo
    
    ax3 = ax2.twinx()
    ax3.plot(df.index, df['mss_score'], label='MSS Score', color='gray', linestyle='--', alpha=0.5)
    ax3.set_ylabel("MSS Score")
    ax3.set_ylim(-1.5, 1.5)
    
    ax2.set_title("Exposure vs MSS Score")
    ax2.grid(True)
    
    # Combine legends
    lines, labels = ax2.get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig("reports/mss_verification_result.png")
    print("Saved graph to reports/mss_verification_result.png")
    
    # Save CSV
    df.to_csv("reports/mss_verification_data.csv")

if __name__ == "__main__":
    main()
