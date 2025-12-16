import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts.backtest.run_generic_backtest import run_backtest

if __name__ == "__main__":
    run_backtest("Pure_v2", "playbook_pure_v2.yaml")
