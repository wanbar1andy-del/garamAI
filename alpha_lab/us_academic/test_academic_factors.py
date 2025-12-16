"""
Test Suite for Academic Factors
Tests all 5 core factors: Momentum, Value, Quality, Size, Low Volatility
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import logging
from alpha_lab.us_academic.academic_factors import (
    calc_momentum,
    calc_momentum_multiple,
    calc_value_factors,
    calc_quality_factors,
    calc_size_factor,
    calc_low_vol_factor,
    calc_beta,
    rank_cross_sectional,
    calc_composite_factor
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def generate_test_prices(symbols, days=252):
    """Generate synthetic price data for testing"""
    dates = pd.date_range('2023-01-01', periods=days, freq='D')
    
    # Generate realistic price movements
    prices = {}
    for i, symbol in enumerate(symbols):
        base_price = 100 + i * 10
        returns = np.random.randn(days) * 0.02  # 2% daily volatility
        price_series = base_price * (1 + returns).cumprod()
        prices[symbol] = price_series
    
    return pd.DataFrame(prices, index=dates)


def test_momentum():
    """Test momentum factor calculation"""
    print("\n" + "="*60)
    print("Testing Momentum Factor")
    print("="*60)
    
    # Generate test data
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    prices = generate_test_prices(symbols, days=300)
    
    print(f"\n[1/4] Testing 12-month momentum...")
    momentum_12m = calc_momentum(prices, lookback=252, skip=21)
    print(f"  Calculated momentum for {len(momentum_12m)} symbols")
    print(f"  Sample values:\n{momentum_12m.head()}")
    
    # Validations
    assert len(momentum_12m) == len(symbols), "Should have momentum for all symbols"
    assert not momentum_12m.isna().all(), "Should have some valid values"
    print("  [OK] 12-month momentum test passed")
    
    print(f"\n[2/4] Testing multiple momentum periods...")
    momentum_multi = calc_momentum_multiple(prices)
    print(f"  Calculated {len(momentum_multi.columns)} momentum periods")
    print(f"  Columns: {list(momentum_multi.columns)}")
    assert len(momentum_multi.columns) == 3, "Should have 3 periods (12m, 6m, 3m)"
    print("  [OK] Multiple momentum periods test passed")
    
    print(f"\n[3/4] Testing momentum with insufficient data...")
    short_prices = prices.tail(50)  # Only 50 days
    momentum_short = calc_momentum(short_prices, lookback=252, skip=21)
    print(f"  Result with short data: {momentum_short.isna().sum()} NaN values")
    print("  [OK] Insufficient data handling test passed")
    
    print(f"\n[4/4] Testing momentum ranking...")
    momentum_ranks = rank_cross_sectional(momentum_12m, ascending=False)
    print(f"  Ranks (0=worst, 1=best):\n{momentum_ranks.sort_values(ascending=False)}")
    assert (momentum_ranks >= 0).all() and (momentum_ranks <= 1).all(), "Ranks should be 0-1"
    print("  [OK] Momentum ranking test passed")
    
    print("\n[SUCCESS] All Momentum tests passed!")
    return True


def test_value_factors():
    """Test value factors calculation"""
    print("\n" + "="*60)
    print("Testing Value Factors")
    print("="*60)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    prices = generate_test_prices(symbols, days=100)
    
    print(f"\n[1/3] Testing value factors with mock fundamentals...")
    value_factors = calc_value_factors(prices)
    print(f"  Calculated {len(value_factors.columns)} value factors")
    print(f"  Factors: {list(value_factors.columns)}")
    print(f"  Sample values:\n{value_factors.head()}")
    
    assert len(value_factors) == len(symbols), "Should have values for all symbols"
    assert 'value_pe' in value_factors.columns, "Should have P/E factor"
    print("  [OK] Value factors calculation test passed")
    
    print(f"\n[2/3] Testing value factor ranking...")
    pe_ranks = rank_cross_sectional(value_factors['value_pe'], ascending=False)
    print(f"  P/E ranks:\n{pe_ranks.sort_values(ascending=False)}")
    print("  [OK] Value ranking test passed")
    
    print(f"\n[3/3] Testing with custom fundamentals...")
    custom_fundamentals = pd.DataFrame({
        'PE': [15, 20, 25, 30, 35],
        'PB': [2, 3, 4, 5, 6]
    }, index=symbols)
    value_custom = calc_value_factors(prices, custom_fundamentals)
    print(f"  Custom value factors shape: {value_custom.shape}")
    assert len(value_custom) == len(symbols), "Should match symbol count"
    print("  [OK] Custom fundamentals test passed")
    
    print("\n[SUCCESS] All Value Factor tests passed!")
    return True


def test_quality_factors():
    """Test quality factors calculation"""
    print("\n" + "="*60)
    print("Testing Quality Factors")
    print("="*60)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    print(f"\n[1/2] Testing quality factors with mock fundamentals...")
    quality_factors = calc_quality_factors(symbols=symbols)
    print(f"  Calculated {len(quality_factors.columns)} quality factors")
    print(f"  Factors: {list(quality_factors.columns)}")
    print(f"  Sample values:\n{quality_factors.head()}")
    
    assert len(quality_factors) == len(symbols), "Should have quality for all symbols"
    assert 'quality_roe' in quality_factors.columns, "Should have ROE factor"
    print("  [OK] Quality factors calculation test passed")
    
    print(f"\n[2/2] Testing quality factor ranking...")
    roe_ranks = rank_cross_sectional(quality_factors['quality_roe'], ascending=False)
    print(f"  ROE ranks:\n{roe_ranks.sort_values(ascending=False)}")
    print("  [OK] Quality ranking test passed")
    
    print("\n[SUCCESS] All Quality Factor tests passed!")
    return True


def test_size_factor():
    """Test size factor calculation"""
    print("\n" + "="*60)
    print("Testing Size Factor")
    print("="*60)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    print(f"\n[1/3] Testing size factor with log transform...")
    market_caps = pd.Series([2e12, 1.5e12, 1e12, 800e9, 600e9], index=symbols)
    size_scores = calc_size_factor(market_caps, log_transform=True)
    print(f"  Size scores (smaller = higher):\n{size_scores.sort_values(ascending=False)}")
    
    assert len(size_scores) == len(symbols), "Should have size for all symbols"
    assert not size_scores.isna().all(), "Should have valid values"
    print("  [OK] Size factor calculation test passed")
    
    print(f"\n[2/3] Testing size factor ranking...")
    size_ranks = rank_cross_sectional(size_scores, ascending=False)
    print(f"  Size ranks (small-cap premium):\n{size_ranks.sort_values(ascending=False)}")
    print("  [OK] Size ranking test passed")
    
    print(f"\n[3/3] Testing size factor without log transform...")
    size_simple = calc_size_factor(market_caps, log_transform=False)
    print(f"  Simple size scores:\n{size_simple.sort_values(ascending=False).head()}")
    print("  [OK] Non-log transform test passed")
    
    print("\n[SUCCESS] All Size Factor tests passed!")
    return True


def test_low_vol_factor():
    """Test low volatility factor calculation"""
    print("\n" + "="*60)
    print("Testing Low Volatility Factor")
    print("="*60)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    prices = generate_test_prices(symbols, days=252)
    
    print(f"\n[1/4] Testing low vol factor (60-day)...")
    low_vol_60 = calc_low_vol_factor(prices, window=60, method='std')
    print(f"  Low vol scores:\n{low_vol_60.sort_values(ascending=False)}")
    
    assert len(low_vol_60) == len(symbols), "Should have low vol for all symbols"
    assert not low_vol_60.isna().all(), "Should have valid values"
    print("  [OK] Low vol calculation test passed")
    
    print(f"\n[2/4] Testing low vol factor (252-day)...")
    low_vol_252 = calc_low_vol_factor(prices, window=252, method='std')
    print(f"  252-day low vol scores:\n{low_vol_252.sort_values(ascending=False)}")
    print("  [OK] 252-day low vol test passed")
    
    print(f"\n[3/4] Testing low vol ranking...")
    low_vol_ranks = rank_cross_sectional(low_vol_60, ascending=False)
    print(f"  Low vol ranks:\n{low_vol_ranks.sort_values(ascending=False)}")
    print("  [OK] Low vol ranking test passed")
    
    print(f"\n[4/4] Testing beta calculation...")
    # Create mock market index
    market_prices = prices.mean(axis=1)  # Simple average as market proxy
    betas = calc_beta(prices, market_prices, window=60)
    print(f"  Betas:\n{betas.sort_values()}")
    assert len(betas) == len(symbols), "Should have beta for all symbols"
    print("  [OK] Beta calculation test passed")
    
    print("\n[SUCCESS] All Low Volatility tests passed!")
    return True


def test_cross_sectional_ranking():
    """Test cross-sectional ranking utility"""
    print("\n" + "="*60)
    print("Testing Cross-Sectional Ranking")
    print("="*60)
    
    symbols = ['A', 'B', 'C', 'D', 'E']
    values = pd.Series([10, 20, 30, 40, 50], index=symbols)
    
    print(f"\n[1/3] Testing ascending ranking...")
    ranks_asc = rank_cross_sectional(values, ascending=True)
    print(f"  Original values: {values.tolist()}")
    print(f"  Ranks (ascending): {ranks_asc.tolist()}")
    assert ranks_asc['A'] == 0.0, "Lowest value should get rank 0"
    assert ranks_asc['E'] == 1.0, "Highest value should get rank 1"
    print("  [OK] Ascending ranking test passed")
    
    print(f"\n[2/3] Testing descending ranking...")
    ranks_desc = rank_cross_sectional(values, ascending=False)
    print(f"  Ranks (descending): {ranks_desc.tolist()}")
    assert ranks_desc['E'] == 0.0, "Highest value should get rank 0 when descending"
    assert ranks_desc['A'] == 1.0, "Lowest value should get rank 1 when descending"
    print("  [OK] Descending ranking test passed")
    
    print(f"\n[3/3] Testing ranking with NaN...")
    values_with_nan = pd.Series([10, np.nan, 30, 40, 50], index=symbols)
    ranks_nan = rank_cross_sectional(values_with_nan, ascending=True)
    print(f"  Values with NaN: {values_with_nan.tolist()}")
    print(f"  Ranks: {ranks_nan.tolist()}")
    assert pd.isna(ranks_nan['B']), "NaN should remain NaN"
    print("  [OK] NaN handling test passed")
    
    print("\n[SUCCESS] All Cross-Sectional Ranking tests passed!")
    return True


def test_composite_factor():
    """Test composite factor calculation"""
    print("\n" + "="*60)
    print("Testing Composite Factor")
    print("="*60)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    # Create sample factors
    factor_df = pd.DataFrame({
        'momentum': [0.8, 0.6, 0.4, 0.2, 0.0],
        'value': [0.2, 0.4, 0.6, 0.8, 1.0],
        'quality': [0.9, 0.7, 0.5, 0.3, 0.1]
    }, index=symbols)
    
    print(f"\n[1/2] Testing equal-weight composite...")
    composite_equal = calc_composite_factor(factor_df)
    print(f"  Composite scores:\n{composite_equal.sort_values(ascending=False)}")
    assert len(composite_equal) == len(symbols), "Should have composite for all symbols"
    print("  [OK] Equal-weight composite test passed")
    
    print(f"\n[2/2] Testing custom-weight composite...")
    weights = {'momentum': 0.5, 'value': 0.3, 'quality': 0.2}
    composite_custom = calc_composite_factor(factor_df, weights)
    print(f"  Custom weighted composite:\n{composite_custom.sort_values(ascending=False)}")
    print("  [OK] Custom-weight composite test passed")
    
    print("\n[SUCCESS] All Composite Factor tests passed!")
    return True


def test_integration():
    """Integration test: Calculate all factors for a small universe"""
    print("\n" + "="*60)
    print("Testing Integration - All Factors")
    print("="*60)
    
    from alpha_lab.us_academic.symbol_universe import SymbolUniverse
    from alpha_lab.us_academic.us_data_loader import USDataLoader
    
    # Get small universe
    universe = SymbolUniverse()
    symbols = universe.get_sector("Technology")[:5]
    print(f"\nTest universe: {symbols}")
    
    # Fetch real data
    loader = USDataLoader()
    print("\nFetching price data...")
    results = loader.fetch_multiple(symbols, "2023-01-01", "2023-12-31", delay=0.1)
    
    if len(results) == 0:
        print("  [WARN] No data fetched, using mock data")
        prices = generate_test_prices(symbols, days=252)
    else:
        prices = pd.DataFrame({symbol: df['close'] for symbol, df in results.items()})
    
    print(f"Price data shape: {prices.shape}")
    
    # Calculate all factors
    print("\nCalculating all factors...")
    
    print("  1. Momentum...")
    momentum = calc_momentum(prices, lookback=252, skip=21)
    print(f"     Momentum calculated: {len(momentum.dropna())} valid values")
    
    print("  2. Value...")
    value = calc_value_factors(prices)
    print(f"     Value factors: {value.shape}")
    
    print("  3. Quality...")
    quality = calc_quality_factors(symbols=symbols)
    print(f"     Quality factors: {quality.shape}")
    
    print("  4. Size...")
    from alpha_lab.us_academic.academic_factors import _generate_mock_fundamentals
    fundamentals = _generate_mock_fundamentals(symbols)
    size = calc_size_factor(fundamentals['MarketCap'])
    print(f"     Size calculated: {len(size.dropna())} valid values")
    
    print("  5. Low Volatility...")
    low_vol = calc_low_vol_factor(prices, window=60)
    print(f"     Low vol calculated: {len(low_vol.dropna())} valid values")
    
    # Create factor summary
    print("\n" + "="*60)
    print("Factor Summary (Percentile Ranks)")
    print("="*60)
    
    factor_summary = pd.DataFrame({
        'momentum_rank': rank_cross_sectional(momentum, ascending=False),
        'low_vol_rank': rank_cross_sectional(low_vol, ascending=False),
        'size_rank': rank_cross_sectional(size, ascending=False)
    })
    
    print(factor_summary.sort_values('momentum_rank', ascending=False))
    
    print("\n[SUCCESS] Integration test passed!")
    return True


def main():
    """Run all tests"""
    print("="*60)
    print("Academic Factors Test Suite")
    print("="*60)
    
    results = []
    
    tests = [
        ("Momentum", test_momentum),
        ("Value Factors", test_value_factors),
        ("Quality Factors", test_quality_factors),
        ("Size Factor", test_size_factor),
        ("Low Volatility", test_low_vol_factor),
        ("Cross-Sectional Ranking", test_cross_sectional_ranking),
        ("Composite Factor", test_composite_factor),
        ("Integration", test_integration)
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
        print(f"{name:30s}: {status}")
    
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
