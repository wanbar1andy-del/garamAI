import sys
import pandas as pd
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

# Add project root
sys.path.insert(0, 'c:/garam')
from garam.config import PATHS
from garam.engine.controller import HybridController

def verify_dual_engine():
    print("--- Verifying Dual Engine Volatility Integration ---")
    
    controller = HybridController()
    
    # Run loop
    date = "2025-11-14"
    print(f"Testing Date: {date}")
    
    # Context Setup
    # Controller usually loads data internally via engine or we pass it? 
    # LegacyEngine loads via AlphaAggregator (which has internal data loader usually).
    # But AdvancedEngine needs 'market_data' in context.
    # In run_live_trading, we preload data.
    
    # We need to mimic the data loading of run_live_trading.py
    # Load Market Data
    market_data = {}
    # Load Universe
    uni = pd.read_csv(PATHS.DATA_DIR / "real_universe_400.csv")
    targets = uni['Code'].astype(str).str.zfill(6).tolist() if 'Code' in uni.columns else []
    targets = targets[:50] # Test with top 50 to save time
    
    print(f"Loading data for {len(targets)} stocks...")
    closes, opens, highs, lows, volumes = {}, {}, {}, {}, {}
    
    for sym in targets:
        f = PATHS.HISTORY_DIR / "daily" / f"{sym}_daily.csv"
        if f.exists():
            df = pd.read_csv(f)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            if pd.Timestamp(date) in df.index:
                closes[sym] = df['close']
                opens[sym] = df['open']
                highs[sym] = df['high']
                lows[sym] = df['low']
                if 'volume' in df.columns:
                    volumes[sym] = df['volume']
                else:
                    volumes[sym] = 0
                
    market_df_close = pd.DataFrame(closes)
    market_df_open = pd.DataFrame(opens)
    market_df_high = pd.DataFrame(highs)
    market_df_low = pd.DataFrame(lows)
    market_df_volume = pd.DataFrame(volumes)
    
    context = {
        'market_data': {
            'close': market_df_close,
            'open': market_df_open,
            'high': market_df_high,
            'low': market_df_low,
            'volume': market_df_volume
        },
        'universe': targets,
        'regime': 'R3_UP_BOX'
    }
    
    # Run Cycle
    result = controller.run_cycle(pd.Timestamp(date), context)
    
    # Verify Checks
    signals = result.get('signals', {})
    meta = result.get('meta', {})
    directives = result.get('directives', {})
    
    print("\n--- RESULTS ---")
    print(f"Controller Status: {meta.get('controller_status')}")
    print(f"Directives: {directives}")
    
    # 1. Check Vol Mode
    e2_meta = meta.get('engine2_meta', {})
    vol_mode = e2_meta.get('vol_mode')
    print(f"Market Vol Mode: {vol_mode}")
    
    if vol_mode in ['STABLE', 'VOL_WARNING', 'VOL_PANIC']:
        print("PASS: Volatility Timer is working.")
    else:
        print("FAIL: Volatility Timer output UNKNOWN or missing.")
        
    # 2. Check Sizing
    e1_meta = meta.get('engine1_meta', {})
    sizing_method = e1_meta.get('sizing_method')
    print(f"Sizing Method: {sizing_method}")
    
    if sizing_method == 'RiskParity':
        print("PASS: LegacyEngine used Risk Parity.")
    else:
        print("FAIL: LegacyEngine did not use Risk Parity.")
        
    # 3. Check Weights
    print("\nTop 5 Signals (Weights):")
    sorted_sigs = sorted(signals.items(), key=lambda x: x[1], reverse=True)[:5]
    for sym, w in sorted_sigs:
        print(f"{sym}: {w:.4f}")
        
    # Check if they sum to approx 1 (Legacy logic might scale to 100? or 1?)
    total_w = sum(signals.values()) if signals else 0
    print(f"Total Weight Sum: {total_w:.4f}")
    
    if 0.99 <= total_w <= 1.01:
        print("PASS: Weights sum to 1.0 (Risk Parity confirmed).")
    elif 99 <= total_w <= 101:
        print("PASS: Weights sum to 100 (Scaled Risk Parity confirmed).")
    else:
        print(f"WARNING: Weights sum to {total_w}, expected ~1.0 or ~100.0.")

if __name__ == "__main__":
    verify_dual_engine()
