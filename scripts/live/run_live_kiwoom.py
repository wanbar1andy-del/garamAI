# scripts/live/run_live_kiwoom.py
import sys
import threading
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from PyQt5.QtWidgets import QApplication

from garam_core.live.spec import LiveSpec
from garam_core.live.runner import LiveRunner
from garam_core.live.aggregator import MinuteBarAggregator
from garam_core.live.kiwoom_feed import KiwoomDataFeed
from garam_core.live.kiwoom_wrapper import KiwoomWrapper
from garam_core.live.kiwoom_gateway import KiwoomGateway
from garam_core.live.gateways.paper import PaperGateway  
# Note: Reuse CsvStore logic or similar
from scripts.live.run_live import CsvPortfolioStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", default="005930,000660")
    parser.add_argument("--equity", type=float, default=100_000_000.0)
    parser.add_argument("--log_dir", default=str(PROJECT_ROOT / "logs/live_kiwoom"))
    args = parser.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    # Define Spec
    spec = LiveSpec(
        symbols=symbols,
        timeframe="minute",
        bar_interval=1,
        base_equity=args.equity,
        max_leverage=1.0,
        max_mdd=0.20,
        max_daily_loss=0.05,
        max_consecutive_loss=5,
        topk=3,
        weight_mode="equal",
        log_dir=args.log_dir,
        tag="kiwoom_live_real",
    )

    # 1. PyQt App
    app = QApplication(sys.argv)

    # 2. Components
    aggregator = MinuteBarAggregator()
    feed = KiwoomDataFeed(aggregator)
    gateway = KiwoomGateway()
    store = CsvPortfolioStore(args.log_dir)

    # 3. Wrapper (The Bridge)
    wrapper = KiwoomWrapper(
        on_tick=feed._on_tick_from_kiwoom,
        on_position_update=gateway._on_position_update,
        on_cash_update=gateway._on_cash_update,
        app=app
    )
    # Inject wrapper into gateway
    gateway._kiwoom = wrapper

    # 4. Login & Init
    print("[INIT] Logging in...")
    wrapper.login()
    if not wrapper.connected:
        print("[ERROR] Login failed.")
        sys.exit(1)
    
    print("[INIT] Requesting Balance...")
    wrapper.request_account_balance()
    wrapper.request_deposit()
    
    # Register Realtime for symbols
    # '2000' is just an example screen number
    wrapper.register_realtime("2000", symbols)

    # 5. LiveRunner (Background Thread)
    runner = LiveRunner(spec=spec, feed=feed, gateway=gateway, store=store)
    
    t = threading.Thread(target=runner.run, daemon=True)
    t.start()

    print("[MAIN] Entering Event Loop...")
    app.exec_()
    
    store.flush()
    print("[MAIN] Exit.")

if __name__ == "__main__":
    main()
