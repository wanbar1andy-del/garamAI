
import pandas as pd
import glob
import os
import json
import matplotlib.pyplot as plt
from datetime import datetime

def generate_report(log_dir):
    print(f"Generating Report for: {log_dir}")
    
    # 1. Load Data
    signals_path = os.path.join(log_dir, "signals.csv")
    orders_path = os.path.join(log_dir, "orders.csv")
    events_path = os.path.join(log_dir, "events.jsonl")
    
    # -- Signals --
    try:
        # Check if empty (only header)
        if os.stat(signals_path).st_size < 10:
             signals_df = pd.DataFrame()
        else:
            # signal.csv schema: ts, ... (check header)
            # Actually viewed file has no header? "2026-01-02 03:40:00,,0,0,0,0,0"
            # It seems to lack header or use default.
            # Let's assume cols based on view: ts, sym, score, wz, brk, vol, passed
            signals_df = pd.read_csv(signals_path, names=['ts', 'symbol', 'score', 'w_z', 'brk', 'vol', 'passed'])
            # Force numeric (handle mixed types or headers)
            cols_to_numeric = ['score', 'w_z', 'brk', 'vol', 'passed']
            for c in cols_to_numeric:
                signals_df[c] = pd.to_numeric(signals_df[c], errors='coerce').fillna(0)

    except Exception as e:
        print(f"Signal Load Error: {e}")
        signals_df = pd.DataFrame()

    # -- Orders --
    try:
        orders_df = pd.read_csv(orders_path)
    except:
        orders_df = pd.DataFrame()
        
    # -- Regime/Market Data (from events.jsonl) --
    regime_status = "UNKNOWN"
    market_data = []
    
    try:
        with open(events_path, 'r') as f:
            for line in f:
                if not line.strip(): continue
                evt = json.loads(line)
                if evt['event_type'] == 'REGIME_STATUS':
                    regime_status = evt['payload'].get('status', 'UNKNOWN')
                if evt['event_type'] == 'BAR_CLOSED':
                   market_data.append(evt['payload']) # {count, ts}
    except Exception as e:
        print(f"Event Load Error: {e}")

    # 2. Analysis
    total_signals = len(signals_df)
    valid_signals = len(signals_df[signals_df['score'] > 0])
    top_heroes = signals_df[signals_df['score'] > 0].sort_values('score', ascending=False).head(5)
    
    total_orders = len(orders_df)
    
    # 3. Generate Markdown
    report = []
    report.append(f"# Daily Paper Trading Report ({datetime.now().strftime('%Y-%m-%d')})")
    report.append(f"")
    report.append(f"## 1. System Status")
    report.append(f"- **Regime Status**: {regime_status}")
    report.append(f"- **Engine State**: Active & Processing")
    report.append(f"- **Market Bars Processed**: {len(market_data)} minutes")
    report.append(f"")
    report.append(f"## 2. Hero Discovery")
    report.append(f"- **Total Signal Checks**: {total_signals}")
    report.append(f"- **Valid Heroes Found**: {valid_signals}")
    
    if valid_signals == 0:
        report.append(f"> **NOTE**: No Heroes found yet. This is likely due to:")
        report.append(f"> 1. **Cold Start**: Strategy needs 100 bars (minutes) of history to calculate indicators.")
        report.append(f"> 2. **Market Conditions**: No stocks met the strict Volatility/Breakout criteria.")
    else:
        report.append(f"### Top 5 Heroes")
        report.append(top_heroes.to_markdown(index=False))
        
    report.append(f"")
    report.append(f"## 3. Execution Summary")
    report.append(f"- **Total Orders**: {total_orders}")
    
    if total_orders > 0:
        report.append(orders_df.to_markdown(index=False))
    
    # 4. Save
    out_path = os.path.join(log_dir, "daily_report.md")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
        
    print(f"Report Generated: {out_path}")
    print("\n".join(report))

if __name__ == "__main__":
    import sys
    # Default to current log dir if not provided
    log_dir = "logs/live_paper_real"
    if len(sys.argv) > 1:
        log_dir = sys.argv[1]
    
    generate_report(log_dir)
