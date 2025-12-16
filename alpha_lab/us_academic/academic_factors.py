"""
Academic Factors for US Stocks
Implements 5 core academic factors: Momentum, Value, Quality, Size, Low Volatility
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Union
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Momentum Factors
# ============================================================================

def calc_momentum(
    prices: pd.DataFrame,
    lookback: int = 252,
    skip: int = 21,
    method: str = 'total_return'
) -> pd.Series:
    """
    Calculate momentum factor (cross-sectional)
    
    Args:
        prices: DataFrame with prices (index=date, columns=symbols)
        lookback: Lookback period in days (default: 252 = 12 months)
        skip: Skip recent days (default: 21 = 1 month)
        method: 'total_return' or 'log_return'
    
    Returns:
        Series with momentum scores for each symbol (as of last date)
    """
    if prices.empty:
        return pd.Series(dtype=float)
    
    # Get the last date
    last_date = prices.index[-1]
    
    # Calculate start date for momentum
    start_idx = max(0, len(prices) - lookback - skip)
    end_idx = max(0, len(prices) - skip)
    
    if start_idx >= end_idx:
        logger.warning("Not enough data for momentum calculation")
        return pd.Series(index=prices.columns, data=np.nan)
    
    # Calculate returns
    start_prices = prices.iloc[start_idx]
    end_prices = prices.iloc[end_idx]
    
    if method == 'total_return':
        momentum = (end_prices / start_prices) - 1
    elif method == 'log_return':
        momentum = np.log(end_prices / start_prices)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Remove NaN and inf
    momentum = momentum.replace([np.inf, -np.inf], np.nan)
    
    return momentum


def calc_momentum_multiple(
    prices: pd.DataFrame,
    periods: Dict[str, int] = None
) -> pd.DataFrame:
    """
    Calculate multiple momentum periods
    
    Args:
        prices: DataFrame with prices
        periods: Dict of {name: lookback_days}
                 Default: {'12m': 252, '6m': 126, '3m': 63}
    
    Returns:
        DataFrame with momentum scores for each period
    """
    if periods is None:
        periods = {'12m': 252, '6m': 126, '3m': 63}
    
    results = {}
    for name, lookback in periods.items():
        results[f'momentum_{name}'] = calc_momentum(prices, lookback=lookback)
    
    return pd.DataFrame(results)


# ============================================================================
# Value Factors
# ============================================================================

def calc_value_factors(
    prices: pd.DataFrame,
    fundamentals: Optional[pd.DataFrame] = None,
    fundamentals_provider: Optional['FundamentalsProvider'] = None
) -> pd.DataFrame:
    """
    Calculate value factors
    
    Args:
        prices: DataFrame with prices (index=date, columns=symbols)
        fundamentals: DataFrame with fundamental data (columns: PE, PB, EV_EBITDA, DivYield)
                      If None, will use fundamentals_provider or generate mock data
        fundamentals_provider: FundamentalsProvider instance (optional)
    
    Returns:
        DataFrame with value factor scores
    """
    symbols = prices.columns
    
    # Use fundamentals_provider if provided and fundamentals is None
    if fundamentals is None:
        if fundamentals_provider is not None:
            try:
                # Get fundamentals from provider
                start_date = prices.index[0].strftime('%Y-%m-%d')
                end_date = prices.index[-1].strftime('%Y-%m-%d')
                fields = ['PE', 'PB', 'EV_EBITDA', 'DivYield']
                fund_df = fundamentals_provider.get_fundamentals(
                    list(symbols), start_date, end_date, fields
                )
                # Use latest available data
                if not fund_df.empty:
                    fundamentals = fund_df.groupby('symbol').last()
            except Exception as e:
                logger.warning(f"Failed to get fundamentals from provider: {e}")
        
        # Fallback to mock data
        if fundamentals is None:
            fundamentals = _generate_mock_fundamentals(symbols)
    
    value_factors = pd.DataFrame(index=symbols)
    
    # P/E ratio (lower is better, so invert)
    if 'PE' in fundamentals.columns:
        value_factors['value_pe'] = 1 / fundamentals['PE']
    
    # P/B ratio (lower is better, so invert)
    if 'PB' in fundamentals.columns:
        value_factors['value_pb'] = 1 / fundamentals['PB']
    
    # EV/EBITDA (lower is better, so invert)
    if 'EV_EBITDA' in fundamentals.columns:
        value_factors['value_ev_ebitda'] = 1 / fundamentals['EV_EBITDA']
    
    # Dividend Yield (higher is better)
    if 'DivYield' in fundamentals.columns:
        value_factors['value_div_yield'] = fundamentals['DivYield']
    
    # Replace inf with NaN
    value_factors = value_factors.replace([np.inf, -np.inf], np.nan)
    
    return value_factors


# ============================================================================
# Quality Factors
# ============================================================================

def calc_quality_factors(
    fundamentals: Optional[pd.DataFrame] = None,
    symbols: Optional[list] = None,
    fundamentals_provider: Optional['FundamentalsProvider'] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate quality factors
    
    Args:
        fundamentals: DataFrame with fundamental data (columns: ROE, ROA, DebtEquity, ProfitMargin)
        symbols: List of symbols (used if fundamentals is None)
        fundamentals_provider: FundamentalsProvider instance (optional)
        start_date: Start date for provider query (YYYY-MM-DD)
        end_date: End date for provider query (YYYY-MM-DD)
    
    Returns:
        DataFrame with quality factor scores
    """
    # Use fundamentals_provider if provided and fundamentals is None
    if fundamentals is None:
        if fundamentals_provider is not None and symbols is not None:
            try:
                fields = ['ROE', 'ROA', 'DEBT_TO_EQUITY', 'ProfitMargin']
                fund_df = fundamentals_provider.get_fundamentals(
                    symbols, start_date or '2020-01-01', 
                    end_date or datetime.now().strftime('%Y-%m-%d'),
                    fields
                )
                # Use latest available data
                if not fund_df.empty:
                    fundamentals = fund_df.groupby('symbol').last()
                    # Rename DEBT_TO_EQUITY to DebtEquity for compatibility
                    if 'DEBT_TO_EQUITY' in fundamentals.columns:
                        fundamentals['DebtEquity'] = fundamentals['DEBT_TO_EQUITY']
            except Exception as e:
                logger.warning(f"Failed to get fundamentals from provider: {e}")
        
        # Fallback to mock data
        if fundamentals is None:
            if symbols is None:
                raise ValueError("Either fundamentals or symbols must be provided")
            fundamentals = _generate_mock_fundamentals(symbols)
    
    quality_factors = pd.DataFrame(index=fundamentals.index)
    
    # ROE (higher is better)
    if 'ROE' in fundamentals.columns:
        quality_factors['quality_roe'] = fundamentals['ROE']
    
    # ROA (higher is better)
    if 'ROA' in fundamentals.columns:
        quality_factors['quality_roa'] = fundamentals['ROA']
    
    # Debt/Equity (lower is better, so invert)
    if 'DebtEquity' in fundamentals.columns:
        quality_factors['quality_debt_equity'] = 1 / (1 + fundamentals['DebtEquity'])
    
    # Profit Margin (higher is better)
    if 'ProfitMargin' in fundamentals.columns:
        quality_factors['quality_profit_margin'] = fundamentals['ProfitMargin']
    
    # Replace inf with NaN
    quality_factors = quality_factors.replace([np.inf, -np.inf], np.nan)
    
    return quality_factors


