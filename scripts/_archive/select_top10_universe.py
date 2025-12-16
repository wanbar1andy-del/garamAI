"""
Top 10 Universe Selection with Dead Symbol Rotation

Selects top 10 tradable symbols based on:
1. Liquidity (volume)
2. Volatility (ATR, daily range)
3. Dead Symbol Filter (removes inactive symbols)

Dead Symbol Criteria:
- 20-day avg DailyRangePct < 0.5%, OR
- Last 5 days consecutive DailyRangePct < 0.7%

This ensures "Top 10 기본 but swap out dead symbols" strategy.

Usage:
    python select_top10_universe.py --update-daily
    python select_top10_universe.py --backtest --date 20251126
    python select_top10_universe.py --show-current
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import json
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from garam.config import PATHS


class UniverseSelector:
    """
    Selects Top 10 trading universe with dead symbol rotation
    """
    
    def __init__(self, candidate_pool_size=50):
        self.candidate_pool_size = candidate_pool_size
        self.candidates = []
        self.top10 = []
        self.dead_symbols = []
        
    def load_candidate_pool(self):
        """
        Load candidate pool (30-50 symbols)
        
        Sources:
        - KOSPI 200 top by market cap
        - KOSDAQ 150 selected
        - Major ETFs (KODEX, TIGER series)
        """
        # Placeholder: In real implementation, load from:
        # - Kiwoom API market data
        # - Pre-configured YAML file
        # - Database
        
        # Example candidate pool
        self.candidates = [
            # KOSPI Blue Chips
            '005930',  # Samsung Electronics
            '000660',  # SK Hynix
            '035720',  # Kakao
            '005380',  # Hyundai Motor
            '051910',  # LG Chem
            '006400',  # Samsung SDI
            '035420',  # NAVER
            '068270',  # Celltrion
            '028260',  # Samsung C&T
            '012330',  # Hyundai Mobis
            
            # ETFs
            '069500',  # KODEX 200
            '102110',  # TIGER 200
            '122630',  # KODEX Leverage
            '114800',  # KODEX Inverse
            
            # Add more as needed...
        ]
        
        # In production, load from config
        candidates_file = PATHS.CONFIG_DIR / "universe_candidates.yaml"
        # if candidates_file.exists():
        #     with open(candidates_file, 'r') as f:
        #         config = yaml.safe_load(f)
        #         self.candidates = config.get('candidates', self.candidates)
        
        return self.candidates
    
    def calculate_symbol_metrics(self, symbol, lookback_days=20):
        """
        Calculate metrics for a single symbol
        
        Returns:
        - liquidity_score: Based on avg daily volume
        - volatility_score: Based on ATR and daily range
        - is_dead: Boolean, whether symbol is inactive
        """
        # Load symbol data (placeholder)
        # In production: load from Kiwoom data or database
        
        # Example structure
        try:
            # data_file = PATHS.DATA_ROOT / "history" / f"{symbol}_daily.csv"
            # df = pd.read_csv(data_file, parse_dates=['timestamp'])
            # df = df.tail(lookback_days)
            
            # For now, simulate with random data
            df = self._simulate_symbol_data(symbol, lookback_days)
            
            if df.empty:
                return None
            
            # 1. Daily Range % = (High - Low) / Close
            df['daily_range_pct'] = (df['high'] - df['low']) / df['close'] * 100
            
            # 2. ATR 15-bar % (simplified: use daily ATR as proxy)
            df['tr'] = df.apply(lambda row: max(
                row['high'] - row['low'],
                abs(row['high'] - row['close']),
                abs(row['low'] - row['close'])
            ), axis=1)
            df['atr'] = df['tr'].rolling(15).mean()
            df['atr_pct'] = df['atr'] / df['close'] * 100
            
            # 3. Volume (for liquidity)
            avg_volume = df['volume'].mean()
            avg_value = (df['close'] * df['volume']).mean()  # Daily turnover
            
            # 4. Check if "Dead"
            avg_range_20d = df['daily_range_pct'].mean()
            last_5_ranges = df['daily_range_pct'].tail(5)
            
            is_dead = (
                (avg_range_20d < 0.5) or  # 20D avg range < 0.5%
                (len(last_5_ranges) == 5 and all(last_5_ranges < 0.7))  # 5D consecutive < 0.7%
            )
            
            # 5. Scoring
            # Liquidity score: Higher volume = higher score
            liquidity_score = np.log10(avg_value + 1) if avg_value > 0 else 0
            
            # Volatility score: Higher ATR = higher score (good for intraday)
            volatility_score = df['atr_pct'].iloc[-1] if not df['atr_pct'].isna().all() else 0
            
            # Combined score
            combined_score = liquidity_score * 0.4 + volatility_score * 0.6
            
            return {
                'symbol': symbol,
                'avg_volume': avg_volume,
                'avg_value': avg_value,
                'avg_range_20d_pct': avg_range_20d,
                'atr_pct': df['atr_pct'].iloc[-1] if not df['atr_pct'].isna().all() else 0,
                'is_dead': is_dead,
                'liquidity_score': liquidity_score,
                'volatility_score': volatility_score,
                'combined_score': combined_score
            }
        
        except Exception as e:
            print(f"Error calculating metrics for {symbol}: {e}")
            return None
    
    def _simulate_symbol_data(self, symbol, days):
        """Simulate symbol data for testing (remove in production)"""
        # Generate random OHLCV data
        np.random.seed(int(symbol) if symbol.isdigit() else hash(symbol) % 2**31)
        
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        base_price = np.random.uniform(50000, 150000)
        
        # Simulate some symbols as "dead" (low volatility)
        is_dead_sim = (hash(symbol) % 5 == 0)  # 20% chance
        
        if is_dead_sim:
            volatility = 0.003  # 0.3% daily range
        else:
            volatility = np.random.uniform(0.01, 0.03)  # 1-3% daily range
        
        data = []
        for date in dates:
            close = base_price * (1 + np.random.normal(0, volatility))
            high = close * (1 + abs(np.random.normal(0, volatility * 0.5)))
            low = close * (1 - abs(np.random.normal(0, volatility * 0.5)))
            volume = np.random.uniform(1e6, 1e7)
            
            data.append({
                'timestamp': date,
                'open': close,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def select_top10(self):
        """
        Select Top 10 symbols
        
        Process:
        1. Calculate metrics for all candidates
        2. Filter out dead symbols
        3. Rank by combined score
        4. Select top 10
        """
        print("\n" + "="*70)
        print(" Top 10 Universe Selection with Dead Symbol Filter")
        print("="*70 + "\n")
        
        # Load candidates
        self.load_candidate_pool()
        print(f"📚 Candidate Pool: {len(self.candidates)} symbols\n")
        
        # Calculate metrics
        print("📊 Calculating symbol metrics...")
        metrics = []
        for symbol in self.candidates:
            metric = self.calculate_symbol_metrics(symbol)
            if metric:
                metrics.append(metric)
        
        df = pd.DataFrame(metrics)
        
        # Filter dead symbols
        active_symbols = df[~df['is_dead']].copy()
        dead_symbols = df[df['is_dead']].copy()
        
        self.dead_symbols = dead_symbols['symbol'].tolist()
        
        print(f"\n⚠️ Dead Symbols Filtered: {len(dead_symbols)}")
        if len(dead_symbols) > 0:
            print("   (20D avg range < 0.5% OR last 5D consecutive < 0.7%)")
            for _, row in dead_symbols.head(10).iterrows():
                print(f"   - {row['symbol']}: Range={row['avg_range_20d_pct']:.2f}%, ATR={row['atr_pct']:.2f}%")
        
        # Rank and select Top 10
        active_symbols = active_symbols.sort_values('combined_score', ascending=False)
        top10_df = active_symbols.head(10)
        
        self.top10 = top10_df['symbol'].tolist()
        
        print(f"\n✅ Top 10 Selected:")
        print(f"   (Ranked by: Liquidity 40% + Volatility 60%)\n")
        
        for i, (_, row) in enumerate(top10_df.iterrows(), 1):
            print(f"   {i:2}. {row['symbol']}")
            print(f"       Range: {row['avg_range_20d_pct']:.2f}% | ATR: {row['atr_pct']:.2f}% | Score: {row['combined_score']:.2f}")
        
        print("\n" + "="*70 + "\n")
        
        return self.top10
    
    def save_universe(self, output_file=None):
        """Save Top 10 universe to JSON"""
        if output_file is None:
            output_file = PATHS.CONFIG_DIR / "top10_universe.json"
        
        universe_data = {
            'generated_at': datetime.now().isoformat(),
            'top10': self.top10,
            'dead_symbols': self.dead_symbols,
            'candidate_pool_size': len(self.candidates)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(universe_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Universe saved to: {output_file}\n")
        
        return output_file


def main():
    parser = argparse.ArgumentParser(description="Select Top 10 trading universe")
    parser.add_argument('--update-daily', action='store_true', help='Update Top 10 for today')
    parser.add_argument('--backtest', action='store_true', help='Backtest mode (simulation)')
    parser.add_argument('--date', help='Date for backtest (YYYYMMDD)')
    parser.add_argument('--show-current', action='store_true', help='Show current Top 10')
    parser.add_argument('--candidate-pool-size', type=int, default=50, help='Size of candidate pool')
    
    args = parser.parse_args()
    
    selector = UniverseSelector(candidate_pool_size=args.candidate_pool_size)
    
    if args.show_current:
        # Load and show current universe
        universe_file = PATHS.CONFIG_DIR / "top10_universe.json"
        if universe_file.exists():
            with open(universe_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print("\n" + "="*70)
            print(" Current Top 10 Universe")
            print("="*70 + "\n")
            print(f"Generated: {data['generated_at']}")
            print(f"\nTop 10:")
            for i, symbol in enumerate(data['top10'], 1):
                print(f"   {i:2}. {symbol}")
            print("\n" + "="*70 + "\n")
        else:
            print("No universe file found. Run --update-daily first.")
    
    elif args.update_daily or args.backtest:
        # Select Top 10
        top10 = selector.select_top10()
        
        # Save
        selector.save_universe()
        
        print("✅ Next steps:")
        print("   1. Review Top 10 list above")
        print("   2. Use in DGE_ORB_Aggressive strategy")
        print(f"   3. Monitor dead symbols for rotation\n")
    
    else:
        print("Usage:")
        print("  --update-daily: Update Top 10 for today")
        print("  --show-current: Show current Top 10")
        print("  --backtest: Run in backtest mode")


if __name__ == "__main__":
    main()
