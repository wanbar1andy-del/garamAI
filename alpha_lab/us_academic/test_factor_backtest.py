"""
Test Suite for Factor Backtest Integration
Tests US_MOM_12_1 strategy and BacktestEngine integration
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import logging
from alpha_lab.us_academic.strategies.us_mom_12_1 import (
    USMomentum121Strategy,
    generate_us_mom_12_1_signal
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def generate_test_data(symbols, days=252):
    """Generate synthetic price data"""
    dates = pd.date_range('2023-01-01', periods=days, freq='D')
    
    prices = {}
    for i, symbol in enumerate(symbols):
        base_price = 100 + i * 10
        # Create momentum: some stocks trending up, some down
        trend = 0.001 if i % 2 == 0 else -0.001
        returns = np.random.randn(days) * 0.02 + trend
        price_series = base_price * (1 + returns).cumprod()
        prices[symbol] = price_series
    
    return pd.DataFrame(prices, index=dates)


def test_strategy_initialization():
    """Test strategy initialization"""
    print("\n" + "="*60)
    print("Testing Strategy Initialization")
    print("="*60)
    
    print(f"\n[1/3] Testing default initialization...")
    strategy = USMomentum121Strategy()
    assert strategy.lookback_months == 12, "Default lookback should be 12"
    assert strategy.skip_months == 1, "Default skip should be 1"
    print("  [OK] Default initialization test passed")
    
    print(f"\n[2/3] Testing custom configuration...")
    config = {
        'lookback_months': 6,
        'skip_months': 1,
        'long_quantile': 0.7,
        'short_quantile': 0.3
    }
    strategy = USMomentum121Strategy(config)
    assert strategy.lookback_months == 6, "Custom lookback should be 6"
    assert strategy.long_quantile == 0.7, "Custom long quantile should be 0.7"
    print("  [OK] Custom configuration test passed")
    
    print(f"\n[3/3] Testing parameter conversion...")
    assert strategy.lookback_days == 6 * 21, "Should convert months to days"
    print("  [OK] Parameter conversion test passed")
    
    print("\n[SUCCESS] All Strategy Initialization tests passed!")
    return True


def test_signal_generation():
    """Test signal generation"""
    print("\n" + "="*60)
    print("Testing Signal Generation")
    print("="*60)
    
    symbols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    prices = generate_test_data(symbols, days=300)
    
    strategy = USMomentum121Strategy()
    
    print(f"\n[1/4] Testing signal generation...")
    signals = strategy.generate_signals(prices)
    print(f"  Generated signals for {len(signals)} symbols")
    assert len(signals) > 0, "Should generate signals"
    print("  [OK] Signal generation test passed")
    
    print(f"\n[2/4] Testing signal values...")
    unique_signals = signals.unique()
    print(f"  Unique signal values: {sorted(unique_signals)}")
    assert all(s in [-1.0, 0.0, 1.0] for s in unique_signals), "Signals should be -1, 0, or 1"
    print("  [OK] Signal values test passed")
    
    print(f"\n[3/4] Testing long/short counts...")
    long_count = (signals == 1.0).sum()
    short_count = (signals == -1.0).sum()
    print(f"  Long positions: {long_count}")
    print(f"  Short positions: {short_count}")
    assert long_count > 0, "Should have long positions"
    assert short_count > 0, "Should have short positions"
    print("  [OK] Long/short counts test passed")
    
    print(f"\n[4/4] Testing signal generation at specific date...")
    mid_date = prices.index[len(prices) // 2]
    signals_mid = strategy.generate_signals(prices, as_of_date=mid_date)
    print(f"  Signals at {mid_date}: {len(signals_mid)} symbols")
    print("  [OK] Specific date test passed")
    
    print("\n[SUCCESS] All Signal Generation tests passed!")
    return True


def test_weight_generation():
    """Test weight generation from signals"""
    print("\n" + "="*60)
    print("Testing Weight Generation")
    print("="*60)
    
    strategy = USMomentum121Strategy()
    
    # Create test signals
    signals = pd.Series({
        'A': 1.0, 'B': 1.0, 'C': 1.0,  # Long
        'D': -1.0, 'E': -1.0,           # Short
        'F': 0.0, 'G': 0.0              # Neutral
    })
    
    print(f"\n[1/3] Testing equal-weight...")
    weights = strategy.generate_weights(signals, equal_weight=True)
    print(f"  Weights:\n{weights}")
    
    long_weight_sum = weights[weights > 0].sum()
    short_weight_sum = weights[weights < 0].sum()
    print(f"  Long weight sum: {long_weight_sum:.4f}")
    print(f"  Short weight sum: {short_weight_sum:.4f}")
    
    assert abs(long_weight_sum - 1.0) < 0.01, "Long weights should sum to 1"
    assert abs(short_weight_sum + 1.0) < 0.01, "Short weights should sum to -1"
    print("  [OK] Equal-weight test passed")
    
    print(f"\n[2/3] Testing net exposure...")
    net_exposure = weights.sum()
    print(f"  Net exposure: {net_exposure:.6f}")
    assert abs(net_exposure) < 0.01, "Net exposure should be near zero"
    print("  [OK] Net exposure test passed")
    
    print(f"\n[3/3] Testing neutral positions...")
    neutral_weights = weights[signals == 0]
    assert (neutral_weights == 0).all(), "Neutral signals should have zero weight"
    print("  [OK] Neutral positions test passed")
    
    print("\n[SUCCESS] All Weight Generation tests passed!")
    return True


def test_backtest():
    """Test backtest functionality"""
    print("\n" + "="*60)
    print("Testing Backtest Functionality")
    print("="*60)
    
    symbols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    prices = generate_test_data(symbols, days=300)
    
    strategy = USMomentum121Strategy()
    
    print(f"\n[1/4] Testing backtest execution...")
    results = strategy.backtest(prices, "2023-01-01", "2023-10-31")
    print(f"  Backtest results shape: {results.shape}")
    assert 'returns' in results.columns, "Should have returns column"
    assert 'cumulative' in results.columns, "Should have cumulative column"
    print("  [OK] Backtest execution test passed")
    
    print(f"\n[2/4] Testing return statistics...")
    returns = results['returns'].dropna()
    print(f"  Trading days: {len(returns)}")
    print(f"  Mean return: {returns.mean():.6f}")
    print(f"  Std return: {returns.std():.6f}")
    assert len(returns) > 0, "Should have returns"
    assert not returns.isna().all(), "Should have valid returns"
    print("  [OK] Return statistics test passed")
    
    print(f"\n[3/4] Testing performance metrics...")
    metrics = results.attrs.get('metrics', {})
    print(f"  Metrics: {list(metrics.keys())}")
    assert 'sharpe_ratio' in metrics, "Should have Sharpe ratio"
    assert 'max_drawdown' in metrics, "Should have max drawdown"
    print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    print(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
    print("  [OK] Performance metrics test passed")
    
    print(f"\n[4/4] Testing cumulative returns...")
    cumulative = results['cumulative'].dropna()
    final_value = cumulative.iloc[-1]
    total_return = final_value - 1
    print(f"  Final cumulative value: {final_value:.4f}")
    print(f"  Total return: {total_return:.2%}")
    assert final_value > 0, "Cumulative value should be positive"
    print("  [OK] Cumulative returns test passed")
    
    print("\n[SUCCESS] All Backtest tests passed!")
    return True


def test_signal_generator_function():
    """Test signal generator function for BacktestEngine"""
    print("\n" + "="*60)
    print("Testing Signal Generator Function")
    print("="*60)
    
    symbols = ['A', 'B', 'C', 'D', 'E']
    prices = generate_test_data(symbols, days=300)
    
    print(f"\n[1/2] Testing signal generator function...")
    spec = {
        'universe': symbols,
        'config': {
            'lookback_months': 12,
            'skip_months': 1
        }
    }
    
    # Test with prices as data bundle
    signals = generate_us_mom_12_1_signal(spec, prices, prices.index[-1])
    print(f"  Generated signals: {len(signals)} symbols")
    assert len(signals) > 0, "Should generate signals"
    print("  [OK] Signal generator function test passed")
    
    print(f"\n[2/2] Testing signal values...")
    print(f"  Signals:\n{signals}")
    assert all(s in [-1.0, 0.0, 1.0] for s in signals.values), "Signals should be -1, 0, or 1"
    print("  [OK] Signal values test passed")
    
    print("\n[SUCCESS] All Signal Generator Function tests passed!")
    return True


def test_integration_with_real_data():
    """Integration test with real data"""
    print("\n" + "="*60)
    print("Testing Integration with Real Data")
    print("="*60)
    
    from alpha_lab.us_academic.symbol_universe import SymbolUniverse
    from alpha_lab.us_academic.us_data_loader import USDataLoader
    from alpha_lab.us_academic.factor_portfolios import print_performance_summary
    
    # Get small universe
    universe = SymbolUniverse()
    symbols = universe.get_sector("Technology")[:5]
    print(f"\nTest universe: {symbols}")
    
    # Fetch data
    loader = USDataLoader()
    print("\nFetching price data...")
    results = loader.fetch_multiple(symbols, "2023-01-01", "2023-12-31", delay=0.1)
    
    if len(results) == 0:
        print("  [WARN] No data fetched, using mock data")
        prices = generate_test_data(symbols, days=252)
    else:
        prices = pd.DataFrame({s: df['close'] for s, df in results.items()})
    
    print(f"Price data shape: {prices.shape}")
    
    print(f"\n[1/2] Testing strategy on real data...")
    strategy = USMomentum121Strategy()
    results_df = strategy.backtest(prices, "2023-01-01", "2023-12-31")
    
    print(f"  Backtest results: {len(results_df)} days")
    assert len(results_df) > 0, "Should have results"
    print("  [OK] Real data backtest test passed")
    
    print(f"\n[2/2] Testing performance summary...")
    if len(results_df['returns'].dropna()) > 10:
        print_performance_summary(results_df['returns'], "US Momentum 12-1 (Real Data)")
    print("  [OK] Performance summary test passed")
    
    print("\n[SUCCESS] All Integration tests passed!")
    return True


def main():
    """Run all tests"""
    print("="*60)
    print("Factor Backtest Integration Test Suite")
    print("="*60)
    
    results = []
    
    tests = [
        ("Strategy Initialization", test_strategy_initialization),
        ("Signal Generation", test_signal_generation),
        ("Weight Generation", test_weight_generation),
        ("Backtest Functionality", test_backtest),
        ("Signal Generator Function", test_signal_generator_function),
        ("Integration with Real Data", test_integration_with_real_data)
    ]
    
    for name, test_func in tests:
        try:
            results.append((name, test_func()))
        except Exception as e:
            print(f"\n[FAIL] {name} test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK] Pass" if result else "[FAIL] Fail"
        print(f"{name:35s}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[FAIL] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