# ============================================================================
# Size Factor
# ============================================================================

def calc_size_factor(
    market_caps: Union[pd.Series, pd.DataFrame],
    log_transform: bool = True
) -> pd.Series:
    """
    Calculate size factor
    
    Args:
        market_caps: Series or DataFrame with market cap values
        log_transform: Apply log transformation (recommended)
    
    Returns:
        Series with size scores (smaller = higher score for small-cap premium)
    """
    if isinstance(market_caps, pd.DataFrame):
        # If DataFrame, use the last row
        market_caps = market_caps.iloc[-1]
    
    if log_transform:
        # Log transform and invert (smaller caps get higher scores)
        size_scores = -np.log(market_caps)
    else:
        # Simple inversion
        size_scores = 1 / market_caps
    
    # Replace inf with NaN
    size_scores = size_scores.replace([np.inf, -np.inf], np.nan)
    
    return size_scores


# ============================================================================
# Low Volatility Factor
# ============================================================================

def calc_low_vol_factor(
    prices: pd.DataFrame,
    window: int = 60,
    method: str = 'std'
) -> pd.Series:
    """
    Calculate low volatility factor
    
    Args:
        prices: DataFrame with prices (index=date, columns=symbols)
        window: Rolling window for volatility calculation (default: 60 days)
        method: 'std' (standard deviation) or 'range' (high-low range)
    
    Returns:
        Series with volatility scores (lower vol = higher score)
    """
    if prices.empty or len(prices) < window:
        return pd.Series(index=prices.columns, data=np.nan)
    
    # Calculate returns
    returns = prices.pct_change()
    
    if method == 'std':
        # Rolling standard deviation of returns
        vol = returns.rolling(window=window).std().iloc[-1]
    elif method == 'range':
        # Rolling range (max - min) / mean
        rolling_max = prices.rolling(window=window).max()
        rolling_min = prices.rolling(window=window).min()
        rolling_mean = prices.rolling(window=window).mean()
        vol = ((rolling_max - rolling_min) / rolling_mean).iloc[-1]
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Invert (lower volatility = higher score)
    low_vol_scores = 1 / (1 + vol)
    
    # Replace inf with NaN
    low_vol_scores = low_vol_scores.replace([np.inf, -np.inf], np.nan)
    
    return low_vol_scores


