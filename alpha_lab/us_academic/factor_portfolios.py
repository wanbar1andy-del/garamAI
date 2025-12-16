"""
Factor Portfolio Construction
Converts factor scores into investable portfolios with returns
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Union, Tuple
import logging

logger = logging.getLogger(__name__)


def build_factor_portfolio(
    prices: pd.DataFrame,
    scores: Union[pd.Series, pd.DataFrame],
    long_quantile: float = 0.8,
    short_quantile: float = 0.2,
    rebalance_freq: str = "M",
    long_only: bool = False,
    equal_weight: bool = True
) -> pd.Series:
    """
    Build factor portfolio from prices and factor scores
    
    Args:
        prices: DataFrame with prices (index=date, columns=symbols)
        scores: Series (single period) or DataFrame (time series) of factor scores
        long_quantile: Threshold for long positions (e.g., 0.8 = top 20%)
        short_quantile: Threshold for short positions (e.g., 0.2 = bottom 20%)
        rebalance_freq: Rebalancing frequency ('M'=monthly, 'Q'=quarterly, 'D'=daily)
        long_only: If True, only long positions (no shorts)
        equal_weight: If True, equal-weight; if False, score-weighted
    
    Returns:
        Series of portfolio returns indexed by date
    """
    if prices.empty:
        logger.warning("Empty prices DataFrame")
        return pd.Series(dtype=float)
    
    # Get rebalance dates
    rebalance_dates = pd.date_range(
        start=prices.index[0],
        end=prices.index[-1],
        freq=rebalance_freq
    )
    
    # Align rebalance dates to actual trading days
    rebalance_dates = [prices.index[prices.index >= d][0] if len(prices.index[prices.index >= d]) > 0 
                       else prices.index[-1] for d in rebalance_dates]
    rebalance_dates = sorted(set(rebalance_dates))
    
    logger.info(f"Building portfolio with {len(rebalance_dates)} rebalance periods")
    
    # Calculate daily returns
    returns = prices.pct_change()
    
    # Initialize portfolio returns
    portfolio_returns = []
    
    for i, rebal_date in enumerate(rebalance_dates[:-1]):
        # Get scores for this rebalance date
        if isinstance(scores, pd.Series):
            period_scores = scores
        else:
            # Find closest date in scores
            score_dates = scores.index[scores.index <= rebal_date]
            if len(score_dates) == 0:
                continue
            period_scores = scores.loc[score_dates[-1]]
        
        # Remove NaN scores
        valid_scores = period_scores.dropna()
        if len(valid_scores) == 0:
            continue
        
        # Select long and short positions
        long_threshold = valid_scores.quantile(long_quantile)
        long_symbols = valid_scores[valid_scores >= long_threshold].index.tolist()
        
        if long_only:
            short_symbols = []
        else:
            short_threshold = valid_scores.quantile(short_quantile)
            short_symbols = valid_scores[valid_scores <= short_threshold].index.tolist()
        
        # Calculate weights
        if equal_weight:
            long_weights = {s: 1.0 / len(long_symbols) if len(long_symbols) > 0 else 0 
                           for s in long_symbols}
            short_weights = {s: -1.0 / len(short_symbols) if len(short_symbols) > 0 else 0 
                            for s in short_symbols}
        else:
            # Score-weighted
            long_score_sum = valid_scores[long_symbols].sum() if len(long_symbols) > 0 else 0
            short_score_sum = valid_scores[short_symbols].sum() if len(short_symbols) > 0 else 0
            
            long_weights = {s: valid_scores[s] / long_score_sum if long_score_sum > 0 else 0 
                           for s in long_symbols}
            short_weights = {s: -valid_scores[s] / short_score_sum if short_score_sum > 0 else 0 
                            for s in short_symbols}
        
        # Combine weights
        weights = {**long_weights, **short_weights}
        
        # Get next rebalance date
        next_rebal_date = rebalance_dates[i + 1]
        
        # Calculate portfolio returns for this period
        period_dates = returns.index[(returns.index > rebal_date) & (returns.index <= next_rebal_date)]
        
        for date in period_dates:
            daily_return = 0.0
            for symbol, weight in weights.items():
                if symbol in returns.columns:
                    daily_return += weight * returns.loc[date, symbol]
            
            portfolio_returns.append((date, daily_return))
    
    # Convert to Series
    if len(portfolio_returns) == 0:
        return pd.Series(dtype=float)
    
    dates, rets = zip(*portfolio_returns)
    portfolio_series = pd.Series(rets, index=dates)
    
    # Remove NaN and inf
    portfolio_series = portfolio_series.replace([np.inf, -np.inf], np.nan).dropna()
    
    logger.info(f"Portfolio returns: {len(portfolio_series)} days, "
                f"mean={portfolio_series.mean():.4f}, std={portfolio_series.std():.4f}")
    
    return portfolio_series


def build_long_only_tilt(
    prices: pd.DataFrame,
    scores: pd.Series,
    rebalance_freq: str = "M",
    top_pct: float = 0.3
) -> pd.Series:
    """
    Build long-only portfolio with factor tilt
    
    Args:
        prices: DataFrame with prices
        scores: Series of factor scores
        rebalance_freq: Rebalancing frequency
        top_pct: Top percentage to hold (e.g., 0.3 = top 30%)
    
    Returns:
        Series of portfolio returns
    """
    quantile_threshold = 1.0 - top_pct
    
    return build_factor_portfolio(
        prices=prices,
        scores=scores,
        long_quantile=quantile_threshold,
        short_quantile=0.0,  # No shorts
        rebalance_freq=rebalance_freq,
        long_only=True,
        equal_weight=True
    )


def build_standard_factor_portfolios(
    prices: pd.DataFrame,
    symbols: List[str],
    start_date: str,
    end_date: str,
    rebalance_freq: str = "M",
    long_only: bool = False
) -> pd.DataFrame:
    """
    Build all 5 standard factor portfolios
    
    Args:
        prices: DataFrame with prices
        symbols: List of symbols in universe
        start_date: Start date for backtest
        end_date: End date for backtest
        rebalance_freq: Rebalancing frequency
        long_only: If True, build long-only portfolios
    
    Returns:
        DataFrame with columns: MOM, VAL, QLT, SIZE, LOWVOL
    """
    from alpha_lab.us_academic.academic_factors import (
        calc_momentum, calc_value_factors, calc_quality_factors,
        calc_size_factor, calc_low_vol_factor, _generate_mock_fundamentals
    )
    
    logger.info(f"Building standard factor portfolios for {len(symbols)} symbols")
    
    # Filter prices to date range
    prices_filtered = prices[(prices.index >= start_date) & (prices.index <= end_date)]
    
    if prices_filtered.empty:
        logger.warning("No price data in specified date range")
        return pd.DataFrame()
    
    # Calculate factors (using last available data)
    logger.info("Calculating factor scores...")
    
    # Momentum
    momentum_scores = calc_momentum(prices_filtered, lookback=252, skip=21)
    
    # Value
    value_factors = calc_value_factors(prices_filtered)
    value_scores = value_factors['value_pe'] if 'value_pe' in value_factors.columns else value_factors.iloc[:, 0]
    
    # Quality
    quality_factors = calc_quality_factors(symbols=symbols)
    quality_scores = quality_factors['quality_roe'] if 'quality_roe' in quality_factors.columns else quality_factors.iloc[:, 0]
    
    # Size
    mock_fundamentals = _generate_mock_fundamentals(symbols)
    size_scores = calc_size_factor(mock_fundamentals['MarketCap'])
    
    # Low Volatility
    low_vol_scores = calc_low_vol_factor(prices_filtered, window=60)
    
    # Build portfolios
    logger.info("Building factor portfolios...")
    
    factor_portfolios = {}
    
    if not momentum_scores.dropna().empty:
        factor_portfolios['MOM'] = build_factor_portfolio(
            prices_filtered, momentum_scores, long_only=long_only, rebalance_freq=rebalance_freq
        )
    
    if not value_scores.dropna().empty:
        factor_portfolios['VAL'] = build_factor_portfolio(
            prices_filtered, value_scores, long_only=long_only, rebalance_freq=rebalance_freq
        )
    
    if not quality_scores.dropna().empty:
        factor_portfolios['QLT'] = build_factor_portfolio(
            prices_filtered, quality_scores, long_only=long_only, rebalance_freq=rebalance_freq
        )
    
    if not size_scores.dropna().empty:
        factor_portfolios['SIZE'] = build_factor_portfolio(
            prices_filtered, size_scores, long_only=long_only, rebalance_freq=rebalance_freq
        )
    
    if not low_vol_scores.dropna().empty:
        factor_portfolios['LOWVOL'] = build_factor_portfolio(
            prices_filtered, low_vol_scores, long_only=long_only, rebalance_freq=rebalance_freq
        )
    
    # Combine into DataFrame
    if len(factor_portfolios) == 0:
        return pd.DataFrame()
    
    # Align all series to common index
    all_dates = sorted(set().union(*[set(s.index) for s in factor_portfolios.values()]))
    
    result = pd.DataFrame(index=all_dates)
    for name, series in factor_portfolios.items():
        result[name] = series
    
    logger.info(f"Built {len(factor_portfolios)} factor portfolios with {len(result)} days")
    
    return result


def calculate_performance_metrics(returns: pd.Series) -> Dict[str, float]:
    """
    Calculate performance metrics for a return series
    
    Args:
        returns: Series of daily returns
    
    Returns:
        Dictionary of performance metrics
    """
    if returns.empty or returns.isna().all():
        return {}
    
    # Remove NaN
    returns = returns.dropna()
    
    if len(returns) == 0:
        return {}
    
    # Total return
    total_return = (1 + returns).prod() - 1
    
    # Annualized return (assuming 252 trading days)
    n_days = len(returns)
    n_years = n_days / 252
    annualized_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0
    
    # Annualized volatility
    annualized_vol = returns.std() * np.sqrt(252)
    
    # Sharpe ratio (assuming 0% risk-free rate)
    sharpe_ratio = annualized_return / annualized_vol if annualized_vol > 0 else 0
    
    # Max drawdown
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Calmar ratio
    calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown < 0 else 0
    
    # Win rate
    win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0
    
    # Average win/loss
    wins = returns[returns > 0]
    losses = returns[returns < 0]
    avg_win = wins.mean() if len(wins) > 0 else 0
    avg_loss = losses.mean() if len(losses) > 0 else 0
    
    return {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'annualized_volatility': annualized_vol,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'calmar_ratio': calmar_ratio,
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'n_days': n_days
    }


def print_performance_summary(returns: pd.Series, name: str = "Portfolio"):
    """
    Print formatted performance summary
    
    Args:
        returns: Series of daily returns
        name: Portfolio name
    """
    metrics = calculate_performance_metrics(returns)
    
    if not metrics:
        print(f"\n{name}: No data")
        return
    
    print(f"\n{'='*60}")
    print(f"{name} Performance Summary")
    print(f"{'='*60}")
    print(f"Period: {returns.index[0].date()} to {returns.index[-1].date()}")
    print(f"Trading Days: {metrics['n_days']}")
    print(f"\nReturns:")
    print(f"  Total Return:       {metrics['total_return']:>10.2%}")
    print(f"  Annualized Return:  {metrics['annualized_return']:>10.2%}")
    print(f"  Annualized Vol:     {metrics['annualized_volatility']:>10.2%}")
    print(f"\nRisk-Adjusted:")
    print(f"  Sharpe Ratio:       {metrics['sharpe_ratio']:>10.2f}")
    print(f"  Max Drawdown:       {metrics['max_drawdown']:>10.2%}")
    print(f"  Calmar Ratio:       {metrics['calmar_ratio']:>10.2f}")
    print(f"\nWin/Loss:")
    print(f"  Win Rate:           {metrics['win_rate']:>10.2%}")
    print(f"  Avg Win:            {metrics['avg_win']:>10.4f}")
    print(f"  Avg Loss:           {metrics['avg_loss']:>10.4f}")


if __name__ == "__main__":
    # Demo
    import logging
    logging.basicConfig(level=logging.INFO)
    
    from alpha_lab.us_academic.symbol_universe import SymbolUniverse
    from alpha_lab.us_academic.us_data_loader import USDataLoader
    
    print("="*60)
    print("Factor Portfolio Demo")
    print("="*60)
    
    # Get universe
    universe = SymbolUniverse()
    symbols = universe.get_sector("Technology")[:10]
    print(f"\nUniverse: {symbols}")
    
    # Fetch data
    loader = USDataLoader()
    print("\nFetching price data...")
    results = loader.fetch_multiple(symbols, "2023-01-01", "2023-12-31", delay=0.1)
    
    if len(results) == 0:
        print("No data fetched, exiting demo")
    else:
        prices = pd.DataFrame({s: df['close'] for s, df in results.items()})
        print(f"Price data: {prices.shape}")
        
        # Build factor portfolios
        print("\nBuilding factor portfolios...")
        factor_returns = build_standard_factor_portfolios(
            prices, symbols, "2023-01-01", "2023-12-31", long_only=False
        )
        
        print(f"\nFactor portfolios built: {list(factor_returns.columns)}")
        
        # Print performance for each factor
        for factor in factor_returns.columns:
            if not factor_returns[factor].dropna().empty:
                print_performance_summary(factor_returns[factor], factor)
