# Garam Trading AI – Comprehensive Development Whitepaper v0.1

## 1. Document Overview

### Purpose

Integrate Garam project's goals, design philosophy, system architecture, strategies, risk management, and development roadmap into a single document.
Document the process of creating an AI trading system capable of **real account operation**, not just "research".

### Target Audience

- **Internal**: Strategy Designers, Quants, Developers, Risk Managers.
- **External (Future)**: Partners, Potential Investors, Strategy Validators.

### Scope

Full-stack coverage including Korean Short-term/Swing + US Academic Factor Strategies + Portfolio/Regime Engines.

## 2. Garam Vision & Key KPIs

### Vision

**"An AI Trading OS that maximizes returns without fear within known risks, and automatically defends the account against unknown risks (unpredicted volatility)."**

### Key Objectives

- **Daily Return Target Zone**:
  - Realistic Target: 0.1~0.4% daily.
  - High Upside Scenario: >1% daily (handled by separate modules).
- **10-Year Backtest Criteria**:
  - CAGR, Max Drawdown, Sharpe/Sortino, Win Rate, Expectancy (R-Multiple).
- **Real Account Mode**:
  - Monthly negative months allowance / Maximum allowable drawdown specified.

## 3. Design Principles

1. **Profit First + Verification First**: Features that don't generate profit are not maintained. Must pass CSV/Replay → Shadow → Small Live steps.
2. **Risk Before Return**: Profit optimization comes *after* "account destruction prevention" is secured.
3. **Modularity**: Loose coupling between Strategy / Routing / Execution / Risk / Gateway.
4. **Observability**: Logs/Tags/Metadata for every decision.
5. **Data Hygiene**: Standardized time-series processing (Timezone, Resampling, Missing/Outlier handling).
6. **Conservative Cost Model**: Overestimate fees, taxes, and slippage in tests.
7. **Crowding Sensitivity**: Automatic deleveraging if ACI decile performance deteriorates.
8. **Simple Defaults**: Default parameters are always conservative; advanced options are flagged.
9. **Rollback Capability**: Every release must be immediately rollback-able.
10. **Security/Compliance**: Keys/Tokens/Account Info managed via .env/secrets, least privilege.

## 4. Research Basis (Academic & Practical)

- **Factor Investing**: Fama–French 3/5 Factors (Market, Size, Value, Profitability, Investment). Momentum, Low Vol, Quality have independent explanatory power.
- **Momentum Strategy**: Jegadeesh–Titman 12-1 Cross-sectional Momentum.
- **Position Sizing & R-Multiple**: Van Tharp's theory - Success depends more on Exit and Position Sizing than Entry.
- **Kelly & Fractional Kelly**: Use Fractional Kelly (1/2, 1/4) to manage drawdown while maximizing long-term growth.
- **Regime Switching**: HMM/Threshold models to divide market into Bull/Bear, High/Low Volatility.

**Garam applies these researches directly to Live Strategies, Regime Filters, and Exit/Size Engines.**

## 5. System Architecture Overview

### 5.1 High-Level Components

- **Data Lake**: Local + Google Drive based Time-series/Fundamental storage.
- **Feature Factory**: Trend, Volatility, News/Fear, Investor Flow, Microstructure features.
- **Alpha Lab**: Backtest Engine + Academic Factor Library + Factor Portfolio API.
- **Surfing Brain**: Market State Classification (MarketStateAgent), Regime Detection, Strategy ON/OFF/Sizing.
- **Execution Layer**: RealBrokerSim + Real Broker (Kiwoom API, etc.) Routing.
- **Risk & SafeGuard**: Risk Limits, Trading Mode, Kill-Switch, Account Protection.
- **GaramUI**: Dashboard, Monitoring, Real-time/Shadow/Optimization Visualization.
- **Dev/AutoDev Layer**: Antigravity/AgentKit based Code Generation/Test/Deploy Flow.

## 6. Data Layer & Data Lake

### 6.1 Data Sources

- **Korea**: Kiwoom OpenAPI+ (Real-time Tick/Min/Daily), Past CSV/Replay Packs.
- **US**: Yahoo Finance (Public Source), Future Fundamental API (Alpha Vantage, etc.).

### 6.2 Structure

- **Local Root**: `C:\garam\garam\GARAM_Data`
- **Google Drive**: `g:\My Drive\garamdata` (symbols, daily, experiments)
- **Common Format**: Symbol, Date/Time, OHLCV, Market Cap, Sector.

### 6.3 Data Hygiene Standards

- Timezone Consistency (KST/UTC).
- Resampling Rules (Tick -> Min -> Daily).
- Integrated Missing/Outlier Handling Utilities.

## 7. Feature Factory

