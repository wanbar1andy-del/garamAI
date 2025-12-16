# scripts/verify_ssot.py
from pathlib import Path
import pandas as pd
import numpy as np
import sys
# Path hack
sys.path.append(str(Path(__file__).parents[1]))
from garam_core.reporting.report_writer import ReportWriter

class MockResult:
    def __init__(self):
        self.metric = {}
        self.trades = [
            {"id": 1, "entry_ts": pd.Timestamp.now(), "return_net": 0.05, "tags": ["TEST"]}
        ]
        times = pd.date_range("2024-01-01", periods=10, freq="1min")
        self.equity_curve = pd.Series(np.linspace(1.0, 1.1, 10), index=times)
        self.metrics = {
            "total_return": 0.10,
            "trades_count": 1,
            "cost_total": -0.01
        }

def test():
    rw = ReportWriter(Path("c:/garam/garam/garam_core"))
    mock = MockResult()
    
    # 1. Replay Report
    p = rw.write_replay_report(
        run_id="test_run_001",
        mode="TEST",
        symbol="005930",
        timeframe="1m",
        config={"signal_params": {"k": 1}},
        replay_result=mock,
        data_range={"bars": 10}
    )
    print(f"Replay Report Verification: {p.exists()}")
    
    # 2. Tuning Report
    p2 = rw.write_tuning_report(
        run_id="test_tuning_001",
        experiments=[{"name": "E1", "score": 10}],
        ranking=[],
        winner="E1",
        criteria={},
        config={}
    )
    print(f"Tuning Report Verification: {p2.exists()}")

if __name__ == "__main__":
    test()
