"""
US Momentum 12-1 Strategy
Cross-sectional momentum strategy using 12-month returns, skipping recent 1 month
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class USMomentum121Strategy:
    """
    US Momentum 12-1 Strategy
    
    Methodology:
    - Calculate 12-month total returns, skipping the most recent month
    - Rank stocks cross-sectionally
    - Long top 20%, short bottom 20%
    - Monthly rebalancing
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize strategy
        
        Args:
            config: Strategy configuration
                - lookback_months: Lookback period (default: 12)
                - skip_months: Skip recent months (default: 1)
                - long_quantile: Long threshold (default: 0.8)
                - short_quantile: Short threshold (default: 0.2)
                - rebalance_freq: Rebalancing frequency (default: 'M')
        """
        self.config = config or {}
        
        # Strategy parameters
        self.lookback_months = self.config.get('lookback_months', 12)
        self.skip_months = self.config.get('skip_months', 1)
        self.long_quantile = self.config.get('long_quantile', 0.8)
        self.short_quantile = self.config.get('short_quantile', 0.2)
        self.rebalance_freq = self.config.get('rebalance_freq', 'M')
        
        # Convert months to trading days (approx 21 days per month)
        self.lookback_days = self.lookback_months * 21
        self.skip_days = self.skip_months * 21
        
        logger.info(f"Initialized US Momentum 12-1 Strategy: "
                   f"lookback={self.lookback_months}m, skip={self.skip_months}m")
    
    def generate_signals(
        self,
        prices: pd.DataFrame,
        as_of_date: Optional[pd.Timestamp] = None
    ) -> pd.Series:
        """
        Generate momentum signals for given date
        
        Args:
            prices: DataFrame with prices (index=date, columns=symbols)
            as_of_date: Date to generate signals for (default: last date)
        
        Returns:
            Series of signals (-1 to 1) for each symbol
        """
        from alpha_lab.us_academic.academic_factors import calc_momentum, rank_cross_sectional
        
        if as_of_date is None:
            as_of_date = prices.index[-1]
        
        # Filter prices up to as_of_date
        prices_filtered = prices[prices.index <= as_of_date]
        
        if len(prices_filtered) < self.lookback_days + self.skip_days:
            logger.warning(f"Insufficient data for momentum calculation at {as_of_date}")
            return pd.Series(dtype=float)
        
        # Calculate momentum scores
        momentum_scores = calc_momentum(
            prices_filtered,
            lookback=self.lookback_days,
            skip=self.skip_days
        )
        
        # Remove NaN
        valid_scores = momentum_scores.dropna()
        
        if len(valid_scores) == 0:
            return pd.Series(dtype=float)
        
        # Generate signals based on quantiles
        signals = pd.Series(0.0, index=valid_scores.index)
        
        # Long positions (top quantile)
        long_threshold = valid_scores.quantile(self.long_quantile)
        long_mask = valid_scores >= long_threshold
        signals[long_mask] = 1.0
        
        # Short positions (bottom quantile)
        short_threshold = valid_scores.quantile(self.short_quantile)
        short_mask = valid_scores <= short_threshold
        signals[short_mask] = -1.0
        
        logger.debug(f"Generated signals for {as_of_date}: "
                    f"{long_mask.sum()} longs, {short_mask.sum()} shorts")
        
        return signals
    
    def generate_weights(
        self,
        signals: pd.Series,
        equal_weight: bool = True
    ) -> pd.Series:
        """
        Convert signals to position weights
        
        Args:
            signals: Series of signals (-1, 0, 1)
            equal_weight: If True, equal-weight; if False, signal-weighted
        
        Returns:
            Series of weights (sum to 0 for long-short)
        """
        if signals.empty:
            return pd.Series(dtype=float)
        
        # Separate long and short
        long_signals = signals[signals > 0]
        short_signals = signals[signals < 0]
        
        weights = pd.Series(0.0, index=signals.index)
        
        if equal_weight:
            # Equal-weight within each leg
            if len(long_signals) > 0:
                weights[long_signals.index] = 1.0 / len(long_signals)
            if len(short_signals) > 0:
                weights[short_signals.index] = -1.0 / len(short_signals)
        else:
            # Signal-weighted
            long_sum = long_signals.sum()
            short_sum = short_signals.abs().sum()
            
            if long_sum > 0:
                weights[long_signals.index] = long_signals / long_sum
            if short_sum > 0:
                weights[short_signals.index] = -short_signals.abs() / short_sum
        
        return weights
    
    def backtest(
        self,
        prices: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Run backtest on historical data
        
        Args:
            prices: DataFrame with prices
            start_date: Start date for backtest
            end_date: End date for backtest
        
        Returns:
            DataFrame with backtest results (returns, positions, etc.)
        """
        from alpha_lab.us_academic.factor_portfolios import (
            build_factor_portfolio,
            calculate_performance_metrics
        )
        from alpha_lab.us_academic.academic_factors import calc_momentum
        
        # Filter date range
        if start_date:
            prices = prices[prices.index >= start_date]
        if end_date:
            prices = prices[prices.index <= end_date]
        
        logger.info(f"Running backtest from {prices.index[0]} to {prices.index[-1]}")
        
        # Calculate momentum scores
        momentum_scores = calc_momentum(
            prices,
            lookback=self.lookback_days,
            skip=self.skip_days
        )
        
        # Build portfolio
        portfolio_returns = build_factor_portfolio(
            prices=prices,
            scores=momentum_scores,
            long_quantile=self.long_quantile,
            short_quantile=self.short_quantile,
            rebalance_freq=self.rebalance_freq,
            long_only=False,
            equal_weight=True
        )
        
        # Calculate performance metrics
        metrics = calculate_performance_metrics(portfolio_returns)
        
        # Create results DataFrame
        results = pd.DataFrame({
            'returns': portfolio_returns,
            'cumulative': (1 + portfolio_returns).cumprod()
        })
        
        # Add metrics as attributes
        results.attrs['metrics'] = metrics
        
        logger.info(f"Backtest complete: {len(portfolio_returns)} days, "
                   f"Sharpe={metrics.get('sharpe_ratio', 0):.2f}")
        
        return results


