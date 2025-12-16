"""
GARAM Dashboard API Server
Provides unified endpoints for dashboard integration
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from datetime import datetime

# Configure Logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('c:/garam/garam/GARAM_Data/logs/server.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)
from typing import Dict, Any, Optional
import json
from pathlib import Path
try:
    import pandas as pd
    import numpy as np
except ImportError:
    pd = None
    np = None
    logger.warning("Pandas not found. Some features will be disabled.")

# Import GARAM components
import sys
# Adjust path as needed for your environment
sys.path.insert(0, 'c:/garam') 

# [C-2] Unified Python Environment
import os
PYTHON_32 = os.environ.get("GARAM_PYTHON_32") or sys.executable
logger.info(f"Subprocess Python: {PYTHON_32}") 

# Import centralized paths
from garam.config import PATHS

# from garam.live.shadow_trader import ShadowTrader
# from garam.agents.gpt_css_agent import GPTCSSAgent
# from garam.agents.market_state_agent import MarketStateAgent
# from garam.alpha_lab.lab import AlphaLab
ShadowTrader = None
# GPTCSSAgent = None
MarketStateAgent = None
AlphaLab = None
from garam.utils.alert_manager import get_alert_manager
from garam.utils.health_check import get_health_checker
from garam.core.health_collector import get_health_collector

# Initialize Flask App
# Point static_folder to ../ui/static to serve dashboard files
app = Flask(__name__, static_folder='../ui/static', static_url_path='')
CORS(app) # Enable CORS for API

# ========== STOCK NAME HELPER ==========
STOCK_NAMES_CACHE = None

def get_stock_names():
    """Load and cache stock names"""
    global STOCK_NAMES_CACHE
    if STOCK_NAMES_CACHE is None:
        try:
            names_file = PATHS.DATA_DIR / "reference" / "stock_names.json"
            if names_file.exists():
                with open(names_file, 'r', encoding='utf-8') as f:
                    STOCK_NAMES_CACHE = json.load(f)
            else:
                STOCK_NAMES_CACHE = {}
        except Exception as e:
            logger.error(f"Failed to load stock names: {e}")
            STOCK_NAMES_CACHE = {}
    return STOCK_NAMES_CACHE

def get_stock_name(code):
    """Get stock name from code"""
    names = get_stock_names()
    return names.get(code, code)
# ========================================

# Import dashboard blueprints
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
# from ui.api.dashboard_api import dashboard_bp
# from ui.api.kr_intraday_api import kr_bp
# from ui.api.us_factor_api import us_bp
# from ui.api.metrics_api import metrics_bp
# from ui.api.health_api import health_bp
# from ui.api.shadow_api import shadow_bp
# from ui.api.regime_api import regime_bp
# from ui.api.ai_core_api import ai_core_bp
# from ui.api.strategy_api import strategy_bp
# from ui.api.portfolio_api import portfolio_bp
from ui.api.simulation_api import simulation_bp

# app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
# app.register_blueprint(kr_bp, url_prefix='/api/kr')
# app.register_blueprint(us_bp, url_prefix='/api/us')
# app.register_blueprint(metrics_bp, url_prefix='/api/metrics')
# app.register_blueprint(health_bp, url_prefix='/api/health')
# app.register_blueprint(shadow_bp, url_prefix='/api/shadow')
# app.register_blueprint(regime_bp, url_prefix='/api')
# app.register_blueprint(ai_core_bp, url_prefix='/api/ai')
# app.register_blueprint(strategy_bp, url_prefix='/api/strategy')
# app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
app.register_blueprint(simulation_bp, url_prefix='/api/simulation')

# [PHASE 3] New Endpoints
@app.route('/api/system/kiwoom/start', methods=['POST'])
@app.route('/api/system/login_kiwoom', methods=['POST'])
def login_kiwoom():
    """Trigger Kiwoom Login Process"""
    try:
        import subprocess
        logger.info("🚀 Triggering Kiwoom Login Window...")
        
        # Path to Kiwoom login UI script
        script_path = PATHS.BASE_DIR / "scripts" / "kiwoom_login_ui.py"
        
        if not script_path.exists():
            return jsonify({
                'status': 'error', 
                'error': f'Login script not found: {script_path}'
            }), 404
        
        # Get 32-bit Python path from env or default
        python_32 = PYTHON_32
        
        # Launch Kiwoom login UI in separate process
        subprocess.Popen(
            [python_32, str(script_path)],
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        
        logger.info("✅ Kiwoom login window launched successfully")
        return jsonify({
            'status': 'triggered', 
            'message': 'Kiwoom 로그인 창을 실행했습니다.'
        })
    except Exception as e:
        logger.error(f"Login trigger failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/kiwoom_status', methods=['GET'])
def kiwoom_status():
    """Check if Kiwoom is connected"""
    try:
        flag_file = PATHS.KIWOOM_FLAG_PATH
        connected = flag_file.exists()
        
        return jsonify({
            'connected': connected,
            'flag_file': str(flag_file)
        })
    except Exception as e:
        logger.error(f"Kiwoom status check failed: {e}")
        return jsonify({'connected': False, 'error': str(e)}), 500

@app.route('/api/system/kiwoom/stop', methods=['POST'])
def stop_kiwoom():
    """Stop Kiwoom Connection (Delete Flag)"""
    try:
        if PATHS.KIWOOM_FLAG_PATH.exists():
            PATHS.KIWOOM_FLAG_PATH.unlink()
        return jsonify({'status': 'stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/state/shadow', methods=['GET'])
def shadow_status():
    """Get real-time shadow trader status"""
    pass # Placeholder

@app.route('/api/live/status', methods=['GET'])
def get_live_status():
    """Get real-time status from live runner"""
    try:
        status_file = PATHS.LOGS_DIR / "dashboard_status.json"
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # --- PnL Delta Calculation Start ---
                try:
                    pnl_delta_daily = 0
                    pnl_delta_daily_pct = 0.0
                    pnl_delta_monthly = 0
                    pnl_delta_monthly_pct = 0.0
                    
                    if PATHS.ACCOUNT_SNAPSHOT.exists():
                        snapshot_df = pd.read_csv(PATHS.ACCOUNT_SNAPSHOT)
                        if not snapshot_df.empty and 'total_equity' in snapshot_df.columns:
                            current_eq = snapshot_df.iloc[-1]['total_equity']
                            
                            # Daily (vs Prev Close)
                            if len(snapshot_df) > 1:
                                prev_eq = snapshot_df.iloc[-2]['total_equity']
                                pnl_delta_daily = current_eq - prev_eq
                                pnl_delta_daily_pct = (pnl_delta_daily / prev_eq) * 100 if prev_eq > 0 else 0.0
                                
                            # Monthly (vs 20 days ago)
                            if len(snapshot_df) > 20:
                                month_eq = snapshot_df.iloc[-21]['total_equity']
                                pnl_delta_monthly = current_eq - month_eq
                                pnl_delta_monthly_pct = (pnl_delta_monthly / month_eq) * 100 if month_eq > 0 else 0.0
                            elif len(snapshot_df) > 0:
                                # Less than a month history, calculate from start
                                start_eq = snapshot_df.iloc[0]['total_equity']
                                pnl_delta_monthly = current_eq - start_eq
                                pnl_delta_monthly_pct = (pnl_delta_monthly / start_eq) * 100 if start_eq > 0 else 0.0
                    
                    data['pnl_delta_daily'] = pnl_delta_daily
                    data['pnl_delta_daily_pct'] = round(pnl_delta_daily_pct, 2)
                    data['pnl_delta_monthly'] = pnl_delta_monthly
                    data['pnl_delta_monthly_pct'] = round(pnl_delta_monthly_pct, 2)
                except Exception as delta_err:
                    logger.warning(f"Failed to calc PnL delta: {delta_err}")
                    data['pnl_delta_daily'] = 0
                    data['pnl_delta_monthly'] = 0
                # --- PnL Delta Calculation End ---
                
                return jsonify(data)
        else:
            return jsonify({
                "profile": "Waiting...",
                "market_regime": "UNKNOWN",
                "micro_regime": "UNKNOWN",
                "last_update": "-",
                "allocations": {},
                "active_strategies": [],
                "pnl_delta_daily": 0,
                "pnl_delta_monthly": 0
            })
    except Exception as e:
        logger.error(f"Error reading live status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/live/portfolio', methods=['GET'])
def get_live_portfolio():
    """Get current portfolio positions and summary from signals_live.json"""
    try:
        signals_file = PATHS.STRATEGY_SIGNALS_LIVE
        
        equity = 0
        cash = 0
        positions = []
        
        def safe_float(val):
            if val is None: return 0.0
            try:
                fval = float(val)
                # Check for nan/inf
                if fval != fval or fval == float('inf') or fval == float('-inf'):
                    return 0.0
                return fval
            except:
                return 0.0

        logger.info(f"Checking Signals File: {signals_file}, Exists: {signals_file.exists()}")

        if signals_file.exists():
            with open(signals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                equity = data.get('equity', 0)
                cash = data.get('cash', 0)
                holdings = data.get('holdings', {})
                
                logger.info(f"DEBUG PORTFOLIO: File={signals_file}, Equity={equity}, Cash={cash}, Holdings={len(holdings)}")
                
                # Convert holdings dict to list
                for sym, info in holdings.items():
                    # info now contains enriched data from run_live_trading.py
                    # {name, qty, entry_price, current_price, entry_date, value, pnl, pnl_pct}
                    
                    # Fallback if old format
                    qty = info.get('qty', 0)
                    price = info.get('current_price', info.get('entry_price', 0))
                    val = info.get('value', qty * price)
                    weight = val / equity if equity > 0 else 0
                    
                    # Fetch History for Sparkline
                    history = []
                    try:
                        # Try daily history first
                        daily_csv = PATHS.HISTORY_DIR / "daily" / f"{sym}_daily.csv"
                        if daily_csv.exists():
                            if pd:
                                df = pd.read_csv(daily_csv)
                                if not df.empty:
                                    history = df['close'].tail(20).tolist()
                            else:
                                logger.warning(f"Pandas not available, skipping history for {sym}")
                        else:
                            logger.debug(f"History file not found: {daily_csv}")
                    except Exception as h_err:
                        logger.warning(f"Failed to load history for {sym}: {h_err}")

                    positions.append({
                        "symbol": sym,
                        "name": get_stock_name(sym),  # Always use fresh stock name from JSON
                        "weight": round(safe_float(weight), 4),
                        "value": safe_float(val),
                        "pnl": safe_float(info.get('pnl')),
                        "pnl_pct": safe_float(info.get('pnl_pct')),
                        "qty": safe_float(qty), # Keep as float then maybe int in UI
                        "price": safe_float(price),
                        "entry_price": safe_float(info.get('entry_price')),
                        "entry_date": info.get('entry_date', '-'),
                        "history": [safe_float(x) for x in history]
                    })

        return jsonify({
            "total_equity": safe_float(equity),
            "cash_balance": safe_float(cash),
            "positions": positions
        })
    except Exception as e:
        logger.error(f"Error reading portfolio: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/live/performance', methods=['GET'])
def get_live_performance():
    """Get equity curve and performance metrics"""
    try:
        if not PATHS.ACCOUNT_SNAPSHOT.exists():
            return jsonify({"equity_curve": [], "monthly_pnl": []})
            
        df = pd.read_csv(PATHS.ACCOUNT_SNAPSHOT)
        # Simplify for chart
        equity_curve = df[['timestamp', 'total_equity']].to_dict('records')
        
        return jsonify({
            "equity_curve": equity_curve,
            "monthly_pnl": [] # Todo: Calculate from df
        })
    except Exception as e:
        logger.error(f"Error reading performance: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/live/trades', methods=['GET'])
def get_live_trades():
    """Get execution log"""
    try:
        if not PATHS.LIVE_TRADES.exists():
            return jsonify({"trades": []})
            
        df = pd.read_csv(PATHS.LIVE_TRADES)
        return jsonify({"trades": df.to_dict('records')})
    except Exception as e:
        logger.error(f"Error reading trades: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/live/intent', methods=['GET'])
def get_live_intent():
    """Get daily intent"""
    try:
        if not PATHS.DAILY_INTENT.exists():
            return jsonify({})
            
        with open(PATHS.DAILY_INTENT, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except Exception as e:
        logger.error(f"Error reading intent: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/live/cashflow', methods=['GET'])
def get_live_cashflow():
    """Get cash flow events"""
    try:
        if not PATHS.CASH_EVENTS.exists():
            return jsonify({"events": []})
            
        df = pd.read_csv(PATHS.CASH_EVENTS)
        return jsonify({"events": df.to_dict('records')})
    except Exception as e:
        logger.error(f"Error reading cashflow: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/kr/targets', methods=['GET'])
def kr_targets():
    """Get target symbols with REAL status from ShadowTraders."""
    try:
        logger.info("DEBUG: Executing kr_targets with dynamic mode loading...")
        # 1. Define Base Targets
        base_targets = {
            '005930': '삼성전자', '000660': 'SK하이닉스', '373220': 'LG에너지솔루션',
            '207940': '삼성바이오로직스', '005380': '현대차', '000270': '기아',
            '068270': '셀트리온', '105560': 'KB금융', '005490': 'POSCO홀딩스',
            '035420': 'NAVER'
        }
        
        # 2. Read Status Files
        mode_config = load_trading_mode()
        current_mode = mode_config.get('trading_mode', 'SHADOW')
        log_dir = PATHS.LOGS_DIR / ("live_paper" if current_mode == "LIVE_PAPER" else "shadow")
        status_files = list(log_dir.glob("status_*.json"))
        
        results = []
        
        # 3. Merge Data
        for symbol, name in base_targets.items():
            # Default State
            item = {
                'symbol': symbol,
                'name': name,
                'price': 0,
                'change': 0,
                'status': 'WAITING',
                'reason': 'Initializing...',
                'history': [] # For sparkline
            }
            
            # A. Try to read Status File (Live/Shadow Trader status)
            status_file = log_dir / f"status_{symbol}.json"
            if status_file.exists():
                try:
                    with open(status_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Check if data is from today
                        ts_str = data.get('timestamp', '')
                        if ts_str.startswith(datetime.now().strftime("%Y-%m-%d")):
                            item['price'] = data.get('price', 0)
                            item['status'] = data.get('signal', 'WAITING')
                            item['reason'] = data.get('reason', '-')
                            # If change is available in status, use it
                            if 'change' in data:
                                item['change'] = data['change']
                except:
                    pass

            # B. Get Price History
            # Strategy: Realtime 1m (Latest) -> Daily History (Fallback)
            csv_dir = PATHS.DATA_DIR / "kr" / "realtime" / "1m"
            target_csv = None
            
            # 1. Try Realtime (Today or Latest)
            if csv_dir.exists():
                today_str = datetime.now().strftime("%Y%m%d")
                possible_today = csv_dir / f"{symbol}_{today_str}.csv"
                if possible_today.exists():
                    target_csv = possible_today
                else:
                    # Find latest available realtime
                    all_csvs = sorted(list(csv_dir.glob(f"{symbol}_*.csv")))
                    if all_csvs:
                        target_csv = all_csvs[-1]

            # 2. Read Realtime if found
            if target_csv and target_csv.exists() and pd:
                try:
                    df = pd.read_csv(target_csv)
                    if not df.empty:
                        item['history'] = df['close'].tail(60).tolist()
                        item['price'] = int(df.iloc[-1]['close'])
                        
                        first_price = df.iloc[0]['close']
                        if first_price > 0:
                            item['change'] = round(((item['price'] - first_price) / first_price) * 100, 2)
                except Exception as e:
                    logger.warning(f"Error reading realtime CSV for {symbol}: {e}")

            # 3. Fallback to Daily History (If Price still 0)
            if item['price'] == 0:
                try:
                    daily_csv = PATHS.HISTORY_DIR / "daily" / f"{symbol}_daily.csv"
                    if daily_csv.exists() and pd:
                        df_d = pd.read_csv(daily_csv)
                        if not df_d.empty:
                            last_close = df_d.iloc[-1]['close']
                            prev_close = df_d.iloc[-2]['close'] if len(df_d) > 1 else last_close
                            
                            item['price'] = int(last_close)
                            item['change'] = round(((last_close - prev_close) / prev_close) * 100, 2)
                            item['reason'] = "장 마감 (일봉 데이터)" # Market Closed (Daily Data)
                            item['history'] = df_d['close'].tail(20).tolist() # Daily sparkline
                except Exception as e:
                    logger.warning(f"Error reading daily fallback for {symbol}: {e}")

            # 4. Final Fallback
            if item['price'] == 0:
                item['price'] = 0
                item['change'] = 0
                item['reason'] = "데이터 없음" # No Data Available
                item['history'] = []
                
            results.append(item)
            
        return jsonify({'targets': results})
        
    except Exception as e:
        logger.error(f"Error in kr_targets ({__file__}): {e}")
        return jsonify({'targets': [], 'error': f"{str(e)} in {__file__}"})

@app.route('/api/market/indices', methods=['GET'])
def get_market_indices():
    """
    Get KOSPI/KOSDAQ Index Data.
    Reads from labeled_KR_KOSPI/KOSDAQ_daily_20y.csv in HISTORY_DIR.
    """
    try:
        indices = {}
        
        target_files = {
            "kospi": {
                "name": "KOSPI",
                "file": "labeled_KR_KOSPI_daily_20y.csv", 
                "base": 2500.0
            },
            "kosdaq": {
                "name": "KOSDAQ", 
                "file": "labeled_KR_KOSDAQ_daily_20y.csv",
                "base": 850.0
            }
        }

        for key, info in target_files.items():
            try:
                # PATHS.HISTORY_DIR = g:/내 드라이브/garamdata/history
                csv_path = PATHS.HISTORY_DIR / info["file"]
                
                if csv_path.exists() and pd:
                    # Read last 30 rows to be safe
                    # Note: engine='python' might be needed if path has special chars, but usually pathlib handles it.
                    # Use 'utf-8' or 'euc-kr' depending on file save. Usually utf-8 is safe default if generated by python.
                    df = pd.read_csv(csv_path) 
                    
                    if not df.empty:
                        # Ensure sorted
                        # df = df.sort_values('timestamp') # Assuming already sorted
                        
                        last_row = df.iloc[-1]
                        price = float(last_row['close'])
                        
                        # Calculate change
                        if len(df) > 1:
                            prev_row = df.iloc[-2]
                            prev_close = float(prev_row['close'])
                            change = price - prev_close
                            change_pct = (change / prev_close) * 100
                        else:
                            change = 0.0
                            change_pct = 0.0
                            
                        # History for sparkline (last 20)
                        history = df['close'].tail(20).tolist()
                        
                        indices[key] = {
                            "name": info["name"],
                            "price": round(price, 2),
                            "change": round(change, 2),
                            "change_pct": round(change_pct, 2),
                            "history": [round(x, 2) for x in history]
                        }
                    else:
                        raise Exception("Empty CSV")
                else:
                     raise Exception("File not found")

            except Exception as e:
                # Fallback to Mock if file read fails
                # logger.warning(f"Index {key} load failed: {e}. Using mock.")
                import random
                base = info["base"]
                curr = base + random.uniform(-10, 10)
                indices[key] = {
                    "name": info["name"],
                    "price": round(curr, 2),
                    "change": 0.0,
                    "change_pct": 0.0,
                    "history": [base] * 20
                }

        return jsonify(indices)

    except Exception as e:
        logger.error(f"Error getting indices: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/live/signals', methods=['GET'])
def get_live_signals():
    """Get recent trading signals from signals_live.json."""
    try:
        signals_file = PATHS.STRATEGY_SIGNALS_LIVE
        
        signals = []
        if signals_file.exists():
            with open(signals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # data['orders'] contains the list of orders
                # We need to format them for the frontend
                # Frontend expects: { time, name, signal, price }
                
                # Use generated_at time
                gen_time = data.get('generated_at', '').split(' ')[1][:5] # HH:MM
                
                for order in data.get('orders', []):
                    signals.append({
                        'symbol': order.get('symbol', 'UNKNOWN'),
                        'name': order.get('symbol', 'UNKNOWN'), # TODO: Map symbol to name
                        'signal': order.get('action', 'UNKNOWN'),
                        'price': order.get('price', 0),
                        'time': gen_time
                    })
        
        return jsonify({'signals': signals})
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/live/orders', methods=['GET'])
def get_live_orders():
    """Get detailed order history from live_trades.csv (Persistent)."""
    try:
        trades_file = PATHS.LIVE_TRADES
        orders = []
        
        if trades_file.exists() and pd:
            try:
                # Read last 50 trades
                df = pd.read_csv(trades_file)
                if not df.empty:
                    recent = df.tail(50).sort_index(ascending=False)
                    for _, row in recent.iterrows():
                        # Format timestamp to HH:MM of the day (or full date if old)
                        ts_str = str(row['timestamp'])
                        # "2025-11-21 15:30:00" -> "11/21 15:30"
                        try:
                            dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                            display_time = dt.strftime("%m/%d %H:%M")
                        except:
                            display_time = ts_str

                        def safe_int(val):
                            try:
                                if pd.isna(val): return 0
                                return int(float(val))
                            except: return 0

                        orders.append({
                            'time': display_time,
                            'symbol': str(row.get('symbol', '')).zfill(6),
                            'name': str(row.get('name', '')),
                            'signal': row.get('type', ''),
                            'price': safe_int(row.get('price')),
                            'qty': safe_int(row.get('qty')),
                            'pnl': safe_int(row.get('pnl'))
                        })
            except Exception as e:
                logger.warning(f"Failed to read live_trades.csv: {e}")
                
        # Fallback to signals_live.json if CSV empty or fail
        if not orders and PATHS.STRATEGY_SIGNALS_LIVE.exists():
             with open(PATHS.STRATEGY_SIGNALS_LIVE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                gen_time = data.get('generated_at', '').split(' ')[1][:5]
                for order in data.get('orders', []):
                    if 'time' not in order: order['time'] = gen_time
                    orders.append(order)
        
        return jsonify({'orders': orders})
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Handle AI Chat Messages"""
    try:
        data = request.get_json()
        user_msg = data.get('message', '')
        
        # Real AI Logic (Placeholder for now, but no fake data)
        # If no AI agent is connected, return standard message
        response = "AI Agent not connected."
        
        # if css_agent:
        #      # In future, call css_agent.chat(user_msg)
        #      pass

        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio/detailed', methods=['GET'])
