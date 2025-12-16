"""
Test Trading Accounting Module
Constant-notional test trading accounting and logging framework.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, NamedTuple
from enum import Enum
import pandas as pd
from datetime import datetime
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS

# --- Data Structures for Segmentation & Anomalies ---

class SegmentKey(NamedTuple):
    segment_type: str  # "DAY", "WEEK", "MONTH", "REGIME"
    value: str         # e.g. "2025-11-24", "2025-W48", "2025-11", "EAT"

class SegmentPnl(NamedTuple):
    key: SegmentKey
    realized_pnl: float
    pnl_balance_start: float
    pnl_balance_end: float
    num_trades: int
    max_drawdown: float  # within segment

class TradeExpectation(NamedTuple):
    trade_id: str
    expected_direction: str   # "LONG", "SHORT"
    expected_R_range: Tuple[float, float]  # e.g. (0.5, 3.0)
    expected_holding_period: int          # in bars
    expected_regime: str                  # "EAT", "HURT", "DEATH"
    notes: str = ""

class TradeOutcome(NamedTuple):
    trade_id: str
    realized_R: float
    actual_holding_period: int
    realized_pnl: float
    regime_at_entry: str
    regime_at_exit: str
    max_favorable_excursion_R: float  # MFE in R
    max_adverse_excursion_R: float    # MAE in R
    exit_reason: str = "UNKNOWN"

class AnomalyRecord(NamedTuple):
    trade_id: str
    anomaly_type: str         # "UNDERPERFORM", "OVERPERFORM", "HOLDING", "REGIME_DRIFT", ...
    expectation: TradeExpectation
    outcome: TradeOutcome
    root_cause: Optional[str] # "SLIPPAGE", "GAP", "API_ERROR", "UNKNOWN"

@dataclass
class EquityPoint:
    timestamp: datetime
    equity: float
    pnl_balance: float

# --- Core Test Account Class ---

class TestAccount:
    """
    Constant-notional test account for Garam.
    - base_capital: fixed 100,000,000 KRW (no compounding)
    - test_capital: always maintained at base_capital for simulation
    - pnl_balance: cumulative realized PnL (profits - losses)
    """
    
    def __init__(self, base_capital: float = 100_000_000):
        self.base_capital = base_capital
        self.test_capital = base_capital
        self.pnl_balance = 0.0
        self.realized_pnl = 0.0
        self.equity_history: List[EquityPoint] = []
        
        # Segment tracking
        self.segments: Dict[SegmentKey, SegmentPnl] = {}
        self.current_segment_pnls: Dict[SegmentKey, float] = {} # Accumulator for current segment
        
        # Anomaly tracking
        self.anomalies: List[AnomalyRecord] = []
        
        # Trade History
        self.trade_history = []
        
        # Initial state
        self._record_equity(datetime.now())

    def _record_equity(self, timestamp: datetime):
        self.equity_history.append(EquityPoint(
            timestamp=timestamp,
            equity=self.base_capital + self.pnl_balance,
            pnl_balance=self.pnl_balance
        ))

    def get_balance(self) -> float:
        """Get current total equity (Cash + PnL)"""
        return self.base_capital + self.pnl_balance

    def on_trade_closed(self, trade_pnl: float, timestamp: datetime, 
                       expectation: Optional[TradeExpectation] = None,
                       outcome: Optional[TradeOutcome] = None,
                       entry_time: Optional[datetime] = None,
                       symbol: str = "UNKNOWN"):
        """
        Process a closed trade.
        Supports legacy signature: on_trade_closed(trade_record: dict, symbol: str)
        """
        # Legacy Support
        if isinstance(trade_pnl, dict):
            record = trade_pnl
            sym = timestamp if isinstance(timestamp, str) else record.get('symbol', 'UNKNOWN')
            
            # Extract fields
            pnl = record.get('pnl', 0.0)
            ts = record.get('exit_time', record.get('timestamp', datetime.now()))
            entry = record.get('entry_time')
            
            # Update balances
            self.pnl_balance += pnl
            self.realized_pnl += pnl
            
            # Ensure symbol is set
            record['symbol'] = sym
            
            self.trade_history.append(record)
            self._record_equity(ts)
            return

        # Standard Logic
        # Update balances
        self.pnl_balance += trade_pnl
        self.realized_pnl += trade_pnl
        
        # Record trade
        self.trade_history.append({
            'trade_id': outcome.trade_id if outcome else "UNKNOWN",
            'symbol': symbol,
            'timestamp': timestamp, # Exit time
            'entry_time': entry_time,
            'pnl': trade_pnl,
            'realized_R': outcome.realized_R if outcome else 0.0,
            'holding_period': outcome.actual_holding_period if outcome else 0,
            'exit_reason': outcome.exit_reason if outcome else "UNKNOWN"
        })
        
        # Check for capital breach (if cumulative loss > base capital)
        # In constant notional, pnl_balance can go negative indefinitely, 
        # but if it goes below -base_capital, it means we lost everything.
        if self.pnl_balance < -self.base_capital:
            print(f"[WARNING] Capital Breach! PnL Balance: {self.pnl_balance:,.0f}")
            
        self._record_equity(timestamp)
        
        # Anomaly Detection
        if expectation and outcome:
            self._check_anomalies(expectation, outcome)

    def _check_anomalies(self, exp: TradeExpectation, out: TradeOutcome):
        """
        Check for deviations between expectation and outcome.
        """
        # 1. R-Multiple Deviation
        if out.realized_R < exp.expected_R_range[0] - 1.0:
            self.anomalies.append(AnomalyRecord(
                trade_id=exp.trade_id,
                anomaly_type="UNDERPERFORM",
                expectation=exp,
                outcome=out,
                root_cause="UNKNOWN" # Default
            ))
        elif out.realized_R > exp.expected_R_range[1] + 1.0:
             self.anomalies.append(AnomalyRecord(
                trade_id=exp.trade_id,
                anomaly_type="OVERPERFORM",
                expectation=exp,
                outcome=out,
                root_cause="UNKNOWN"
            ))
            
        # 2. Holding Period Deviation
        if out.actual_holding_period > 2 * exp.expected_holding_period:
             self.anomalies.append(AnomalyRecord(
                trade_id=exp.trade_id,
                anomaly_type="HOLDING_PROLONGED",
                expectation=exp,
                outcome=out,
                root_cause="UNKNOWN"
            ))
            
        # 3. Regime Drift
        if exp.expected_regime != out.regime_at_exit:
             self.anomalies.append(AnomalyRecord(
                trade_id=exp.trade_id,
                anomaly_type="REGIME_DRIFT",
                expectation=exp,
                outcome=out,
                root_cause="MARKET_CHANGE"
            ))

    def save_anomalies(self, strategy_id: str, run_id: str):
        """
        Save anomalies to JSONL file.
        """
        if not self.anomalies:
            return
            
        output_dir = PATHS.EXPERIMENTS_DIR / strategy_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / f"anomalies_{run_id}.jsonl"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for anomaly in self.anomalies:
                record = {
                    'trade_id': anomaly.trade_id,
                    'type': anomaly.anomaly_type,
                    'root_cause': anomaly.root_cause,
                    'expected_R': anomaly.expectation.expected_R_range,
                    'realized_R': anomaly.outcome.realized_R,
                    'expected_regime': anomaly.expectation.expected_regime,
                    'exit_regime': anomaly.outcome.regime_at_exit
                }
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
                
    def save_summary(self, strategy_id: str, run_id: str):
        """
        Save anomaly summary to Markdown.
        """
        output_dir = PATHS.EXPERIMENTS_DIR / strategy_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / f"anomaly_summary_{run_id}.md"
        
        unknown_count = sum(1 for a in self.anomalies if a.root_cause == "UNKNOWN")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Anomaly Summary for {strategy_id} (Run {run_id})\n\n")
            f.write(f"- Total Anomalies: {len(self.anomalies)}\n")
            f.write(f"- Unknown Causes: {unknown_count}\n\n")
            
            if unknown_count > 0:
                f.write("## Unknown Cause Cases (Top 5)\n")
                unknowns = [a for a in self.anomalies if a.root_cause == "UNKNOWN"][:5]
                for a in unknowns:
                    f.write(f"- Trade {a.trade_id}: {a.anomaly_type} (Exp R: {a.expectation.expected_R_range}, Real R: {a.outcome.realized_R})\n")