def calc_beta(
    prices: pd.DataFrame,
    market_prices: pd.Series,
    window: int = 252
) -> pd.Series:
    """
    Calculate beta (systematic risk)
    
    Args:
        prices: DataFrame with stock prices
        market_prices: Series with market index prices
        window: Rolling window (default: 252 = 1 year)
    
    Returns:
        Series with beta values
    """
    if len(prices) < window or len(market_prices) < window:
        return pd.Series(index=prices.columns, data=np.nan)
    
    # Calculate returns
    stock_returns = prices.pct_change()
    market_returns = market_prices.pct_change()
    
    # Calculate beta for each stock
    betas = {}
    for symbol in prices.columns:
        # Covariance and variance
        cov = stock_returns[symbol].tail(window).cov(market_returns.tail(window))
        var = market_returns.tail(window).var()
        
        if var > 0:
            betas[symbol] = cov / var
        else:
            betas[symbol] = np.nan
    
    return pd.Series(betas)


# ============================================================================
# Cross-Sectional Ranking
# ============================================================================

def rank_cross_sectional(
    values: pd.Series,
    ascending: bool = False,
    method: str = 'average'
) -> pd.Series:
    """
    Rank values cross-sectionally (percentile ranking)
    
    Args:
        values: Series with values to rank
        ascending: If True, lower values get higher ranks
        method: 'average', 'min', 'max', 'dense', 'first'
    
    Returns:
        Series with percentile ranks (0 to 1)
    """
    # Remove NaN
    valid_values = values.dropna()
    
    if len(valid_values) == 0:
        return pd.Series(index=values.index, data=np.nan)
    
    # Rank
    ranks = valid_values.rank(ascending=ascending, method=method)
    
    # Convert to percentiles (0 to 1)
    percentiles = (ranks - 1) / (len(ranks) - 1) if len(ranks) > 1 else pd.Series(0.5, index=ranks.index)
    
    # Reindex to original index (fills NaN for missing values)
    percentiles = percentiles.reindex(values.index)
    
    return percentiles


