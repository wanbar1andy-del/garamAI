# GARAM DGEFinal Concentrated Swing Engine (Champion Rule v2)

**Version**: v0.2 Spec (Profit-First Pivot)
**Objective**: Maximize Net Profit (CAGR +30%+) with aggressive concentration. Allow MDD up to -60%.
**Philosophy**: "Winner Takes All". Do not optimize for safety (low volatility) if it sacrifices Alpha.

## 1. Core Principles

### 1.1 Profit First (Aggressive)

* **Primary Goal**: CAGR >= 30%.
* **Risk Tolerance**: MDD -50% ~ -60% is acceptable.
* **Failure Definition**: Flat returns (±5%) are considered a FAILURE (no edge).

### 1.2 Concentration

* **Winner Takes All**: Capital is allocated to the highest scoring stock(s).
* **No Diversification for Safety**: Do not dilute the portfolio to reduce volatility.

### 1.3 Profile Separation

* **Max Drawdown**: <= **-60%**
* **Universe**: >= 30 Symbols (Real Data)

### 3.2 Objective Function

* Optimize for **Total Return**.
* Apply penalty only if MDD > -60%.
* Ignore Sharpe Ratio or Volatility metrics.

## 4. Implementation Plan

1. **Data**: Fetch 6-month minute data for Top 50 Liquid Stocks (Kiwoom).
2. **Layer 1**: Implement `Regime + Edge` Score Engine.
3. **Backtest**: Run `run_champion_rule_backtest.py` with v2 logic.
