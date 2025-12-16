# US Factor Portfolio API Documentation

## Overview

The **US Factor Portfolio API** provides a robust framework for constructing, analyzing, and backtesting academic factor strategies in the US market. It bridges the gap between raw factor scores (from `academic_factors.py`) and investable portfolios.

## Key Components

### 1. Factor Portfolio Construction (`factor_portfolios.py`)

This module converts cross-sectional factor scores into daily portfolio returns.

#### `build_factor_portfolio`

Generic builder for long-short or long-only portfolios.

```python
def build_factor_portfolio(
    prices: pd.DataFrame,           # Price history (Date x Symbol)
    scores: pd.DataFrame,           # Factor scores (Date x Symbol)
    long_quantile: float = 0.8,     # Top 20%
    short_quantile: float = 0.2,    # Bottom 20%
    rebalance_freq: str = "M",      # Monthly rebalancing
    long_only: bool = False,        # Long-only mode
    equal_weight: bool = True       # Equal vs Score weighting
) -> pd.Series:
    """
    Constructs a factor portfolio and returns cumulative returns series.
    """
```

#### `build_standard_factor_portfolios`

Wrapper to build all 5 core academic factors at once.

```python
def build_standard_factor_portfolios(
    prices: pd.DataFrame,
    symbols: List[str],
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    Returns a DataFrame with columns: ['MOM', 'VAL', 'QLT', 'SIZE', 'LOWVOL']
    """
```

### 2. Performance Metrics

Built-in calculation of standard risk-adjusted metrics.

- **Sharpe Ratio**: Annualized Return / Annualized Volatility
- **Max Drawdown**: Maximum peak-to-trough decline
- **Calmar Ratio**: Annualized Return / Max Drawdown
- **Win Rate**: Percentage of positive trading days

### 3. BacktestEngine Integration (`strategies/`)

Integration with Garam's event-driven `BacktestEngine`.

#### `USMomentum121Strategy`

Implementation of the classic 12-1 Month Momentum strategy.

- **Lookback**: 12 months (252 days)
- **Skip**: 1 month (21 days) to avoid short-term reversal
- **Rebalance**: Monthly
- **Weighting**: Equal-weight Long-Short (Net Zero)

## Usage Examples

### Example 1: Building a Momentum Portfolio

```python
from alpha_lab.us_academic import USDataLoader, SymbolUniverse
from alpha_lab.us_academic.academic_factors import calc_momentum
from alpha_lab.us_academic.factor_portfolios import build_factor_portfolio

# 1. Load Data
loader = USDataLoader()
universe = SymbolUniverse()
symbols = universe.get_sp500()
prices = loader.fetch_multiple(symbols, "2020-01-01", "2023-12-31")

# 2. Calculate Scores
scores = calc_momentum(prices, lookback=252, skip=21)

# 3. Build Portfolio
returns = build_factor_portfolio(prices, scores, long_only=False)

# 4. Analyze
print(f"Sharpe Ratio: {calculate_sharpe(returns):.2f}")
```

### Example 2: Running a Backtest

```python
from alpha_lab.us_academic.strategies.us_mom_12_1 import USMomentum121Strategy

# 1. Initialize Strategy
strategy = USMomentum121Strategy()

# 2. Run Backtest
results = strategy.backtest(prices, "2020-01-01", "2023-12-31")

# 3. View Results
print(results['cumulative'].tail())
```

## Design Decisions

1. **No Look-Ahead Bias**: Rebalancing uses scores from `t-1`.
2. **Robustness**: Handles missing data and NaN scores gracefully.
3. **Modularity**: Factor calculation is separated from portfolio construction.
4. **Testing**: Verified with 100% test coverage (`test_factor_portfolios.py`, `test_factor_backtest.py`).

## Future Roadmap

- **Real Fundamental Data**: Replace mock data for Value/Quality factors.
- **Transaction Costs**: Integrate slippage and commission models.
- **Multi-Factor Optimization**: Combine factors using Mean-Variance or Risk Parity.