- **Basic Features**: MA, MACD, ADX, ATR, Bollinger Bands, Realized Volatility, News Sentiment.
- **Regime Features**: Market Volatility, Correlation, Breadth, Gap/Large Candle Frequency, News Fear Score.
- **Status**: Core FeatureFactory completed and verified (reusable for KR/US).

## 8. Alpha Lab & US Academic Alpha

### 8.1 Academic Factor Library v1 (Completed)

- **File**: `alpha_lab/us_academic/academic_factors.py`
- **Factors**: Momentum (12-1), Value (Mock Fundamentals), Quality, Size, Low Volatility.
- **Utils**: Cross-sectional ranking, Composite factor.
- **Testing**: `test_academic_factors.py` (8/8 Passed).

### 8.2 Factor Portfolio API (In Progress)

- **Purpose**: Convert factor scores to investable portfolio return series.
- **Design**: `build_factor_portfolio`, `build_standard_factor_portfolios`.
- **Status**: API designed and implemented.

### 8.3 Backtest Engine Integration

- **Goal**: Integrate US Factor Strategies (e.g., US_MOM_12_1) into Garam BacktestEngine.
- **Status**: Completed Integration and Verification.

## 9. Regime Engine (Market State / Death vs Eat vs Hurt)

### 9.1 Regime Definitions

- **GREEN (Eat Regime)**: Positive expectancy, controllable drawdown.
- **YELLOW (Hurt Regime)**: High volatility/whipsaw, but account survives.
- **RED (Death Regime)**: Worst 1-5% drawdown patterns in 10-year backtest.

### 9.2 Detection Logic

- **Features**: Volatility, Correlation, Breadth, News Fear, Strategy Internal State.
- **Models**: v1 (Rule-based + Simple ML), v2 (HMM/Clustering).

### 9.3 Real-time Application

- **Surfing Brain**: Calculates `market_regime` + `p_death`.
- **Action**: Adjust Strategy ON/OFF, Position Size, Exit Intensity.

## 10. Exit & Position Sizing Engine

### 10.1 ExitEngine

- **Components**: Initial Stop (ATR), Profit Target (R-Multiple), Trailing Stop, Time Stop.
- **Logging**: Entry/Exit, R, MFE/MAE, Holding Time, Exit Rule.

### 10.2 Regime-based Policy

- **Green**: Far TP, Loose TSL, Large Size.
- **Yellow**: Medium TP/TSL, Half Size.
- **Red**: No Entry, Tight TSL, Rapid Reduction.
- **Sizing**: Fractional Kelly (0.25~0.5) based on strategy expectancy/variance.

## 11. Strategy Catalog

### 11.1 KR Short-term/Scalping

- **Universe**: Top N Trading Value (20~100).
- **Entry**: Momentum, VWAP Breakout, Gap/Reversal, News Spike.
- **Exit**: Linked to Regime + ExitEngine.

### 11.2 US Factor Swing

- **Universe**: S&P 500 (or subset).
- **Entry**: Multi-factor Score (Mom + Val + Qlt + LowVol).
- **Regime**: Global Macro + Factor Return based Regime Filter.

### 11.3 Hedge & Portfolio

- **Hedge**: Partial hedge using KOSPI200 Futures/ETF.

## 12. Risk & Account Protection

- **SafeGuard / LIVE_ACCOUNT_PROTECTION**: Kill-switch for max loss/anomalies.
- **Configuration**: `risk_limits.json`, `trading_mode.json`.
- **Future**: Regime-based Risk Profiles.

## 13. Operations & Monitoring (GaramUI)

- **Features**: Login/Out, Real-time Account, Shadow/Sim/Opt Visualization.
- **Dashboard**: Factor Return Curves, Factor Exposure, Regime History.

## 14. Development Process & AutoDev

- **Tools**: Antigravity + AgentKit.
- **Pipeline**: Code Indexing -> AutoDev Loop -> Test -> Deploy.
- **Tests**: `validate_garam.py`, `test_components.py`, `test_integration.py`.
- **Deployment**: Code Change -> Test Pass -> Shadow -> Small Live -> Full Size.

## 15. Roadmap Summary

### Short-term (3 Months)

- Factor Portfolio API & BacktestEngine Integration (Done).
- Regime Engine v1 (Rule + Simple ML) -> Surfing Brain Integration.
- ExitEngine/Position Sizing Sweep Backtest.

### Mid-term (6-12 Months)

- US Real Data/Fundamental API -> Real Value/Quality Factors.
- KR Short-term Strategy v1 -> Small Live Operation.
- GaramUI Visualization (Regime, Exit, Factor).

### Long-term (1 Year+)

- Regime Engine v2 (HMM/Hybrid ML).
- AI-based Exit Policy Tuning (RL).
- Multi-asset Expansion (Bond/Commodity/FX).
