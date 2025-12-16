# Multi-Alpha Engine Specification

## 1. Overview

The **Multi-Alpha Engine** transitions GARAM from a single-strategy approach to a consensus-based system.

- **Alpha**: Treated as a dynamic "State of Winning Probability" (0 to 100).
- **Engine**: Manages multiple alpha sources, scores them independently, and aggregates them based on the current Market Regime.

## 2. AlphaModule Interface

All alpha modules must inherit from `BaseAlpha` and implement the following:

### Input

- **symbol**: Target stock symbol.
- **market_data**: DataFrame containing OHLCV history (Daily/Minute).
- **regime** (Optional): Current market regime (e.g., `R3_UP_BOX`).

### Output

#### 1. Score (`calculate_score`)

A normalized float value representing the "winning probability" from this alpha's perspective.

- **Range**: `0.0` to `100.0`
- **Interpretation**:
  - `80 ~ 100`: **Strong Buy** / High Probability
  - `60 ~ 79`: **Buy** / Positive
  - `40 ~ 59`: **Neutral** / Hold
  - `20 ~ 39`: **Sell** / Negative
  - `0 ~ 19`: **Strong Sell** / Avoid

#### 2. Signal (`get_signal`)

A structured dictionary for discrete decision making.

```json
{
    "action": "BUY" | "SELL" | "FLAT",
    "confidence": 0.0 to 1.0,
    "metadata": { ... }
}
```

## 3. Alpha Catalog Schema (`alpha_catalog.yaml`)

Defines the metadata and configuration for each alpha.

```yaml
- id: A1_trend_mom_6m          # Unique ID
  name: "6M Trend Momentum"    # Display Name
  module: "a1_trend_mom"       # Python Module Name (garam.alphas.a1_trend_mom)
  class: "A1TrendMomentum"     # Class Name
  type: "Trend"                # Trend, MeanRev, Volatility, Event
  time_horizon: "6M"           # Timeframe (Intraday, Daily, Weekly, 6M)
  regime_suitability:          # Weighting per Regime (0.0 to 1.0)
    R1_STRONG_UP: 1.0
    R2_UP: 0.8
    R3_UP_BOX: 0.2
    R4_BOX: 0.0
    R5_DOWN_BOX: 0.0
    R6_DOWN: 0.0
    R7_CRASH: 0.0
  enabled: true                # Master Switch
```

## 4. Alpha Aggregator Logic

The `AlphaAggregator` combines scores from active alphas.

**Formula:**
$$ FinalScore = \frac{\sum (Score_i \times Weight_{regime, i})}{\sum Weight_{regime, i}} $$

1. **Load**: Identify active alphas from Catalog.
2. **Compute**: Call `calculate_score()` for each alpha.
3. **Weight**: Look up `regime_suitability` for the current System Regime.
4. **Aggregate**: Calculate weighted average.

## 5. Strategy Integration

The Final Score determines the portfolio action.

- **Entry Rule**: Final Score > `70` (Configurable)
- **Exit Rule**: Final Score < `40` (Configurable)
- **Sizing**: Position size can be scaled by `(Final Score - 50) / 50`.