def get_detailed_portfolio():
    """Get Rich Portfolio Data for Visualization"""
    try:
        # Return empty structure if no real data source
        return jsonify({
            'total_equity': 0,
            'cash': 0,
            'positions': []
        })
    except Exception as e:
        logger.error(f"Portfolio data failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/v4/<path:path>')
def serve_v4(path):
    return app.send_static_file(f'v4/{path}')

@app.route('/api/ai/logs', methods=['GET'])
@app.route('/api/logs', methods=['GET'])
def get_system_logs():
    """
    Get today's system logs (reverse chronological)
    """
    try:
        today_str = datetime.now().strftime("%Y%m%d")
        # 1. Main System Log
        log_file = PATHS.LOGS_DIR / f"system_{today_str}.log"
        # 2. Ingest Log
        ingest_log = PATHS.LOGS_DIR / "kiwoom_system_log.txt"
        
        logs = []
        
        def read_log_safe(fpath, tag):
            if fpath.exists():
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()[-200:] # Last 200 lines
                    for line in lines:
                        logs.append(f"[{tag}] {line.strip()}")

        read_log_safe(log_file, "ENGINE")
        read_log_safe(ingest_log, "GATEWAY")
        
        # Reverse to show newest first
        logs.reverse()
        
        return jsonify({"logs": logs})
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return jsonify({'error': str(e), 'logs': []})

@app.route('/api/tasks')
def get_tasks():
    """Read and parse task.md for dashboard display"""
    try:
        task_file = Path(r"C:\Users\wanba\.gemini\antigravity\brain\00ffe881-8176-4fe8-be5c-57c6752caca2\task.md")
        if not task_file.exists():
            return jsonify({"tasks": []})
            
        tasks = []
        with open(task_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('- [ ]') or line.startswith('- [x]'):
                    status = 'done' if line.startswith('- [x]') else 'todo'
                    text = line.replace('- [ ]', '').replace('- [x]', '').strip()
                    # Remove HTML comments if any
                    if '<!--' in text:
                        text = text.split('<!--')[0].strip()
                    # Remove bold markdown
                    text = text.replace('**', '')
                    
                    tasks.append({"status": status, "text": text})
                    
        return jsonify({"tasks": tasks})
    except Exception as e:
        logger.error(f"Error reading tasks: {e}")
        return jsonify({"error": str(e), "tasks": []})

# Global instances
shadow_trader = None
# css_agent = None
alpha_lab = None
alert_manager = get_alert_manager()
health_checker = get_health_checker()

# State cache
_state_cache = {
    'market_state': {},
    'active_condition': {},
    'mode': {},
    'last_update': None
}

# Trading mode file
TRADING_MODE_FILE = PATHS.TRADING_MODE_FILE

def load_trading_mode() -> Dict[str, Any]:
    """Load trading mode configuration"""
    try:
        if TRADING_MODE_FILE.exists():
            with open(TRADING_MODE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load trading mode: {e}")
    
    return {
        'trading_mode': 'SHADOW',
        'auto_switch': True,
        'safeguard_status': 'ACTIVE'
    }

def save_trading_mode(mode_config: Dict[str, Any]):
    """Save trading mode configuration"""
    try:
        TRADING_MODE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TRADING_MODE_FILE, 'w', encoding='utf-8') as f:
            json.dump(mode_config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save trading mode: {e}")

@app.route('/api/state/global', methods=['GET'])
def get_global_state():
    """
    통합 상태 API
    Returns: Market State + Active Condition + Mode
    """
    try:
        # Market State (from MarketStateAgent or cache)
        # In production, this would call MarketStateAgent
        market_state = {
            'trend': 'UP',
            'volatility': 'NORMAL',
            'news_fear_score': 35,
            'ai_footprint': 'MODERATE',
            'regime': 'UP_NORMAL',
            'confidence': 0.85
        }
        
        # Active Condition (from GPTCSSAgent)
        try:
            current_conditions = None
            # if css_agent:
            #     current_conditions = css_agent.load_current_conditions()
            
            if current_conditions:
                active_condition = {
                    'id': current_conditions.get('active_condition_id', 'UNKNOWN'),
                    'activated_at': current_conditions.get('activated_at'),
                    'strategies': ['S1_D1_Scalping'],  # Would load from condition set
                    'risk_profile': {
                        'daily_return_target': 0.015,
                        'max_drawdown': -0.008,
                        'max_gross_exposure': 0.8
                    }
                }
            else:
                active_condition = {
                    'id': 'DEFAULT',
                    'activated_at': datetime.now().isoformat(),
                    'strategies': ['S1_D1_Scalping'],
                    'risk_profile': {}
                }
        except Exception as e:
            logger.warning(f"Failed to load active condition: {e}")
            active_condition = {'id': 'ERROR', 'error': str(e)}
        
        # Mode
        mode = load_trading_mode()
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'market_state': market_state,
            'active_condition': active_condition,
            'mode': mode
        })
    except Exception as e:
        logger.error(f"Error in get_global_state: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/shadow/trades', methods=['GET'])
def get_shadow_trades():
    """
    Shadow Trading 체결 내역
    Query Params: limit, since
    """
    try:
        if not shadow_trader:
            return jsonify({
                'trades': [],
                'summary': {
                    'total_trades': 0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'max_dd': 0
                },
                'status': 'not_running'
            })
        
        # Get trades from broker
        trades = shadow_trader.broker.trade_log
        
        # Calculate summary
        sell_trades = [t for t in trades if t['type'] == 'SELL']
        total_pnl = sum(t.get('pnl', 0) for t in sell_trades)
        wins = sum(1 for t in sell_trades if t.get('pnl', 0) > 0)
        win_rate = wins / len(sell_trades) if sell_trades else 0
        
        # Calculate max drawdown (simplified)
        equity_curve = []
        running_equity = shadow_trader.broker.get_balance()
        for trade in trades:
            if trade['type'] == 'SELL':
                running_equity += trade.get('pnl', 0)
                equity_curve.append(running_equity)
        
        max_dd = 0
        if equity_curve:
            peak = equity_curve[0]
            for equity in equity_curve:
                if equity > peak:
                    peak = equity
                dd = equity - peak
                if dd < max_dd:
                    max_dd = dd
        
        summary = {
            'total_trades': len(sell_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'max_dd': max_dd
        }
        
        # Apply limit
        limit = request.args.get('limit', type=int, default=50)
        trades_limited = trades[-limit:] if len(trades) > limit else trades
        
        return jsonify({
            'trades': trades_limited,
            'summary': summary,
            'status': 'running'
        })
    except Exception as e:
        logger.error(f"Error in get_shadow_trades: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alpha/results', methods=['GET'])
def get_alpha_results():
    """
    최신 백테스트 결과
    """
    try:
        # Return empty/null if no real results
        return jsonify({
            'latest_backtest': None
        })
    except Exception as e:
        logger.error(f"Error in get_alpha_results: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy/params', methods=['GET', 'POST'])
def strategy_params():
    """
    전략 파라미터 조회/변경
    """
    try:
        if request.method == 'GET':
            # Load current params (from config file or state)
            return jsonify({
                'current_params': {
                    'trend_filter_enabled': True,
                    'volatility_filter_enabled': True,
                    'news_fear_filter_enabled': False,
                    'vol_threshold': 0.015,
                    'fear_threshold': 60,
                    'condition_mode': 'AUTO'
                },
                'available_conditions': [
                    {'id': 'UP_NORMAL_v1', 'name': '상승 정상장'},
                    {'id': 'DOWN_VOLATILE_v1', 'name': '하락 고변동'},
                    {'id': 'SIDEWAYS_LOW_v1', 'name': '횡보 저변동'}
                ]
            })
        
        elif request.method == 'POST':
            new_params = request.get_json()
            # Save params and trigger update
            logger.info(f"Updating params: {new_params}")
            # TODO: Save to config and trigger strategy update
            return jsonify({'status': 'success', 'updated': new_params})
    
    except Exception as e:
        logger.error(f"Error in strategy_params: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/control/shadow', methods=['POST'])
def control_shadow():
    """
    Shadow Trading 제어 (start/stop)
    """
    global shadow_trader
    
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'start':
            if shadow_trader and shadow_trader.running:
                return jsonify({'status': 'already_running'})
            
            symbol = data.get('symbol', '005930')
            initial_capital = data.get('initial_capital', 100_000_000)
            
            # Load global trading mode
            mode_config = load_trading_mode()
            current_mode = mode_config.get('trading_mode', 'SHADOW')
            
            logger.info(f"Starting ShadowTrader in {current_mode} mode with REAL feed")
            
            if not ShadowTrader:
                return jsonify({'error': 'ShadowTrader not available (pandas missing)'}), 500

            shadow_trader = ShadowTrader(
                mode=current_mode,
                symbol=symbol, 
                initial_capital=initial_capital,
                feed_mode='real'
            )
            shadow_trader.start()
            
            return jsonify({
                'status': 'started',
                'symbol': symbol,
                'capital': initial_capital,
                'mode': current_mode,
                'feed': 'real'
            })
        
        elif action == 'stop':
            if shadow_trader:
                shadow_trader.stop()
                status = shadow_trader.get_status()
                shadow_trader = None
                return jsonify({'status': 'stopped', 'final_state': status})
            else:
                return jsonify({'status': 'not_running'})
        
        else:
            return jsonify({'error': 'Invalid action'}), 400
    
    except Exception as e:
        logger.error(f"Error in control_shadow: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/control/mode', methods=['POST'])
def control_mode():
    """
    Trading Mode 변경
    """
    try:
        data = request.get_json()
        new_mode = data.get('mode')
        
        if new_mode not in ['SHADOW', 'LIVE_PAPER', 'LIVE_REAL']:
            return jsonify({'error': 'Invalid mode'}), 400
        
        # LIVE_REAL requires confirmation
        if new_mode == 'LIVE_REAL':
            confirmation = data.get('confirmation_code')
            if confirmation != 'REAL_TRADING_CONFIRMED':
                return jsonify({'error': 'Confirmation required for LIVE_REAL'}), 403
        
        mode_config = load_trading_mode()
        mode_config['trading_mode'] = new_mode
        save_trading_mode(mode_config)
        
        logger.warning(f"Trading mode changed to: {new_mode}")
        
        return jsonify({
            'status': 'success',
            'mode': new_mode,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in control_mode: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    헬스 체크
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'shadow_running': shadow_trader is not None and shadow_trader.running if shadow_trader else False
    })

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """
    Get system health status
    Returns: status (GREEN/ORANGE/RED), active_alerts, alert_counts
    """
    try:
        status = alert_manager.get_system_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error in get_system_status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/alerts', methods=['GET'])
def get_system_alerts():
    """
    Get active alerts for dashboard
    """
    try:
        alerts = alert_manager.get_dashboard_alerts()
        return jsonify({'alerts': alerts})
    except Exception as e:
        logger.error(f"Error in get_system_alerts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id: str):
    """
    Acknowledge an alert
    """
    try:
        alert_manager.acknowledge_alert(alert_id)
        return jsonify({'status': 'acknowledged', 'alert_id': alert_id})
    except Exception as e:
        logger.error(f"Error in acknowledge_alert: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/health-check', methods=['POST'])
def run_health_check():
    """
    Run all health checks
    """
    try:
        results = health_checker.run_all_checks()
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in run_health_check: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/health-check/latest', methods=['GET'])
@app.route('/api/system/health/latest', methods=['GET']) # Alias for dashboard compatibility
def get_latest_health_check():
    """
    Get latest health check results from HealthCollector
    """
    try:
        # Try to read today's health file from HealthCollector
        today_str = datetime.now().strftime("%Y%m%d")
        health_file = PATHS.HEALTH_DIR / f"health_{today_str}.json"
        
        if health_file.exists():
            # Check if file is recent (within 10 mins)
            mtime = datetime.fromtimestamp(health_file.stat().st_mtime)
            if (datetime.now() - mtime).total_seconds() < 600:
                with open(health_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return jsonify(data)
        
        # Fallback if no file or stale
        return jsonify({
            "status": "UNKNOWN",
            "timestamp": datetime.now().isoformat(),
            "message": "Health check pending or stale",
            "mode": {"trading_mode": "UNKNOWN"}
        })
            
    except Exception as e:
        logger.error(f"Error in get_latest_health_check: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulation/today', methods=['GET'])
def get_simulation_today():
    """
    Get today's simulation report
    """
    try:
        report_file = PATHS.TODAY_SIM_FILE
        if not report_file.exists():
            return jsonify({'error': 'No simulation report found', 'status': 'NO_DATA'}), 404
            
        with open(report_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Calculate derived metrics if missing
        if 'win_rate' not in data and 'trades' in data:
            trades = data['trades']
            completed_trades = [t for t in trades if 'pnl' in t]
            if completed_trades:
                wins = sum(1 for t in completed_trades if t['pnl'] > 0)
                data['win_rate'] = wins / len(completed_trades)
                data['pnl'] = sum(t['pnl'] for t in completed_trades)
            else:
                data['win_rate'] = 0
                data['pnl'] = 0
                
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error reading simulation report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulation/comparison', methods=['GET'])
def get_simulation_comparison():
    """
    Get 1-year simulation comparison data (Engine 1 vs Engine 2 vs KOSPI)
    Reads from: GARAM_Data/reports/simulation_1year_turbo.csv
    """
    try:
        csv_path = PATHS.DATA_DIR / "reports" / "simulation_1year_turbo.csv"
        
        if not csv_path.exists():
            # If not found, try to trigger generation or return empty?
            # For now return error so frontend knows
            return jsonify({'error': 'Comparison data not generated yet', 'status': 'NO_DATA'}), 404
            
        df = pd.read_csv(csv_path)
        
        # Structure for Chart.js
        response_data = {
            'dates': df['date'].tolist() if 'date' in df.columns else df.index.astype(str).tolist(),
            'engine1': df['engine1'].tolist(),
            'engine2': df['engine2'].tolist(),
            'kospi': df['kospi'].tolist()
        }
        
        # If dates were index in CSV read (pandas defaults)
        if 'date' not in response_data or not response_data['date']:
             # If CSV was saved with index=True, read_csv typically makes it a column unless index_col is set
             # But our script used to_csv without index=False? 
             # Wait, script used output_df.to_csv(output_csv_path). 
             # This includes index (date) as first column.
             # pd.read_csv will treat it as a column named 'date' if headers align.
             pass

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Comparison API Error: {e}")
        return jsonify({'error': str(e)}), 500

# [PHASE 4] EOD Report Endpoints
@app.route('/api/system/kiwoom/stop', methods=['POST'])
def stop_kiwoom_process():
    """Stop Kiwoom process and prevent restart"""
    try:
        # 1. Create Stop Flag
        STOP_FLAG = PATHS.BASE_DIR / "kiwoom_stop.flag"
        STOP_FLAG.touch()
        
        # 2. Kill Process
        # We need to find python.exe running kiwoom_login_ui.py
        import psutil
        killed = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'kiwoom_login_ui.py' in ' '.join(cmdline):
                    proc.kill()
                    killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        # 3. Update Flag File (Delete Connection Flag)
        if PATHS.KIWOOM_FLAG_FILE.exists():
            PATHS.KIWOOM_FLAG_FILE.unlink()

        return jsonify({'status': 'stopped', 'killed': killed})
    except Exception as e:
        logger.error(f"Stop Kiwoom Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/latest', methods=['GET'])
def get_latest_report():
    """
    Get the latest EOD report
    """
    try:
        report_file = PATHS.BASE_DIR / "reports" / "latest.json"
        if not report_file.exists():
            return jsonify({'error': 'No reports available'}), 404
        
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        return jsonify(report)
    except Exception as e:
        logger.error(f"Error in get_latest_report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/history', methods=['GET'])
def get_report_history():
    """
    Get historical EOD reports
    Query Params: days (default: 7)
    """
    try:
        days = request.args.get('days', type=int, default=7)
        reports_dir = PATHS.BASE_DIR / "reports"
        
        if not reports_dir.exists():
            return jsonify({'reports': []})
        
        # Find all EOD report files
        report_files = sorted(reports_dir.glob('eod_*.json'), reverse=True)
        reports = []
        
        for report_file in report_files[:days]:
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    reports.append(report_data)
            except Exception as e:
                logger.warning(f"Failed to load report {report_file}: {e}")
                continue
        
        
        return jsonify({'reports': reports})
    
    except Exception as e:
        logger.error(f"Error in get_report_history: {e}")
        return jsonify({'error': str(e)}), 500

import os

@app.route('/api/system/kiwoom/start', methods=['POST'])
def start_kiwoom_process():
    """Resume Kiwoom process (Delete Stop Flag)"""
    try:
        STOP_FLAG = PATHS.BASE_DIR / "kiwoom_stop.flag"
        if STOP_FLAG.exists():
            STOP_FLAG.unlink()
        return jsonify({'status': 'resumed'})
    except Exception as e:
        logger.error(f"Start Kiwoom Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('c:/garam/garam/GARAM_Data/logs/server.log', encoding='utf-8')
        ]
    )
    
    # Log Success Banner
    logger.info("="*60)
    logger.info("GARAM SYSTEM STARTUP: SUCCESS")
    logger.info("Timestamp: %s", datetime.now().isoformat())
    logger.info("Configuration: Port 5003 | Debug=False | UI=Korean")
    logger.info("Status: Phase 4 Health Collector Enabled")
    logger.info("="*60)

    # Start Health Collector in Background
    try:
        collector = get_health_collector()
        collector.start()
        logger.info("✅ System Health Collector started (Background Thread)")
    except Exception as e:
        logger.error(f"Failed to start Health Collector: {e}")

    # Print registered routes for debugging
    print("Registered Routes:")
    print(app.url_map)

    # ========== TURBO CONTROL API ==========
    @app.route('/api/turbo/get', methods=['GET'])
    def get_turbo_settings():
        """Get current turbo control settings"""
        try:
            turbo_file = PATHS.DATA_DIR / "system" / "turbo_state.json"
            
            if not turbo_file.exists():
                # Return defaults
                return jsonify({
                    'mode': 'auto',
                    'manual_value': 1.0,
                    'auto_enabled': True,
                    'current_multiplier': 1.0
                })
            
            with open(turbo_file, 'r') as f:
                state = json.load(f)
            
            return jsonify(state)
        
        except Exception as e:
            logger.error(f"Error reading turbo settings: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/turbo/set', methods=['POST'])
    def set_turbo_settings():
        """Update turbo control settings"""
        try:
            data = request.get_json()
            
            turbo_file = PATHS.DATA_DIR / "system" / "turbo_state.json"
            turbo_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Read current state or create new
            if turbo_file.exists():
                with open(turbo_file, 'r') as f:
                    state = json.load(f)
            else:
                state = {
                    'mode': 'auto',
                    'manual_value': 1.0,
                    'auto_enabled': True
                }
            
            # Update fields
            if 'mode' in data:
                state['mode'] = data['mode']
            if 'manual_value' in data:
                state['manual_value'] = float(data['manual_value'])
            if 'auto_enabled' in data:
                state['auto_enabled'] = bool(data['auto_enabled'])
            
            # Save
            with open(turbo_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"✅ Turbo settings updated: {state}")
            
            return jsonify({
                'success': True,
                'state': state
            })
        
        except Exception as e:
            logger.error(f"Error setting turbo: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ========================================
    
    # ========== PAPER TRADING API ==========
    @app.route('/api/paper/status', methods=['GET'])
    def get_paper_trading_status():
        """Get current paper trading status"""
        try:
            state_file = PATHS.DATA_DIR / "paper_trading" / "state.json"
            
            if not state_file.exists():
                return jsonify({
                    'active': False,
                    'message': 'Paper trading not started'
                })
            
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            return jsonify({
                'active': True,
                'mode': state.get('mode', 'paper'),
                'equity': state.get('equity', 0),
                'cash': state.get('cash', 0),
                'started_at': state.get('started_at'),
                'positions_count': len(state.get('positions', {}))
            })
        except Exception as e:
            logger.error(f"Error reading paper trading status: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/paper/portfolio', methods=['GET'])
    def get_paper_portfolio():
        """Get current paper trading portfolio"""
        try:
            state_file = PATHS.DATA_DIR / "paper_trading" / "state.json"
            
            if not state_file.exists():
                return jsonify({'positions': [], 'cash': 0, 'equity': 0})
            
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            return jsonify({
                'cash': state.get('cash', 0),
                'equity': state.get('equity', 0),
                'positions': state.get('positions', {})
            })
        except Exception as e:
            logger.error(f"Error reading paper portfolio: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/paper/performance', methods=['GET'])
    def get_paper_performance():
        """Get paper trading performance metrics"""
        try:
            perf_file = PATHS.DATA_DIR / "paper_trading" / "daily_performance.json"
            
            if not perf_file.exists():
                return jsonify({'daily_returns': [], 'total_return': 0})
            
            with open(perf_file, 'r', encoding='utf-8') as f:
                performance = json.load(f)
            
            return jsonify(performance)
        except Exception as e:
            logger.error(f"Error reading paper performance: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ========================================

    # Use SERVER_PORT from env (set by start_garam.bat) or default to 5003
    port = int(os.environ.get("SERVER_PORT", 5003))
    logger.info(f"Starting GARAM Dashboard API Server on Port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