def generate_us_mom_12_1_signal(
    spec: Dict[str, Any],
    data_bundle: Any,
    as_of_date: pd.Timestamp
) -> pd.Series:
    """
    Signal generator function for BacktestEngine integration
    
    Args:
        spec: Strategy specification
        data_bundle: Data bundle with prices and other data
        as_of_date: Date to generate signals for
    
    Returns:
        Series of signals for each symbol
    """
    # Extract prices from data bundle
    if hasattr(data_bundle, 'get_prices'):
        prices = data_bundle.get_prices(spec.get('universe'), as_of_date)
    elif hasattr(data_bundle, 'prices'):
        prices = data_bundle.prices
    else:
        # Assume data_bundle is the prices DataFrame
        prices = data_bundle
    
    # Create strategy instance
    strategy = USMomentum121Strategy(spec.get('config', {}))
    
    # Generate signals
    signals = strategy.generate_signals(prices, as_of_date)
    
    return signals


if __name__ == "__main__":
    # Demo
    import logging
    logging.basicConfig(level=logging.INFO)
    
    from alpha_lab.us_academic.symbol_universe import SymbolUniverse
    from alpha_lab.us_academic.us_data_loader import USDataLoader
    from alpha_lab.us_academic.factor_portfolios import print_performance_summary
    
    print("="*60)
    print("US Momentum 12-1 Strategy Demo")
    print("="*60)
    
    # Get universe
    universe = SymbolUniverse()
    symbols = universe.get_sector("Technology")[:10]
    print(f"\nUniverse: {symbols}")
    
    # Fetch data
    loader = USDataLoader()
    print("\nFetching price data...")
    results = loader.fetch_multiple(symbols, "2023-01-01", "2023-12-31", delay=0.1)
    
    if len(results) > 0:
        prices = pd.DataFrame({s: df['close'] for s, df in results.items()})
        print(f"Price data: {prices.shape}")
        
        # Create strategy
        strategy = USMomentum121Strategy()
        
        # Run backtest
        print("\nRunning backtest...")
        results_df = strategy.backtest(prices, "2023-01-01", "2023-12-31")
        
        # Print performance
        print_performance_summary(results_df['returns'], "US Momentum 12-1")
        
        # Show final cumulative return
        final_cum_return = results_df['cumulative'].iloc[-1] - 1
        print(f"\nFinal Cumulative Return: {final_cum_return:.2%}")
