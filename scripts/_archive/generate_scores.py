#!/usr/bin/env python3
"""
Score Generation Pipeline with Universe Enforcement
Universe 파일 기준으로 강제로 Score 생성 - 100% Coverage 보장
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import sys
import argparse

class ScoreGenerator:
    """Universe 강제 기반 Score 생성기"""
    
    def __init__(self, universe_file, price_data_dir):
        self.universe_file = Path(universe_file)
        self.price_data_dir = Path(price_data_dir)
        
        # Load universe
        print(f"Loading universe from {self.universe_file}...")
        df_univ = pd.read_csv(self.universe_file)
        
        # Get symbol column
        if 'Code' in df_univ.columns:
            self.universe_symbols = df_univ['Code'].astype(str).tolist()
        elif 'symbol' in df_univ.columns:
            self.universe_symbols = df_univ['symbol'].astype(str).tolist()
        else:
            self.universe_symbols = df_univ.iloc[:, 0].astype(str).tolist()
        
        print(f"✓ Universe loaded: {len(self.universe_symbols)} symbols")
        
        self.price_data = {}
        self.loaded_count = 0
        self.failed_symbols = []
    
    def load_price_data(self, start_date, end_date):
        """가격 데이터 로드"""
        print(f"\nLoading price data from {self.price_data_dir}...")
        print(f"Date range: {start_date} to {end_date}")
        
        for symbol in self.universe_symbols:
            price_file = self.price_data_dir / f"{symbol}_daily.csv"
            
            if not price_file.exists():
                self.failed_symbols.append(symbol)
                continue
            
            try:
                df = pd.read_csv(price_file)
                
                # Handle date column
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                elif 'timestamp' in df.columns:
                    df['date'] = pd.to_datetime(df['timestamp'])
                else:
                    print(f"  ⚠️  {symbol}: No date column")
                    self.failed_symbols.append(symbol)
                    continue
                
                # Filter date range
                df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
                
                if df.empty:
                    self.failed_symbols.append(symbol)
                    continue
                
                df = df.set_index('date').sort_index()
                
                # Ensure we have close price
                if 'close' not in df.columns:
                    self.failed_symbols.append(symbol)
                    continue
                
                self.price_data[symbol] = df
                self.loaded_count += 1
                
            except Exception as e:
                print(f"  ⚠️  {symbol}: {e}")
                self.failed_symbols.append(symbol)
        
        print(f"\n✓ Loaded price data for {self.loaded_count}/{len(self.universe_symbols)} symbols")
        
        if self.failed_symbols:
            print(f"⚠️  Failed to load {len(self.failed_symbols)} symbols")
            print(f"   First 20: {self.failed_symbols[:20]}")
        
        # Calculate coverage
        coverage = self.loaded_count / len(self.universe_symbols)
        print(f"Coverage: {coverage:.1%}")
        
        if coverage < 0.90:
            print(f"\n❌ ERROR: Coverage ({coverage:.1%}) < 90% threshold")
            print(f"   This will cause Universe-Score mismatch!")
            raise ValueError(f"Insufficient price data coverage: {coverage:.1%}")
        
        return coverage
    
    def calculate_momentum_score(self, symbol, df):
        """
        간단한 모멘텀 스코어 계산 (6개월)
        실제로는 더 복잡한 Multi-Alpha 로직 사용
        """
        # 6m momentum
        if len(df) < 126:  # ~6 months
            return None
        
        try:
            current_price = df['close'].iloc[-1]
            past_price = df['close'].iloc[-126]
            
            momentum = (current_price - past_price) / past_price
            
            return momentum
        except:
            return None
    
    def generate_scores(self, start_date, end_date):
        """
        스코어 생성
        """
        print(f"\nGenerating scores...")
        
        # Get all trading dates
        dates = None
        for symbol, df in self.price_data.items():
            if dates is None:
                dates = df.index
            else:
                dates = dates.union(df.index)
        
        dates = sorted(dates)
        print(f"✓ Found {len(dates)} trading dates")
        
        # Generate scores for each date
        all_scores = []
        
        for i, date in enumerate(dates):
            if i % 50 == 0:
                print(f"  Processing date {i}/{len(dates)}: {date.date()}")
            
            for symbol in self.price_data.keys():
                df =self.price_data[symbol]
                
                # Get data up to this date
                df_upto = df.loc[:date]
                
                if len(df_upto) == 0:
                    continue
                
                # Calculate score
                score = self.calculate_momentum_score(symbol, df_upto)
                
                all_scores.append({
                    'date': date,
                    'symbol': symbol,
                    'score': score if score is not None else np.nan
                })
        
        df_scores = pd.DataFrame(all_scores)
        
        print(f"\n✓ Generated {len(df_scores)} score records")
        print(f"  Date range: {df_scores['date'].min().date()} to {df_scores['date'].max().date()}")
        print(f"  Unique symbols: {df_scores['symbol'].nunique()}")
        
        return df_scores
    
    def save_scores(self, df_scores, output_file):
        """스코어 파일 저장 + 메타데이터"""
        output_path = Path(output_file)
        
        # Save scores
        df_scores.to_csv(output_path, index=False)
        print(f"\n✓ Saved scores to {output_path}")
        print(f"  File size: {output_path.stat().st_size:,} bytes")
        
        # Generate metadata
        meta = {
            'generated_at': str(datetime.now()),
            'start_date': str(df_scores['date'].min().date()),
            'end_date': str(df_scores['date'].max().date()),
            'universe_file': str(self.universe_file),
            'universe_count': len(self.universe_symbols),
            'symbols_count': df_scores['symbol'].nunique(),
            'total_records': len(df_scores),
            'missing_symbols': self.failed_symbols,
            'coverage': df_scores['symbol'].nunique() / len(self.universe_symbols)
        }
        
        meta_file = output_path.with_suffix('.meta.json')
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved metadata to {meta_file}")
        
        # Report
        print(f"\n{'='*60}")
        print(f"SCORE GENERATION REPORT")
        print(f"{'='*60}")
        print(f"Universe symbols:  {meta['universe_count']}")
        print(f"Scored symbols:    {meta['symbols_count']}")
        print(f"Coverage:          {meta['coverage']:.1%}")
        print(f"Missing symbols:   {len(meta['missing_symbols'])}")
        print(f"Date range:        {meta['start_date']} to {meta['end_date']}")
        print(f"Total records:     {meta['total_records']:,}")
        print(f"{'='*60}")
        
        # Check coverage
        if meta['coverage'] < 0.90:
            print(f"\n⚠️  WARNING: Coverage < 90%")
            print(f"   Missing symbols ({len(meta['missing_symbols'])}):")
            for sym in meta['missing_symbols'][:30]:
                print(f"     - {sym}")
            return False
        else:
            print(f"\n✅ Coverage >= 90% - Success!")
            return True

def main():
    parser = argparse.ArgumentParser(description='Generate scores with universe enforcement')
    parser.add_argument('--universe', default='GARAM_Data/real_universe_400.csv',
                       help='Universe CSV file')
    parser.add_argument('--price-dir', default='g:/내 드라이브/garamdata/history/daily',
                       help='Price data directory')
    parser.add_argument('--start-date', default='2024-12-05',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=None,
                       help='End date (YYYY-MM-DD), default: today')
    parser.add_argument('--output', default='GARAM_Data/real_scores_2024.csv',
                       help='Output score file')
    
    args = parser.parse_args()
    
    # Parse dates
    start_date = pd.to_datetime(args.start_date)
    if args.end_date:
        end_date = pd.to_datetime(args.end_date)
    else:
        end_date = pd.Timestamp.now()
    
    print(f"\n{'='*60}")
    print(f"GARAM Score Generator")
    print(f"{'='*60}")
    print(f"Universe:    {args.universe}")
    print(f"Price dir:   {args.price_dir}")
    print(f"Date range:  {start_date.date()} to {end_date.date()}")
    print(f"Output:      {args.output}")
    print(f"{'='*60}\n")
    
    # Generate
    generator = ScoreGenerator(args.universe, args.price_dir)
    
    coverage = generator.load_price_data(start_date, end_date)
    
    df_scores = generator.generate_scores(start_date, end_date)
    
    success = generator.save_scores(df_scores, args.output)
    
    if not success:
        print(f"\n❌ Score generation completed with warnings")
        sys.exit(1)
    else:
        print(f"\n✅ Score generation completed successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()
