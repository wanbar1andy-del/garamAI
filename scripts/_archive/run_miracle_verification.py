"""
Run Miracle Verification
Runs a 20-year backtest using the optimized Miracle Strategy Matrix.
Updated for Risk and Filter templates.
"""

import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS
from garam.research.regime.miracle_engine import (
    MiracleBacktester, Policy, Trade,
    ImmediateBreakoutEntry, ConfirmEntry,
    SignalReversalExit, FixedTargetExit, TimeStopExit,
    StandardRisk, VolatilityFilter, DGERisk
)

def run_verification():
    # 1. Load Config
    config_path = PATHS.CONFIG_DIR / "miracle_strategy_matrix.yaml"
    if not config_path.exists():
        print(f"Error: Config not found at {config_path}")
        return

    with open(config_path) as f:
        matrix = yaml.safe_load(f)
    
    print("Loaded Miracle Matrix:")
    for r, c in matrix.items():
        print(f"  {r}: {c['entry_template']} + {c['exit_templates']}")
        print(f"    Risk: {c.get('risk_template', 'Default')}")
        print(f"    Params: {c['params']}")

    # 2. Load Data
    data_path = Path("g:/내 드라이브/garamdata/history/labeled_KR_KOSPI_daily_20y.csv")
    if not data_path.exists():
        print("Data not found.")
        return

    df = pd.read_csv(data_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').sort_index()
    
    # Filter 2005+
    df = df[df.index >= '2005-01-01']
    
    # Pre-calculate Indicators
    for w in [3, 5, 10, 15, 20, 30, 40, 50, 60, 100, 120, 200]:
        df[f'ma_{w}'] = df['close'].rolling(window=w).mean()
        
    for w in [5, 10, 20, 40]:
        for std in [1.0, 1.5, 2.0, 2.5, 3.0]:
            ma = df['close'].rolling(window=w).mean()
            s = df['close'].rolling(window=w).std()
            df[f'upper_{w}_{std}'] = ma + (s * std)
            df[f'lower_{w}_{std}'] = ma - (s * std)

    # 3. Initialize Policies
    policies = {}
    for r, c in matrix.items():
        params = c['params']
        
        # Entry
        if c['entry_template'] == 'ImmediateBreakout':
            entry = ImmediateBreakoutEntry(params)
        elif c['entry_template'] == 'ConfirmEntry':
            entry = ConfirmEntry(params)
        else:
            continue
            
        # Exits
        exits = []
        for et in c['exit_templates']:
            if et == 'SignalReversal':
                exits.append(SignalReversalExit(params))
            elif et == 'FixedTarget':
                exits.append(FixedTargetExit(params))
            elif et == 'TimeStop':
                exits.append(TimeStopExit(params))
                
        # Filters
        filters = []
        for ft in c.get('filter_templates', []):
            if ft == 'VolatilityFilter':
                filters.append(VolatilityFilter(params))
                
        # Risk (Use DGE)
        # risk = StandardRisk(params)
        risk = DGERisk(params)
        
        policies[r] = Policy(entry, exits, filters, risk, theta_id=f"Miracle_{r}")

    # 4. Define Baseline Policies
    baseline_policies = {
        'GREEN': Policy(
            ImmediateBreakoutEntry({'strategy_type': 'TrendFollowing', 'window_fast': 10, 'window_slow': 20}), 
            [SignalReversalExit({})], 
            risk_logic=StandardRisk({'risk_per_trade': 0.01}), # Default 1% risk
            theta_id="Base_GREEN"
        ),
        'YELLOW': Policy(
            ImmediateBreakoutEntry({'strategy_type': 'TrendFollowing', 'window_fast': 5, 'window_slow': 50}), 
            [SignalReversalExit({})],
            risk_logic=StandardRisk({'risk_per_trade': 0.01}),
            theta_id="Base_YELLOW"
        ),
        'RED': Policy(
            ImmediateBreakoutEntry({'strategy_type': 'MeanReversion', 'window': 20, 'std_dev': 1.5}), 
            [SignalReversalExit({})],
            risk_logic=StandardRisk({'risk_per_trade': 0.01}),
            theta_id="Base_RED"
        )
    }

    # 5. Simulation Logic
    def run_regime_simulation(dataframe, policy_map):
        capital = 10000.0
        equity = capital
        active_trade = None
        context = {
            'daily_pnl': 0.0,
            'consecutive_losses': 0,
            'current_date': None,
            'hwm': 0.0
        }
        
        trades = []
        equity_curve = []
        
        for i in range(1, len(dataframe)):
            row = dataframe.iloc[i]
            prev_row = dataframe.iloc[i-1]
            timestamp = row.name
            regime = row['state']
            
            # Daily Reset
            if context['current_date'] != timestamp.date():
                context['current_date'] = timestamp.date()
                context['daily_pnl'] = 0.0
                context['consecutive_losses'] = 0
            
            policy = policy_map.get(regime)
            if not policy:
                equity_curve.append({'date': timestamp, 'equity': equity})
                continue
                
            if active_trade:
                # Mark to Market
                ret = (row['close'] - prev_row['close']) / prev_row['close']
                equity = equity * (1 + ret * active_trade.side)
                
                # Update HWM
                if 'hwm' not in context: context['hwm'] = active_trade.entry_price
                if active_trade.side == 1: context['hwm'] = max(context['hwm'], row['close'])
                else: context['hwm'] = min(context['hwm'], row['close'])
                
                should_exit = False
                reason = ""
                
                current_signal = policy.entry_logic.check_entry(row, prev_row, context)
                context['current_signal'] = current_signal
                
                for exit_logic in policy.exit_logics:
                    ex, r = exit_logic.check_exit(row, active_trade, context)
                    if ex:
                        should_exit = True
                        reason = r
                        break
                
                if should_exit:
                    pnl = (row['close'] - active_trade.entry_price) * active_trade.side
                    pnl_pct = pnl / active_trade.entry_price
                    
                    active_trade.exit_time = timestamp
                    active_trade.exit_price = row['close']
                    active_trade.pnl = pnl
                    active_trade.pnl_pct = pnl_pct
                    active_trade.duration = (timestamp - active_trade.entry_time).days
                    active_trade.exit_reason = reason
                    
                    trades.append(active_trade)
                    
                    # Update Risk Context
                    if pnl_pct < 0:
                        context['consecutive_losses'] += 1
                        context['daily_pnl'] += pnl_pct
                    else:
                        context['consecutive_losses'] = 0
                        context['daily_pnl'] += pnl_pct
                        
                    active_trade = None
                    
                    # Reversal Re-entry
                    if reason == "Signal Reversal" and current_signal != 0:
                        # Check Filters & Risk
                        allowed = True
                        for f in policy.filters:
                            if not f.check_filter(row, context):
                                allowed = False
                                break
                        if allowed and policy.risk_logic.check_risk_limits(context):
                             active_trade = Trade(
                                entry_time=timestamp,
                                entry_price=row['close'],
                                exit_time=pd.Timestamp.min,
                                exit_price=0.0,
                                side=current_signal,
                                pnl=0.0,
                                pnl_pct=0.0,
                                duration=0,
                                exit_reason="",
                                regime=regime,
                                theta_id=policy.theta_id,
                                entry_mode=policy.entry_logic.name,
                                exit_mode=",".join([e.name for e in policy.exit_logics]),
                                risk_mode=policy.risk_logic.name
                            )
            else:
                # Check Risk Limits
                if not policy.risk_logic.check_risk_limits(context):
                    equity_curve.append({'date': timestamp, 'equity': equity})
                    continue
                    
                # Check Filters
                allowed = True
                for f in policy.filters:
                    if not f.check_filter(row, context):
                        allowed = False
                        break
                if not allowed:
                    equity_curve.append({'date': timestamp, 'equity': equity})
                    continue

                signal = policy.entry_logic.check_entry(row, prev_row, context)
                if signal != 0:
                    active_trade = Trade(
                        entry_time=timestamp,
                        entry_price=row['close'],
                        exit_time=pd.Timestamp.min,
                        exit_price=0.0,
                        side=signal,
                        pnl=0.0,
                        pnl_pct=0.0,
                        duration=0,
                        exit_reason="",
                        regime=regime,
                        theta_id=policy.theta_id,
                        entry_mode=policy.entry_logic.name,
                        exit_mode=",".join([e.name for e in policy.exit_logics]),
                        risk_mode=policy.risk_logic.name
                    )
            
            equity_curve.append({'date': timestamp, 'equity': equity})
            
        return trades, equity_curve, equity

    print("\nRunning Miracle Simulation...")
    trades, equity_curve, equity = run_regime_simulation(df, policies)
    
    print("\nRunning Baseline Simulation...")
    b_trades, b_equity_curve, b_equity = run_regime_simulation(df, baseline_policies)

    # 6. Analysis
    print("\n" + "="*40)
    print("MIRACLE VERIFICATION RESULTS (Risk-Aware)")
    print("="*40)
    print(f"Final Equity : ${equity:,.0f}")
    print(f"Total Trades : {len(trades)}")
    
    print("\n" + "="*40)
    print("BASELINE COMPARISON")
    print("="*40)
    print(f"Baseline Equity: ${b_equity:,.0f}")
    print(f"Improvement    : {(equity - b_equity) / b_equity * 100:+.2f}%")
    
    # 7. Gap Analysis
    from garam.research.regime.trade_comparator import TradeComparator
    comparator = TradeComparator(b_trades, trades)
    report = comparator.generate_report()
    print("\n" + report)

if __name__ == "__main__":
    run_verification()
