"""
Verification script for Paper Trading Log Update
Checks if RealBrokerSim correctly calculates exposure and saves logs in the new format.
"""
import sys
from pathlib import Path
import json
import shutil

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from garam.broker.real_broker_sim import RealBrokerSim

def test_paper_trading_log():
    print("Testing RealBrokerSim logging...")
    
    # Use a temp log file
    temp_log = Path("temp_trade_log.json")
    if temp_log.exists():
        temp_log.unlink()
        
    broker = RealBrokerSim(initial_balance=100_000_000, trade_log_path=temp_log)
    
    # 1. Execute BUY
    print("Executing BUY...")
    symbol = "005930"
    price = 70000
    qty = 100 # Value = 7,000,000 (7% exposure)
    
    broker.send_order(symbol, 'BUY', qty, price, strategy_id="TEST_STRAT", reason="Test Buy")
    
    # Check in-memory log
    last_trade = broker.trade_log[-1]
    print(f"Trade Log Entry: {last_trade}")
    
    assert 'exposure_pct' in last_trade, "exposure_pct missing"
    assert 'portfolio_exposure_pct' in last_trade, "portfolio_exposure_pct missing"
    assert 'position_value' in last_trade, "position_value missing"
    assert last_trade['strategy_id'] == "TEST_STRAT", "strategy_id missing"
    
    expected_exposure = (70000 * 100) / 100_000_000
    print(f"Expected Exposure: {expected_exposure:.4f}, Actual: {last_trade['exposure_pct']:.4f}")
    assert abs(last_trade['exposure_pct'] - expected_exposure) < 0.0001
    
    # 2. Check Saved File Format
    print("Checking saved log file...")
    assert temp_log.exists()
    
    with open(temp_log, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    assert 'daily_summary' in data, "daily_summary missing in file"
    assert 'trades' in data, "trades list missing in file"
    assert len(data['trades']) == 1
    
    summary = data['daily_summary']
    print(f"Daily Summary: {summary}")
    assert 'avg_gross_exposure_pct' in summary
    assert 'max_gross_exposure_pct' in summary
    
    # 3. Execute SELL (Partial)
    print("Executing SELL...")
    broker.send_order(symbol, 'SELL', 50, 71000, strategy_id="TEST_STRAT", reason="Take Profit")
    
    with open(temp_log, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    assert len(data['trades']) == 2
    print("Log file updated correctly.")
    
    # Cleanup
    if temp_log.exists():
        temp_log.unlink()
        
    print("\n✅ Verification PASSED!")

if __name__ == "__main__":
    test_paper_trading_log()
