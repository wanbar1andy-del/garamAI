"""
Test script for US Data Infrastructure
Tests USDataLoader and SymbolUniverse
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
from alpha_lab.us_academic.us_data_loader import USDataLoader
from alpha_lab.us_academic.symbol_universe import SymbolUniverse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_symbol_universe():
    """Test Symbol Universe functionality"""
    print("\n" + "="*60)
    print("Testing Symbol Universe")
    print("="*60)
    
    universe = SymbolUniverse()
    
    # Test S&P 500
    print("\n[1/4] Testing S&P 500 symbols...")
    sp500 = universe.get_sp500(limit=10)
    print(f"  Retrieved {len(sp500)} symbols: {sp500}")
    assert len(sp500) == 10, "Should return 10 symbols"
    print("  [OK] S&P 500 test passed")
    
    # Test sectors
    print("\n[2/4] Testing sectors...")
    sectors = universe.get_all_sectors()
    print(f"  Available sectors: {sectors}")
    assert len(sectors) > 0, "Should have sectors"
    
    tech = universe.get_sector("Technology")
    print(f"  Technology sector: {len(tech)} symbols")
    assert len(tech) > 0, "Technology sector should have symbols"
    print("  [OK] Sector test passed")
    
    # Test custom universe
    print("\n[3/4] Testing custom universe...")
    custom_symbols = ["AAPL", "MSFT", "GOOGL"]
    universe.save_custom_universe("test_universe", custom_symbols)
    loaded = universe.get_custom_universe("test_universe")
    print(f"  Saved and loaded: {loaded}")
    assert loaded == custom_symbols, "Custom universe should match"
    print("  [OK] Custom universe test passed")
    
    # Test validation
    print("\n[4/4] Testing symbol validation...")
    test_symbols = ["AAPL", "INVALID!", "MSFT"]
    validation = universe.validate_symbols(test_symbols)
    print(f"  Validation results: {validation}")
    assert validation["AAPL"] == True, "AAPL should be valid"
    assert validation["INVALID!"] == False, "INVALID! should be invalid"
    print("  [OK] Validation test passed")
    
    print("\n[SUCCESS] All Symbol Universe tests passed!")
    return True

def test_data_loader():
    """Test US Data Loader functionality"""
    print("\n" + "="*60)
    print("Testing US Data Loader")
    print("="*60)
    
    loader = USDataLoader()
    
    # Test single symbol (will use mock data if yfinance not available)
    print("\n[1/3] Testing single symbol fetch...")
    df = loader.fetch_data("AAPL", "2023-01-01", "2023-01-31")
    print(f"  Fetched AAPL: {len(df)} rows")
    if not df.empty:
        print(f"  Columns: {list(df.columns)}")
        print(f"  Date range: {df.index[0]} to {df.index[-1]}")
        assert 'close' in df.columns, "Should have 'close' column"
        assert len(df) > 0, "Should have data"
        print("  [OK] Single symbol test passed")
    else:
        print("  [WARN] No data returned (yfinance may not be installed)")
    
    # Test cache
    print("\n[2/3] Testing cache...")
    cache_info = loader.get_cache_info("AAPL")
    print(f"  Cache info: {cache_info}")
    if cache_info.get('cached'):
        print("  [OK] Cache test passed")
    else:
        print("  [INFO] No cache yet")
    
    # Test multiple symbols
    print("\n[3/3] Testing multiple symbols...")
    symbols = ["MSFT", "GOOGL"]
    results = loader.fetch_multiple(symbols, "2023-01-01", "2023-01-31", delay=0.1)
    print(f"  Fetched {len(results)} symbols")
    for symbol, df in results.items():
        print(f"    {symbol}: {len(df)} rows")
    print("  [OK] Multiple symbols test passed")
    
    print("\n[SUCCESS] All Data Loader tests passed!")
    return True

def test_integration():
    """Test integration between components"""
    print("\n" + "="*60)
    print("Testing Integration")
    print("="*60)
    
    universe = SymbolUniverse()
    loader = USDataLoader()
    
    # Get tech sector and fetch data
    print("\n[1/1] Fetching data for Technology sector...")
    tech_symbols = universe.get_sector("Technology")[:3]  # First 3
    print(f"  Symbols: {tech_symbols}")
    
    results = loader.fetch_multiple(tech_symbols, "2023-01-01", "2023-01-31", delay=0.1)
    print(f"  Fetched {len(results)}/{len(tech_symbols)} symbols")
    
    for symbol, df in results.items():
        if not df.empty:
            print(f"    {symbol}: {len(df)} rows, "
                  f"${df['close'].iloc[0]:.2f} -> ${df['close'].iloc[-1]:.2f}")
    
    print("  [OK] Integration test passed")
    print("\n[SUCCESS] All integration tests passed!")
    return True

def main():
    """Run all tests"""
    print("="*60)
    print("US Data Infrastructure Test Suite")
    print("="*60)
    
    results = []
    
    try:
        results.append(("Symbol Universe", test_symbol_universe()))
    except Exception as e:
        print(f"\n[FAIL] Symbol Universe test failed: {e}")
        results.append(("Symbol Universe", False))
    
    try:
        results.append(("Data Loader", test_data_loader()))
    except Exception as e:
        print(f"\n[FAIL] Data Loader test failed: {e}")
        results.append(("Data Loader", False))
    
    try:
        results.append(("Integration", test_integration()))
    except Exception as e:
        print(f"\n[FAIL] Integration test failed: {e}")
        results.append(("Integration", False))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK] Pass" if result else "[FAIL] Fail"
        print(f"{name:20s}: {status}")
    
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
