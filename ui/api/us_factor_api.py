"""
US Factor API Blueprint
Provides endpoints for US market data and factor analysis.
NO MOCK DATA - Uses only real collected data.
"""

from flask import Blueprint, jsonify, request
import pandas as pd
from pathlib import Path
import sys
import logging
from datetime import datetime
"""
US Factor API Blueprint
Provides endpoints for US market data and factor analysis.
NO MOCK DATA - Uses only real collected data.
"""

from flask import Blueprint, jsonify, request
import pandas as pd
from pathlib import Path
import sys
import logging
from datetime import datetime
from alpha_lab.us_academic.factor_engine import FactorEngine
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PATHS

logger = logging.getLogger(__name__)

us_bp = Blueprint('us_factor', __name__, url_prefix='/api')

# Initialize Factor Engine (Lazy loading recommended in production, but eager here for simplicity)
factor_engine = FactorEngine()

@us_bp.route('/us/symbols', methods=['GET'])
def get_available_symbols():
    """Get list of available US symbols from collected data"""
    try:
        # Try to read from constituents file first
        constituents_dir = PATHS.US_SP500_ROOT / "constituents"
        parquet_files = list(constituents_dir.glob("*.parquet"))
        
        if parquet_files:
            latest_file = sorted(parquet_files)[-1]
            df = pd.read_parquet(latest_file)
            if 'Symbol' in df.columns:
                return jsonify({
                    "count": len(df),
                    "symbols": df['Symbol'].tolist()
                })
            elif 'symbol' in df.columns:
                return jsonify({
                    "count": len(df),
                    "symbols": df['symbol'].tolist()
                })
        
        # Fallback: list directories in prices_daily
        prices_dir = PATHS.US_SP500_ROOT / "prices_daily"
        if prices_dir.exists():
            # Support both parquet and csv
            files = list(prices_dir.glob("*.parquet")) + list(prices_dir.glob("*.csv"))
            symbols = sorted(list(set([f.stem for f in files])))
            return jsonify({
                "count": len(symbols),
                "symbols": symbols
            })
            
        return jsonify({"count": 0, "symbols": []})
    except Exception as e:
        logger.error(f"Error getting symbols: {e}")
        return jsonify({"error": str(e)}), 500

@us_bp.route('/us/price/<symbol>', methods=['GET'])
def get_us_price(symbol):
    """
    Get daily price history for a symbol
    """
    try:
        symbol = symbol.upper()
        prices_dir = PATHS.US_SP500_ROOT / "prices_daily"
        
        # Try parquet first, then csv
        file_path = prices_dir / f"{symbol}.parquet"
        if not file_path.exists():
            file_path = prices_dir / f"{symbol}.csv"
        
        if not file_path.exists():
            return jsonify({
                "error": f"Data not found for {symbol}",
                "symbol": symbol,
                "data_source": "real"
            }), 404
            
        if file_path.suffix == '.parquet':
            df = pd.read_parquet(file_path)
        else:
            df = pd.read_csv(file_path)
            # Ensure date column is parsed
            for col in ['Date', 'date', 'Datetime', 'datetime']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
                    break
        
        # Reset index to make Date a column if it's the index
        if isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            
        # Ensure Date column exists and is string
        date_col = None
        for col in ['Date', 'date', 'Datetime', 'datetime']:
            if col in df.columns:
                date_col = col
                break
        
        if not date_col:
             return jsonify({
                "error": "Date column not found",
                "symbol": symbol,
                "data_source": "real"
            }), 500

        # Format data for chart
        # Limit to last 500 days for performance
        df = df.sort_values(date_col).tail(500)
        
        points = []
        for _, row in df.iterrows():
            points.append({
                "date": row[date_col].strftime('%Y-%m-%d') if isinstance(row[date_col], (datetime, pd.Timestamp)) else str(row[date_col]),
                "open": float(row.get('Open', row.get('open', 0))),
                "high": float(row.get('High', row.get('high', 0))),
                "low": float(row.get('Low', row.get('low', 0))),
                "close": float(row.get('Close', row.get('close', 0))),
                "volume": float(row.get('Volume', row.get('volume', 0)))
            })
            
        return jsonify({
            "symbol": symbol,
            "points": points,
            "count": len(points),
            "timestamp": datetime.now().isoformat(),
            "data_source": "real"
        })
        
    except Exception as e:
        logger.error(f"Error in get_us_price: {e}")
        return jsonify({
            "error": str(e),
            "symbol": symbol,
            "data_source": "error"
        }), 500

