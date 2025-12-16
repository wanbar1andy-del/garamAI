"""
Kiwoom Intraday Data Fetcher

Fetches intraday OHLCV data (5m, 15m, 60m) from Kiwoom API and stores in Parquet format.
Designed for KRX market hours (09:00-15:30 KST, no lunch break).

Usage:
    # Fetch recent 6 months (MVP target)
    python fetch_intraday_kiwoom.py --symbol 069500 --interval 15m --months 6
    
    # Backfill 2-3 years
    python fetch_intraday_kiwoom.py --symbol 069500 --interval 15m --start 2022-01-01 --end 2024-12-31
    
Output:
    garamdata/history/intraday/{symbol}/{interval}/{yyyymmdd}.parquet
    
    Columns: timestamp, open, high, low, close, volume
    Timezone: Asia/Seoul (explicit)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import time
import sys

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Kiwoom imports (placeholder - actual implementation depends on Kiwoom32 setup)
try:
    from garam.data.kiwoom_client import KiwoomClient  # To be implemented
except ImportError:
    print("Warning: KiwoomClient not found. Using stub.")
    KiwoomClient = None


class IntradayDataFetcher:
    """
    Fetches and stores intraday data from Kiwoom API.
    
    Key Features:
    - Session-aware: Only fetches KRX regular hours (09:00-15:30 KST)
    - Timezone-explicit: All timestamps in Asia/Seoul
    - Resume capability: Skips already-downloaded dates
    - Rate limit handling: Automatic backoff on API errors
    """
    
    def __init__(self, base_path: str = "g:/내 드라이브/garamdata/history/intraday"):
        self.base_path = Path(base_path)
        self.client = None  # Initialize in connect()
        
    def connect(self):
        """Initialize Kiwoom connection"""
        if KiwoomClient is None:
            raise ImportError("KiwoomClient not implemented yet")
        
        self.client = KiwoomClient()
        self.client.connect()
        print("Connected to Kiwoom API")
        
    def fetch_single_day(self, symbol: str, date: datetime, interval: str) -> pd.DataFrame:
        """
        Fetch intraday data for a single trading day.
        
        Args:
            symbol: Stock code (e.g., '069500' for KODEX 200)
            date: Trading date
            interval: '5m', '15m', or '60m'
            
        Returns:
            DataFrame with OHLCV data, timestamps in Asia/Seoul
        """
        # TODO: Implement actual Kiwoom API call
        # This is a placeholder structure
        
        # Convert interval to minutes
        interval_minutes = int(interval.replace('m', ''))
        
        # KRX session: 09:00-15:30
        session_start = date.replace(hour=9, minute=0, second=0, microsecond=0)
        session_end = date.replace(hour=15, minute=30, second=0, microsecond=0)
        
        # Generate expected timestamps
        timestamps = pd.date_range(
            start=session_start,
            end=session_end,
            freq=f'{interval_minutes}min',
            tz='Asia/Seoul'
        )
        
        # Placeholder: Call Kiwoom API here
        # data = self.client.fetch_intraday(symbol, date, interval)
        
        # For now, return empty DataFrame with correct structure
        df = pd.DataFrame({
            'timestamp': timestamps,
            'open': np.nan,
            'high': np.nan,
            'low': np.nan,
            'close': np.nan,
            'volume': 0
        })
        
        return df
    
    def save_parquet(self, df: pd.DataFrame, symbol: str, interval: str, date: datetime):
        """Save DataFrame to Parquet file"""
        output_dir = self.base_path / symbol / interval
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{date.strftime('%Y%m%d')}.parquet"
        df.to_parquet(output_file, index=False, compression='snappy')
        print(f"Saved: {output_file}")
    
    def fetch_range(self, symbol: str, start_date: datetime, end_date: datetime, interval: str):
        """
        Fetch data for a date range (MVP: 6 months, Full: 2-3 years)
        
        Args:
            symbol: Stock code
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            interval: '5m', '15m', or '60m'
        """
        current_date = start_date
        skipped = 0
        fetched = 0
        
        while current_date <= end_date:
            # Check if already exists
            output_file = self.base_path / symbol / interval / f"{current_date.strftime('%Y%m%d')}.parquet"
            
            if output_file.exists():
                print(f"Skip (exists): {current_date.date()}")
                skipped += 1
                current_date += timedelta(days=1)
                continue
            
            # Skip weekends (KRX closed)
            if current_date.weekday() >= 5:  # Saturday=5, Sunday=6
                current_date += timedelta(days=1)
                continue
            
            try:
                print(f"Fetching: {symbol} {interval} {current_date.date()}")
                df = self.fetch_single_day(symbol, current_date, interval)
                
                # Validate data
                if not df.empty and not df['close'].isna().all():
                    self.save_parquet(df, symbol, interval, current_date)
                    fetched += 1
                else:
                    print(f"  Warning: No data for {current_date.date()} (holiday or API issue)")
                
                # Rate limiting: ~1 request per second (Kiwoom conservative limit)
                time.sleep(1.0)
                
            except Exception as e:
                print(f"  Error fetching {current_date.date()}: {e}")
                # Backoff on error
                time.sleep(5.0)
            
            current_date += timedelta(days=1)
        
        print(f"\nDone. Fetched: {fetched}, Skipped: {skipped}")


def main():
    parser = argparse.ArgumentParser(description="Fetch intraday data from Kiwoom API")
    parser.add_argument('--symbol', required=True, help="Stock code (e.g., 069500)")
    parser.add_argument('--interval', choices=['5m', '15m', '60m'], default='15m', help="Bar interval")
    parser.add_argument('--months', type=int, help="Fetch recent N months (MVP mode)")
    parser.add_argument('--start', help="Start date YYYY-MM-DD (backfill mode)")
    parser.add_argument('--end', help="End date YYYY-MM-DD (backfill mode)")
    parser.add_argument('--base-path', default="g:/내 드라이브/garamdata/history/intraday", help="Output directory")
    
    args = parser.parse_args()
    
    # Determine date range
    if args.months:
        # MVP mode: Recent N months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.months * 30)
        print(f"Mode: Recent {args.months} months")
    elif args.start and args.end:
        # Backfill mode: Explicit range
        start_date = datetime.strptime(args.start, '%Y-%m-%d')
        end_date = datetime.strptime(args.end, '%Y-%m-%d')
        print(f"Mode: Backfill {args.start} to {args.end}")
    else:
        print("Error: Specify either --months or --start/--end")
        return
    
    # Fetch
    fetcher = IntradayDataFetcher(base_path=args.base_path)
    
    try:
        fetcher.connect()
        fetcher.fetch_range(args.symbol, start_date, end_date, args.interval)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
