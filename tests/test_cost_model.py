"""
Test Cost Model
Unit tests for transaction cost calculations.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sim.cost_model import CostModel, Trade

def test_kr_intraday_costs():
    """Test KR intraday cost calculations"""
    print("=" * 60)
    print("Testing KR Intraday Costs")
    print("=" * 60)
    
    model = CostModel(market="kr_intraday")
    
    # Test small trade
    trade = Trade(notional=10_000_000, volatility=0.02, volume_pct=0.001)
    cost = model.total_cost(trade)
    cost_pct = model.cost_as_percentage(trade)
    
    print(f"\nSmall Trade (10M KRW):")
    print(f"  Commission: {model.calculate_commission(trade.notional):,.0f} KRW")
    print(f"  Slippage: {model.calculate_slippage(trade.notional, trade.volatility, trade.volume_pct):,.0f} KRW")
    print(f"  Market Impact: {model.calculate_market_impact(trade.notional, trade.volume_pct):,.0f} KRW")
    print(f"  Total Cost: {cost:,.0f} KRW ({cost_pct:.4%})")
    
    # Test large trade
    trade_large = Trade(notional=100_000_000, volatility=0.03, volume_pct=0.02)
    cost_large = model.total_cost(trade_large)
    cost_pct_large = model.cost_as_percentage(trade_large)
    
    print(f"\nLarge Trade (100M KRW, high vol, large order):")
    print(f"  Total Cost: {cost_large:,.0f} KRW ({cost_pct_large:.4%})")
    
    return model

def test_us_swing_costs():
    """Test US swing trading costs"""
    print("\n" + "=" * 60)
    print("Testing US Swing Costs")
    print("=" * 60)
    
    model = CostModel(market="us_swing")
    
    # Test trade
    trade = Trade(notional=50_000, volatility=0.025, volume_pct=0.005)
    cost = model.total_cost(trade)
    cost_pct = model.cost_as_percentage(trade)
    
    print(f"\nTrade ($50,000):")
    print(f"  Commission: ${model.calculate_commission(trade.notional):,.2f}")
    print(f"  Slippage: ${model.calculate_slippage(trade.notional, trade.volatility, trade.volume_pct):,.2f}")
    print(f"  Market Impact: ${model.calculate_market_impact(trade.notional, trade.volume_pct):,.2f}")
    print(f"  Total Cost: ${cost:,.2f} ({cost_pct:.4%})")
    
    return model

def test_cost_comparison():
    """Compare costs across markets"""
    print("\n" + "=" * 60)
    print("Cost Comparison Across Markets")
    print("=" * 60)
    
    notional = 10_000_000  # 10M KRW or $10K USD
    trade = Trade(notional=notional, volatility=0.02, volume_pct=0.001)
    
    markets = ["kr_intraday", "kr_swing", "us_intraday", "us_swing"]
    
    print(f"\nTrade Size: {notional:,.0f}")
    print(f"Volatility: {trade.volatility:.2%}")
    print(f"Volume %: {trade.volume_pct:.3%}\n")
    
    for market in markets:
        model = CostModel(market=market)
        cost = model.total_cost(trade)
        cost_pct = model.cost_as_percentage(trade)
        print(f"{market:15s}: {cost:10,.2f} ({cost_pct:.4%})")

if __name__ == "__main__":
    print("\nCost Model Unit Tests\n")
    
    test_kr_intraday_costs()
    test_us_swing_costs()
    test_cost_comparison()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