def calc_composite_factor(
    factor_df: pd.DataFrame,
    weights: Optional[Dict[str, float]] = None
) -> pd.Series:
    """
    Calculate composite factor from multiple factors
    
    Args:
        factor_df: DataFrame with multiple factors (columns = factors)
        weights: Dict of {factor_name: weight}
                 If None, equal weights
    
    Returns:
        Series with composite factor scores
    """
    if weights is None:
        weights = {col: 1.0 / len(factor_df.columns) for col in factor_df.columns}
    
    # Normalize weights
    total_weight = sum(weights.values())
    weights = {k: v / total_weight for k, v in weights.items()}
    
    # Calculate weighted sum
    composite = pd.Series(0.0, index=factor_df.index)
    for factor, weight in weights.items():
        if factor in factor_df.columns:
            composite += factor_df[factor].fillna(0) * weight
    
    return composite


# ============================================================================
# Utility Functions
# ============================================================================

def _generate_mock_fundamentals(symbols: list) -> pd.DataFrame:
    """Generate mock fundamental data for testing"""
    np.random.seed(42)  # For reproducibility
    
    n = len(symbols)
    
    fundamentals = pd.DataFrame({
        'PE': np.random.uniform(5, 50, n),           # P/E ratio
        'PB': np.random.uniform(0.5, 10, n),         # P/B ratio
        'EV_EBITDA': np.random.uniform(5, 30, n),    # EV/EBITDA
        'DivYield': np.random.uniform(0, 0.05, n),   # Dividend yield (0-5%)
        'ROE': np.random.uniform(-0.1, 0.4, n),      # ROE (-10% to 40%)
        'ROA': np.random.uniform(-0.05, 0.2, n),     # ROA (-5% to 20%)
        'DebtEquity': np.random.uniform(0, 3, n),    # Debt/Equity ratio
        'ProfitMargin': np.random.uniform(-0.1, 0.3, n),  # Profit margin
        'MarketCap': np.random.uniform(1e9, 1e12, n)      # Market cap ($1B to $1T)
    }, index=symbols)
    
    return fundamentals


# ============================================================================
# Demo Function
# ============================================================================

def demo_factors():
    """Demo function to showcase factor calculations"""
    print("=" * 60)
    print("Academic Factors Demo")
    print("=" * 60)
    
    # Generate sample data
    from alpha_lab.us_academic.symbol_universe import SymbolUniverse
    from alpha_lab.us_academic.us_data_loader import USDataLoader
    
    universe = SymbolUniverse()
    loader = USDataLoader()
    
    # Get tech sector symbols
    symbols = universe.get_sector("Technology")[:5]
    print(f"\nSymbols: {symbols}")
    
    # Fetch price data
    print("\nFetching price data...")
    results = loader.fetch_multiple(symbols, "2023-01-01", "2023-12-31", delay=0.1)
    
    # Create price DataFrame
    prices = pd.DataFrame({symbol: df['close'] for symbol, df in results.items()})
    
    print(f"Price data shape: {prices.shape}")
    
    # Calculate factors
    print("\n" + "=" * 60)
    print("Factor Calculations")
    print("=" * 60)
    
    # 1. Momentum
    print("\n1. Momentum (12-month)")
    momentum = calc_momentum(prices, lookback=252, skip=21)
    print(momentum.sort_values(ascending=False))
    
    # 2. Value
    print("\n2. Value Factors")
    value = calc_value_factors(prices)
    print(value)
    
    # 3. Quality
    print("\n3. Quality Factors")
    quality = calc_quality_factors(symbols=symbols)
    print(quality)
    
    # 4. Size
    print("\n4. Size Factor")
    mock_fundamentals = _generate_mock_fundamentals(symbols)
    size = calc_size_factor(mock_fundamentals['MarketCap'])
    print(size.sort_values(ascending=False))
    
    # 5. Low Volatility
    print("\n5. Low Volatility Factor")
    low_vol = calc_low_vol_factor(prices, window=60)
    print(low_vol.sort_values(ascending=False))
    
    # Cross-sectional rankings
    print("\n" + "=" * 60)
    print("Cross-Sectional Rankings (Percentiles)")
    print("=" * 60)
    
    rankings = pd.DataFrame({
        'momentum_rank': rank_cross_sectional(momentum, ascending=False),
        'low_vol_rank': rank_cross_sectional(low_vol, ascending=False)
    })
    print(rankings.sort_values('momentum_rank', ascending=False))
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    demo_factors()
