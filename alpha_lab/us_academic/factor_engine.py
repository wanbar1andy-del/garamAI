
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS
from alpha_lab.us_academic.academic_factors import (
    calc_momentum, 
    calc_low_vol_factor, 
    calc_value_factors, 
    calc_quality_factors,
    rank_cross_sectional,
    calc_composite_factor
)

logger = logging.getLogger(__name__)

class FactorEngine:
    def __init__(self):
        self.prices_dir = PATHS.US_SP500_ROOT / "prices_daily"
        self.price_df: Optional[pd.DataFrame] = None
        self.factor_cache: Dict[str, pd.DataFrame] = {}
        self.last_update = None
        
    def load_data(self):
        """Load all CSV price files and create a unified price DataFrame"""
        logger.info("Loading US price data...")
        
        if not self.prices_dir.exists():
            logger.error(f"Price directory not found: {self.prices_dir}")
            return
            
        csv_files = list(self.prices_dir.glob("*.csv"))
        if not csv_files:
            logger.warning("No CSV files found in price directory")
            return
            
        prices_dict = {}
        
        for file_path in csv_files:
            symbol = file_path.stem
            try:
                df = pd.read_csv(file_path)
                
                # Identify date column
                date_col = None
                for col in ['Date', 'date', 'Datetime', 'datetime']:
                    if col in df.columns:
                        date_col = col
                        break
                
                if date_col:
                    df[date_col] = pd.to_datetime(df[date_col])
                    df.set_index(date_col, inplace=True)
                    
                    # Get close price
                    close_col = None
                    for col in ['Close', 'close', 'Adj Close', 'adj_close']:
                        if col in df.columns:
                            close_col = col
                            break
                            
                    if close_col:
                        prices_dict[symbol] = df[close_col]
            except Exception as e:
                logger.warning(f"Error loading {symbol}: {e}")
                
        if prices_dict:
            # Combine into a single DataFrame (Index=Date, Columns=Symbols)
            self.price_df = pd.DataFrame(prices_dict)
            self.price_df.sort_index(inplace=True)
            logger.info(f"Loaded price data for {len(self.price_df.columns)} symbols")
        else:
            logger.error("Failed to load any price data")

    def calculate_factors(self):
        """Calculate all factors and rankings"""
        if self.price_df is None:
            self.load_data()
            
        if self.price_df is None or self.price_df.empty:
            return None
            
        logger.info("Calculating factors...")
        
        # 1. Momentum (12m minus 1m)
        momentum = calc_momentum(self.price_df, lookback=252, skip=21)
        
        # 2. Low Volatility (60d)
        low_vol = calc_low_vol_factor(self.price_df, window=60)
        
        # 3. Value (Mock for now)
        # In a real scenario, we would pass a fundamentals provider here
        value_df = calc_value_factors(self.price_df)
        # Create a composite value score
        value_score = calc_composite_factor(value_df)
        
        # 4. Quality (Mock for now)
        quality_df = calc_quality_factors(symbols=list(self.price_df.columns))
        # Create a composite quality score
        quality_score = calc_composite_factor(quality_df)
        
        # 5. Rankings (Percentiles 0-100)
        rankings = pd.DataFrame({
            'momentum_raw': momentum,
            'low_vol_raw': low_vol,
            'value_raw': value_score,
            'quality_raw': quality_score
        })
        
        # Calculate percentile ranks (0.0 to 1.0)
        rankings['momentum_rank'] = rank_cross_sectional(momentum, ascending=True)
        rankings['low_vol_rank'] = rank_cross_sectional(low_vol, ascending=True)
        rankings['value_rank'] = rank_cross_sectional(value_score, ascending=True)
        rankings['quality_rank'] = rank_cross_sectional(quality_score, ascending=True)
        
        # Composite Score (Equal Weight)
        rankings['composite_score'] = (
            rankings['momentum_rank'].fillna(0.5) + 
            rankings['low_vol_rank'].fillna(0.5) + 
            rankings['value_rank'].fillna(0.5) + 
            rankings['quality_rank'].fillna(0.5)
        ) / 4.0
        
        self.factor_cache['rankings'] = rankings
        logger.info("Factor calculation complete")
        
        return rankings

    def get_top_opportunities(self, n=20):
        """Get top N stocks by composite score"""
        if 'rankings' not in self.factor_cache:
            self.calculate_factors()
            
        rankings = self.factor_cache.get('rankings')
        if rankings is None:
            return []
            
        top_stocks = rankings.sort_values('composite_score', ascending=False).head(n)
        
        results = []
        for symbol, row in top_stocks.iterrows():
            results.append({
                'symbol': symbol,
                'composite_score': round(row['composite_score'] * 100, 1),
                'momentum_rank': round(row['momentum_rank'] * 100, 1),
                'value_rank': round(row['value_rank'] * 100, 1),
                'quality_rank': round(row['quality_rank'] * 100, 1),
                'low_vol_rank': round(row['low_vol_rank'] * 100, 1)
            })
            
        return results

    def get_symbol_profile(self, symbol):
        """Get factor profile for a specific symbol"""
        if 'rankings' not in self.factor_cache:
            self.calculate_factors()
            
        rankings = self.factor_cache.get('rankings')
        if rankings is None or symbol not in rankings.index:
            return None
            
        row = rankings.loc[symbol]
        return {
            'symbol': symbol,
            'composite_score': round(row['composite_score'] * 100, 1),
            'factors': {
                'Momentum': round(row['momentum_rank'] * 100, 1),
                'Value': round(row['value_rank'] * 100, 1),
                'Quality': round(row['quality_rank'] * 100, 1),
                'Low Volatility': round(row['low_vol_rank'] * 100, 1)
            },
            'raw_values': {
                'Momentum (12m)': f"{row['momentum_raw']:.2%}" if pd.notnull(row['momentum_raw']) else "N/A",
                'Volatility (60d)': f"{1/row['low_vol_raw'] - 1:.2%}" if pd.notnull(row['low_vol_raw']) else "N/A" 
                # Note: low_vol_raw is 1/(1+vol), so vol = 1/score - 1
            }
        }
