import logging
from flask import Blueprint, jsonify
from datetime import datetime
import random

portfolio_bp = Blueprint('portfolio', __name__)
logger = logging.getLogger(__name__)

@portfolio_bp.route('/universe', methods=['GET'])
def get_universe_status():
    """
    Returns the current active universe and rotation logs.
    """
    try:
        # Mock Data for Universe (Replace with actual PortfolioManager state later)
        active_universe = [
            {'symbol': '005930', 'name': '삼성전자', 'sector': 'Tech', 'rank': 1},
            {'symbol': '000660', 'name': 'SK하이닉스', 'sector': 'Tech', 'rank': 2},
            {'symbol': '373220', 'name': 'LG에너지솔루션', 'sector': 'Battery', 'rank': 3},
            {'symbol': '207940', 'name': '삼성바이오로직스', 'sector': 'Bio', 'rank': 4},
            {'symbol': '005380', 'name': '현대차', 'sector': 'Auto', 'rank': 5},
            {'symbol': '000270', 'name': '기아', 'sector': 'Auto', 'rank': 6},
            {'symbol': '068270', 'name': '셀트리온', 'sector': 'Bio', 'rank': 7},
            {'symbol': '105560', 'name': 'KB금융', 'sector': 'Finance', 'rank': 8},
            {'symbol': '005490', 'name': 'POSCO홀딩스', 'sector': 'Steel', 'rank': 9},
            {'symbol': '035420', 'name': 'NAVER', 'sector': 'Tech', 'rank': 10}
        ]
        
        dead_symbols = [
            {'symbol': '035720', 'name': '카카오', 'reason': 'Low Momentum'},
            {'symbol': '051910', 'name': 'LG화학', 'reason': 'Sector Weakness'}
        ]
        
        rotation_log = [
            {'date': '2025-11-20', 'in': 'KB금융', 'out': '카카오', 'reason': 'Momentum Score'},
            {'date': '2025-11-15', 'in': '기아', 'out': 'LG화학', 'reason': 'Earnings Surprise'}
        ]
        
        return jsonify({
            'active_count': len(active_universe),
            'active': active_universe,
            'dead': dead_symbols,
            'rotation_log': rotation_log
        })
    except Exception as e:
        logger.error(f"Error fetching universe: {e}")
        return jsonify({'error': str(e)}), 500

@portfolio_bp.route('/performance', methods=['GET'])
def get_performance_metrics():
    """
    Returns key performance metrics (CAGR, Sharpe, DD).
    """
    try:
        # Mock Data for Performance (Replace with actual Backtest/Live stats)
        return jsonify({
            'period': '2025-01-01 ~ 2025-11-27',
            'metrics': {
                'total_return': 0.185, # 18.5%
                'cagr': 0.21,
                'sharpe_ratio': 1.8,
                'max_drawdown': -0.085, # -8.5%
                'win_rate': 0.58,
                'profit_factor': 1.6
            },
            'monthly_returns': [0.02, 0.015, -0.01, 0.03, 0.04, -0.02, 0.01, 0.025, 0.03, 0.01, 0.02]
        })
    except Exception as e:
        logger.error(f"Error fetching performance: {e}")
        return jsonify({'error': str(e)}), 500
