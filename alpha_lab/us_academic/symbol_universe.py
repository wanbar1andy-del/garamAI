"""
Symbol Universe Management
Manages lists of symbols for different universes (S&P 500, Russell 2000, etc.)
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict
import logging
import json

logger = logging.getLogger(__name__)


class SymbolUniverse:
    """
    Manages symbol universes for US markets
    Provides lists of symbols for different indices and sectors
    """
    
    # S&P 500 top holdings (sample - in production, fetch from reliable source)
    SP500_SAMPLE = [
        # Technology
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL", "ADBE",
        # Financials
        "BRK.B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SCHW", "AXP",
        # Healthcare
        "UNH", "JNJ", "LLY", "PFE", "ABBV", "TMO", "MRK", "ABT", "DHR", "BMY",
        # Consumer
        "WMT", "HD", "PG", "KO", "PEP", "COST", "MCD", "NKE", "SBUX", "TGT",
        # Industrial
        "BA", "CAT", "GE", "HON", "UNP", "UPS", "RTX", "LMT", "DE", "MMM",
        # Energy
        "XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC", "VLO", "PSX", "OXY",
        # Utilities
        "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "PEG", "XEL", "ED",
        # Real Estate
        "AMT", "PLD", "CCI", "EQIX", "PSA", "WELL", "DLR", "O", "SBAC", "AVB",
        # Materials
        "LIN", "APD", "SHW", "ECL", "DD", "NEM", "FCX", "NUE", "VMC", "MLM",
        # Communication
        "GOOG", "DIS", "CMCSA", "NFLX", "T", "VZ", "TMUS", "CHTR", "EA", "ATVI"
    ]
    
    SECTORS = {
        "Technology": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL", "ADBE"],
        "Financials": ["BRK.B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SCHW", "AXP"],
        "Healthcare": ["UNH", "JNJ", "LLY", "PFE", "ABBV", "TMO", "MRK", "ABT", "DHR", "BMY"],
        "Consumer": ["WMT", "HD", "PG", "KO", "PEP", "COST", "MCD", "NKE", "SBUX", "TGT"],
        "Industrial": ["BA", "CAT", "GE", "HON", "UNP", "UPS", "RTX", "LMT", "DE", "MMM"],
        "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC", "VLO", "PSX", "OXY"],
        "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "PEG", "XEL", "ED"],
        "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "PSA", "WELL", "DLR", "O", "SBAC", "AVB"],
        "Materials": ["LIN", "APD", "SHW", "ECL", "DD", "NEM", "FCX", "NUE", "VMC", "MLM"],
        "Communication": ["GOOG", "DIS", "CMCSA", "NFLX", "T", "VZ", "TMUS", "CHTR", "EA", "ATVI"]
    }
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize Symbol Universe
        
        Args:
            config_dir: Directory for universe configuration files
        """
        if config_dir is None:
            try:
                from garam.config import PATHS
                config_dir = PATHS.CONFIG_DIR / "universes"
            except ImportError:
                config_dir = Path("config/universes")
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"SymbolUniverse initialized with config: {self.config_dir}")
    
    def get_sp500(self, limit: Optional[int] = None) -> List[str]:
        """
        Get S&P 500 symbols
        
        Args:
            limit: Maximum number of symbols to return
        
        Returns:
            List of symbols
        """
        symbols = self.SP500_SAMPLE.copy()
        
        if limit:
            symbols = symbols[:limit]
        
        logger.info(f"Retrieved {len(symbols)} S&P 500 symbols")
        return symbols
    
    def get_sector(self, sector: str) -> List[str]:
        """
        Get symbols for a specific sector
        
        Args:
            sector: Sector name (e.g., 'Technology', 'Financials')
        
        Returns:
            List of symbols in the sector
        """
        if sector not in self.SECTORS:
            logger.warning(f"Unknown sector: {sector}")
            return []
        
        symbols = self.SECTORS[sector].copy()
        logger.info(f"Retrieved {len(symbols)} symbols for sector {sector}")
        return symbols
    
    def get_all_sectors(self) -> List[str]:
        """Get list of all available sectors"""
        return list(self.SECTORS.keys())
    
    def get_custom_universe(self, name: str) -> List[str]:
        """
        Load a custom universe from configuration
        
        Args:
            name: Universe name
        
        Returns:
            List of symbols
        """
        config_file = self.config_dir / f"{name}.json"
        
        if not config_file.exists():
            logger.warning(f"Custom universe not found: {name}")
            return []
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            
            symbols = data.get('symbols', [])
            logger.info(f"Loaded custom universe '{name}': {len(symbols)} symbols")
            return symbols
            
        except Exception as e:
            logger.error(f"Error loading custom universe '{name}': {e}")
            return []
    
    def save_custom_universe(self, name: str, symbols: List[str], metadata: Optional[Dict] = None):
        """
        Save a custom universe
        
        Args:
            name: Universe name
            symbols: List of symbols
            metadata: Optional metadata (description, created_date, etc.)
        """
        config_file = self.config_dir / f"{name}.json"
        
        data = {
            'name': name,
            'symbols': symbols,
            'count': len(symbols),
            'metadata': metadata or {}
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved custom universe '{name}': {len(symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Error saving custom universe '{name}': {e}")
    
    def validate_symbols(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Validate symbols (basic format check)
        
        Args:
            symbols: List of symbols to validate
        
        Returns:
            Dictionary mapping symbol to validity
        """
        results = {}
        
        for symbol in symbols:
            # Basic validation: uppercase, alphanumeric + dots/hyphens
            is_valid = (
                isinstance(symbol, str) and
                len(symbol) > 0 and
                len(symbol) <= 10 and
                all(c.isalnum() or c in '.-' for c in symbol)
            )
            results[symbol] = is_valid
        
        invalid_count = sum(1 for v in results.values() if not v)
        if invalid_count > 0:
            logger.warning(f"Found {invalid_count} invalid symbols")
        
        return results
    
    def get_universe_info(self) -> Dict:
        """Get information about available universes"""
        info = {
            'sp500_count': len(self.SP500_SAMPLE),
            'sectors': {sector: len(symbols) for sector, symbols in self.SECTORS.items()},
            'custom_universes': []
        }
        
        # List custom universes
        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                info['custom_universes'].append({
                    'name': data.get('name'),
                    'count': data.get('count'),
                    'metadata': data.get('metadata', {})
                })
            except Exception as e:
                logger.warning(f"Error reading {config_file}: {e}")
        
        return info


if __name__ == "__main__":
    # Test the universe manager
    logging.basicConfig(level=logging.INFO)
    
    universe = SymbolUniverse()
    
    # Test S&P 500
    print("\n=== S&P 500 Symbols (first 10) ===")
    sp500 = universe.get_sp500(limit=10)
    print(sp500)
    
    # Test sectors
    print("\n=== Available Sectors ===")
    sectors = universe.get_all_sectors()
    print(sectors)
    
    print("\n=== Technology Sector ===")
    tech = universe.get_sector("Technology")
    print(tech)
    
    # Test custom universe
    print("\n=== Creating Custom Universe ===")
    custom_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    universe.save_custom_universe(
        "faang_plus",
        custom_symbols,
        metadata={"description": "FAANG + Tesla", "created": "2024-11-24"}
    )
    
    loaded = universe.get_custom_universe("faang_plus")
    print(f"Loaded custom universe: {loaded}")
    
    # Test validation
    print("\n=== Symbol Validation ===")
    test_symbols = ["AAPL", "INVALID!", "MSFT", "123", "GOOGL"]
    validation = universe.validate_symbols(test_symbols)
    for symbol, is_valid in validation.items():
        print(f"{symbol}: {'Valid' if is_valid else 'Invalid'}")
    
    # Universe info
    print("\n=== Universe Info ===")
    info = universe.get_universe_info()
    print(json.dumps(info, indent=2))
