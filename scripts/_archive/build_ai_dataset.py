import argparse
from pathlib import Path
import pandas as pd
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from garam.research.ai.dataset_builder import DatasetConfig, AIDatasetBuilder
from garam.config import PATHS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--output", required=True, help="output parquet path")
    args = parser.parse_args()

    # Use paths from config if available, else default
    signal_dir = PATHS.LOGS_DIR / "signals"
    price_dir = PATHS.DATA_DIR / "kr" / "realtime" / "1m" # Or wherever 1m data is

    config = DatasetConfig(
        signal_log_dir=signal_dir,
        price_data_root=price_dir,
        universe=[],  # TODO: Load from universe file
    )

    logger.info(f"Building dataset from {args.start} to {args.end}...")
    logger.info(f"Signals Dir: {signal_dir}")
    logger.info(f"Price Dir: {price_dir}")

    builder = AIDatasetBuilder(config)
    df = builder.build(args.start, args.end)
    
    if df.empty:
        logger.warning("No data built. Check date range or logs.")
        return

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path)
    logger.info(f"Saved dataset: {out_path} rows={len(df)}")

if __name__ == "__main__":
    main()