@us_bp.route('/us/factors/rankings', methods=['GET'])
def get_factor_rankings():
    """Get top stocks ranked by composite factor score"""
    try:
        limit = request.args.get('limit', default=20, type=int)
        opportunities = factor_engine.get_top_opportunities(n=limit)
        return jsonify({
            "count": len(opportunities),
            "opportunities": opportunities,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting factor rankings: {e}")
        return jsonify({"error": str(e)}), 500

@us_bp.route('/us/factors/<symbol>', methods=['GET'])
def get_symbol_factors(symbol):
    """Get specific factor scores for a symbol"""
    try:
        symbol = symbol.upper()
        profile = factor_engine.get_symbol_profile(symbol)
        
        if profile:
            return jsonify(profile)
        else:
            return jsonify({
                "error": f"Factor data not found for {symbol}",
                "symbol": symbol
            }), 404
    except Exception as e:
        logger.error(f"Error getting symbol factors: {e}")
        return jsonify({"error": str(e)}), 500

@us_bp.route('/us/strategies/summary', methods=['GET'])
def get_strategies_summary():
    """Get summary of all US factor strategies"""
    try:
        experiments_dir = PATHS.EXPERIMENTS_DIR / "us_factors"
        
        if not experiments_dir.exists():
            return jsonify({
                "strategies": [],
                "count": 0,
                "message": "No strategy results found"
            })
        
        strategies = []
        
        # Look for strategy directories
        for strategy_dir in experiments_dir.glob("US_*"):
            if not strategy_dir.is_dir():
                continue
                
            # Read metrics.csv
            metrics_file = strategy_dir / "metrics.csv"
            if metrics_file.exists():
                try:
                    metrics_df = pd.read_csv(metrics_file, header=None, index_col=0)
                    metrics = metrics_df[1].to_dict()
                    
                    # Extract strategy name from directory
                    strategy_name = strategy_dir.name.split('_')[0] + '_' + strategy_dir.name.split('_')[1] + '_' + strategy_dir.name.split('_')[2]
                    
                    strategies.append({
                        "name": strategy_name,
                        "annual_return": float(metrics.get('annualized_return', 0)),
                        "sharpe_ratio": float(metrics.get('sharpe_ratio', 0)),
                        "max_drawdown": float(metrics.get('max_drawdown', 0)),
                        "total_return": float(metrics.get('total_return', 0)),
                        "win_rate": float(metrics.get('win_rate', 0))
                    })
                except Exception as e:
                    logger.warning(f"Error reading metrics from {strategy_dir}: {e}")
        
        return jsonify({
            "strategies": strategies,
            "count": len(strategies),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting strategies summary: {e}")
        return jsonify({"error": str(e)}), 500

@us_bp.route('/us/strategies/<name>', methods=['GET'])
def get_strategy_detail(name):
    """Get detailed metrics for a specific strategy"""
    try:
        experiments_dir = PATHS.EXPERIMENTS_DIR / "us_factors"
        
        # Find the latest directory for this strategy
        strategy_dirs = list(experiments_dir.glob(f"{name}_*"))
        
        if not strategy_dirs:
            return jsonify({
                "error": f"No results found for strategy {name}",
                "name": name
            }), 404
        
        # Get the most recent one
        latest_dir = sorted(strategy_dirs)[-1]
        
        # Read metrics
        metrics_file = latest_dir / "metrics.csv"
        if not metrics_file.exists():
            return jsonify({
                "error": "Metrics file not found",
                "name": name
            }), 404
        
        metrics_df = pd.read_csv(metrics_file, header=None, index_col=0)
        metrics = metrics_df[1].to_dict()
        
        # Read equity curve
        equity_file = latest_dir / "equity.csv"
        equity_points = []
        
        if equity_file.exists():
            equity_df = pd.read_csv(equity_file)
            # Limit to last 252 days (1 year)
            equity_df = equity_df.tail(252)
            
            for _, row in equity_df.iterrows():
                equity_points.append({
                    "timestamp": str(row['timestamp']),
                    "equity": float(row['equity']),
                    "pnl_balance": float(row['pnl_balance'])
                })
        
        return jsonify({
            "name": name,
            "metrics": {k: float(v) for k, v in metrics.items()},
            "equity_curve": equity_points,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting strategy detail: {e}")
        return jsonify({"error": str(e)}), 500

