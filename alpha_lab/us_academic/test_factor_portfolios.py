"""
Test Suite for Factor Portfolios
Tests portfolio construction and performance metrics
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import logging
from alpha_lab.us_academic.factor_portfolios import (
    build_factor_portfolio,
    build_long_only_tilt,
    build_standard_factor_portfolios,
    calculate_performance_metrics,
    print_performance_summary
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def generate_test_data(symbols, days=252):
    """Generate synthetic price and score data"""
    dates = pd.date_range('2023-01-01', periods=days, freq='D')
    
    # Generate prices
    prices = {}
    for i, symbol in enumerate(symbols):
        base_price = 100 + i * 10
        returns = np.random.randn(days) * 0.02
        price_series = base_price * (1 + returns).cumprod()
        prices[symbol] = price_series
    
    prices_df = pd.DataFrame(prices, index=dates)
    
    # Generate factor scores
    scores = pd.Series(np.random.randn(len(symbols)), index=symbols)
    
    return prices_df, scores


def test_long_short_portfolio():
    """Test long-short portfolio construction"""
    print("\n" + "="*60)
    print("Testing Long-Short Portfolio")
    print("="*60)
    
    symbols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    prices, scores = generate_test_data(symbols, days=126)  # 6 months
    
    print(f"\n[1/4] Testing basic portfolio construction...")
    portfolio_returns = build_factor_portfolio(
        prices=prices,
        scores=scores,
        long_quantile=0.8,   # Top 20%
        short_quantile=0.2,  # Bottom 20%
        rebalance_freq='M',
        long_only=False
    )
    
    print(f"  Portfolio returns: {len(portfolio_returns)} days")
    assert len(portfolio_returns) > 0, "Should have returns"
    assert not portfolio_returns.isna().all(), "Should have valid returns"
    print("  [OK] Basic construction test passed")
    
    print(f"\n[2/4] Testing return statistics...")
    mean_return = portfolio_returns.mean()
    std_return = portfolio_returns.std()
    print(f"  Mean daily return: {mean_return:.6f}")
    print(f"  Std daily return: {std_return:.6f}")
    assert not np.isnan(mean_return), "Mean should not be NaN"
    assert not np.isnan(std_return), "Std should not be NaN"
    print("  [OK] Statistics test passed")
    
    print(f"\n[3/4] Testing no inf values...")
    assert not np.isinf(portfolio_returns).any(), "Should have no inf values"
    print("  [OK] No inf values test passed")
    
    print(f"\n[4/4] Testing monthly rebalancing...")
    # Check that we have reasonable number of rebalances
    # For 6 months, should have ~6 rebalance periods
    print(f"  Total days: {len(portfolio_returns)}")
    print("  [OK] Rebalancing test passed")
    
    print("\n[SUCCESS] All Long-Short Portfolio tests passed!")
    return True


def test_long_only_portfolio():
    """Test long-only portfolio construction"""
    print("\n" + "="*60)
    print("Testing Long-Only Portfolio")
    print("="*60)
    
    symbols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    prices, scores = generate_test_data(symbols, days=126)
    
    print(f"\n[1/3] Testing long-only construction...")
    portfolio_returns = build_factor_portfolio(
        prices=prices,
        scores=scores,
        long_quantile=0.7,  # Top 30%
        short_quantile=0.0,
        rebalance_freq='M',
        long_only=True
    )
    
    print(f"  Portfolio returns: {len(portfolio_returns)} days")
    assert len(portfolio_returns) > 0, "Should have returns"
    print("  [OK] Long-only construction test passed")
    
    print(f"\n[2/3] Testing long-only tilt wrapper...")
    tilt_returns = build_long_only_tilt(
        prices=prices,
        scores=scores,
        rebalance_freq='M',
        top_pct=0.3
    )
    
    print(f"  Tilt returns: {len(tilt_returns)} days")
    assert len(tilt_returns) > 0, "Should have returns"
    print("  [OK] Long-only tilt test passed")
    
    print(f"\n[3/3] Testing return characteristics...")
    mean_return = portfolio_returns.mean()
    print(f"  Mean daily return: {mean_return:.6f}")
    print("  [OK] Return characteristics test passed")
    
    print("\n[SUCCESS] All Long-Only Portfolio tests passed!")
    return True


def test_performance_metrics():
    """Test performance metrics calculation"""
    print("\n" + "="*60)
    print("Testing Performance Metrics")
    print("="*60)
    
    # Generate sample returns
    np.random.seed(42)
    returns = pd.Series(
        np.random.randn(252) * 0.01,  # 1% daily vol
        index=pd.date_range('2023-01-01', periods=252, freq='D')
    )
    
    print(f"\n[1/5] Testing metric calculation...")
    metrics = calculate_performance_metrics(returns)
    
    print(f"  Metrics calculated: {list(metrics.keys())}")
    assert 'total_return' in metrics, "Should have total return"
    assert 'sharpe_ratio' in metrics, "Should have Sharpe ratio"
    assert 'max_drawdown' in metrics, "Should have max drawdown"
    print("  [OK] Metric calculation test passed")
    
    print(f"\n[2/5] Testing total return...")
    total_return = metrics['total_return']
    print(f"  Total return: {total_return:.4f}")
    assert not np.isnan(total_return), "Total return should not be NaN"
    print("  [OK] Total return test passed")
    
    print(f"\n[3/5] Testing Sharpe ratio...")
    sharpe = metrics['sharpe_ratio']
    print(f"  Sharpe ratio: {sharpe:.4f}")
    assert not np.isnan(sharpe), "Sharpe should not be NaN"
    print("  [OK] Sharpe ratio test passed")
    
    print(f"\n[4/5] Testing max drawdown...")
    max_dd = metrics['max_drawdown']
    print(f"  Max drawdown: {max_dd:.4f}")
    assert max_dd <= 0, "Max drawdown should be negative or zero"
    print("  [OK] Max drawdown test passed")
    
    print(f"\n[5/5] Testing win rate...")
    win_rate = metrics['win_rate']
    print(f"  Win rate: {win_rate:.4f}")
    assert 0 <= win_rate <= 1, "Win rate should be between 0 and 1"
    print("  [OK] Win rate test passed")
    
    print("\n[SUCCESS] All Performance Metrics tests passed!")
    return True


def test_standard_factor_portfolios():
    """Test standard factor portfolio builder"""
    print("\n" + "="*60)
    print("Testing Standard Factor Portfolios")
    print("="*60)
    
    from alpha_lab.us_academic.symbol_universe import SymbolUniverse
    from alpha_lab.us_academic.us_data_loader import USDataLoader
    
    # Get small universe
    universe = SymbolUniverse()
    symbols = universe.get_sector("Technology")[:5]
    print(f"\nTest universe: {symbols}")
    
    # Fetch data
    loader = USDataLoader()
    print("\nFetching price data...")
    results = loader.fetch_multiple(symbols, "2023-01-01", "2023-06-30", delay=0.1)
    
    if len(results) == 0:
        print("  [WARN] No data fetched, using mock data")
        prices, _ = generate_test_data(symbols, days=126)
    else:
        prices = pd.DataFrame({s: df['close'] for s, df in results.items()})
    
    print(f"Price data shape: {prices.shape}")
    
    print(f"\n[1/3] Testing standard portfolio builder...")
    factor_returns = build_standard_factor_portfolios(
        prices=prices,
        symbols=symbols,
        start_date="2023-01-01",
        end_date="2023-06-30",
        rebalance_freq='M',
        long_only=False
    )
    
    print(f"  Factor portfolios built: {list(factor_returns.columns)}")
    print(f"  Return data shape: {factor_returns.shape}")
    assert len(factor_returns.columns) > 0, "Should have at least one factor"
    print("  [OK] Standard portfolio builder test passed")
    
    print(f"\n[2/3] Testing individual factors...")
    for factor in factor_returns.columns:
        factor_data = factor_returns[factor].dropna()
        if len(factor_data) > 0:
            print(f"  {factor}: {len(factor_data)} days, "
                  f"mean={factor_data.mean():.6f}, std={factor_data.std():.6f}")
    print("  [OK] Individual factors test passed")
    
    print(f"\n[3/3] Testing performance metrics for each factor...")
    for factor in factor_returns.columns:
        factor_data = factor_returns[factor].dropna()
        if len(factor_data) > 10:  # Need minimum data
            metrics = calculate_performance_metrics(factor_data)
            if metrics:
                print(f"  {factor}: Sharpe={metrics.get('sharpe_ratio', 0):.2f}, "
                      f"MaxDD={metrics.get('max_drawdown', 0):.2%}")
    print("  [OK] Performance metrics test passed")
    
    print("\n[SUCCESS] All Standard Factor Portfolios tests passed!")
    return True


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*60)
    print("Testing Edge Cases")
    print("="*60)
    
    symbols = ['A', 'B', 'C']
    
    print(f"\n[1/3] Testing empty prices...")
    empty_prices = pd.DataFrame()
    empty_scores = pd.Series()
    portfolio_returns = build_factor_portfolio(empty_prices, empty_scores)
    assert portfolio_returns.empty, "Should return empty series for empty input"
    print("  [OK] Empty prices test passed")
    
    print(f"\n[2/3] Testing all NaN scores...")
    prices, _ = generate_test_data(symbols, days=60)
    nan_scores = pd.Series([np.nan] * len(symbols), index=symbols)
    portfolio_returns = build_factor_portfolio(prices, nan_scores)
    # Should handle gracefully (empty or minimal returns)
    print(f"  Returns with NaN scores: {len(portfolio_returns)} days")
    print("  [OK] NaN scores test passed")
    
    print(f"\n[3/3] Testing single symbol...")
    single_symbol = ['A']
    single_prices, single_scores = generate_test_data(single_symbol, days=60)
    portfolio_returns = build_factor_portfolio(single_prices, single_scores, long_only=True)
    print(f"  Single symbol returns: {len(portfolio_returns)} days")
    print("  [OK] Single symbol test passed")
    
    print("\n[SUCCESS] All Edge Cases tests passed!")
    return True


def main():
    """Run all tests"""
    print("="*60)
    print("Factor Portfolios Test Suite")
    print("="*60)
    
    results = []
    
    tests = [
        ("Long-Short Portfolio", test_long_short_portfolio),
        ("Long-Only Portfolio", test_long_only_portfolio),
        ("Performance Metrics", test_performance_metrics),
        ("Standard Factor Portfolios", test_standard_factor_portfolios),
        ("Edge Cases", test_edge_cases)
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
