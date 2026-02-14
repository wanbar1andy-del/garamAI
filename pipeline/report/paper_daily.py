import os
import pandas as pd
import glob
import argparse
from datetime import datetime

def analyze_paper_logs(log_dir):
    print(f"=== Paper Live Daily Report ===")
    print(f"Log Dir: {log_dir}")
    
    # 1. Orders Analysis
    orders_path = os.path.join(log_dir, 'orders.csv')
    if not os.path.exists(orders_path):
        print("[!] orders.csv not found.")
        return

    try:
        df_ord = pd.read_csv(orders_path)
        print(f"\n[Orders Summary]")
        print(f"Total Rows: {len(df_ord)}")
        
        # New Orders vs Updates
        if 'event' in df_ord.columns:
            print(df_ord['event'].value_counts())
            
        # Unique Orders
        unique_orders = df_ord['id'].nunique()
        print(f"Unique Orders: {unique_orders}")
        
        # Status Counts (Latest Status per ID)
        # Sort by ts to get latest
        df_ord['ts'] = pd.to_datetime(df_ord['ts'])
        df_latest = df_ord.sort_values('ts').groupby('id').last()
        print("\n[Final Status Distribution]")
        print(df_latest['status'].value_counts())
        
        # Reject Reasons
        rejects = df_latest[df_latest['status'] == 'REJECTED']
        if not rejects.empty:
            print("\n[Rejection Reasons]")
            print(rejects['reject_reason'].value_counts())
            
    except Exception as e:
        print(f"[!] Error reading orders.csv: {e}")

    # 2. Fills Analysis (PnL)
    fills_path = os.path.join(log_dir, 'fills.csv')
    if os.path.exists(fills_path):
        try:
            df_fills = pd.read_csv(fills_path)
            print(f"\n[Fills Summary]")
            print(f"Total Fills: {len(df_fills)}")
            
            if not df_fills.empty:
                buy_amt = df_fills[df_fills['side']=='BUY']['fill_px'] * df_fills[df_fills['side']=='BUY']['qty']
                sell_amt = df_fills[df_fills['side']=='SELL']['fill_px'] * df_fills[df_fills['side']=='SELL']['qty']
                
                print(f"Total Buy Notional: {buy_amt.sum():,.0f}")
                print(f"Total Sell Notional: {sell_amt.sum():,.0f}")
                
                # Crude PnL (Real PnL requires FIFO matching, but Net Flow is a proxy for cash change)
                # Cash Change = Sells - Buys - Fees (fees implicitly reduced form cash in engine, but here we see fill_px)
                # Ideally check cash delta from logs, but here just raw volume.
                
        except Exception as e:
            print(f"[!] Error reading fills.csv: {e}")
            
    # 3. Events Analysis (Halt/Bar)
    events_path = os.path.join(log_dir, 'events.jsonl')
    if os.path.exists(events_path):
        try:
            df_evt = pd.read_json(events_path, lines=True)
            # Determine column name ('type' vs 'event')
            col = 'type' if 'type' in df_evt.columns else ('event' if 'event' in df_evt.columns else None)
            
            if col is None:
                print(f"[!] Unknown event schema. Columns: {df_evt.columns.tolist()}")
                return

            print(f"\n[Events Summary]")
            print(df_evt[col].value_counts())
            
            # Check Bar Closures
            bars = df_evt[df_evt[col] == 'BAR_CLOSED']
            if not bars.empty:
                print(f"Bar Closures: {len(bars)} (First: {bars['ts'].min()}, Last: {bars['ts'].max()})")
                
            # Check Halts
            halts = df_evt[df_evt[col] == 'HALT_TRIGGER']
            if not halts.empty:
                print(f"\n[!!!] HALT TRIGGERED: {len(halts)} times")
                print(halts[['ts', 'data']])

            # Check Risk Triggers (TIME_STOP ratio)
            risks = df_evt[df_evt[col] == 'RISK_TRIGGER']
            if not risks.empty:
                total_risk = len(risks)
                time_stops = len(risks[risks['data'].apply(lambda x: x.get('reason') == 'TIME_STOP')])
                print(f"\n[Risk Triggers] Total: {total_risk}")
                print(f"TIME_STOP: {time_stops} ({time_stops/total_risk*100:.1f}%)")
                
        except Exception as e:
            print(f"[!] Error reading events.jsonl: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_dir", type=str, default="logs/phase30/paper", help="Log directory to analyze")
    args = parser.parse_args()
    
    analyze_paper_logs(args.log_dir)
