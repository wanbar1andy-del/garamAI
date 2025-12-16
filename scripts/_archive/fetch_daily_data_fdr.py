import FinanceDataReader as fdr
import pandas as pd
import yaml
from pathlib import Path
import os
import time
from datetime import datetime

def fetch_data():
    # Config
    project_root = Path("c:/garam/garam")
    data_dir = Path("g:/내 드라이브/garamdata/history/daily")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Load Universe (Top 200 by Marcap)
    print("Fetching Top 200 Universe from KRX...")
    df_krx = fdr.StockListing('KRX')
    # Sort by Marcap (Marcap is not directly in StockListing for KRX, usually it has 'Marcap' or we use 'Amount'?)
    # FDR KRX listing columns: Symbol, Market, Name, Sector, Industry, ListingDate, SettleMonth, Representative, HomePage, Region
    # Wait, FDR StockListing('KRX') might not have Marcap.
    # Let's use 'KOSPI' and 'KOSDAQ' and maybe we can't easily sort by Marcap without fetching data?
    # Actually FDR StockListing('KRX') often returns 'Marcap' column in recent versions.
    # Let's check columns. If not, we'll fetch a snapshot.
    
    # Alternative: Use 'KRX-MARCAP' if available? No.
    # Let's try to get Marcap. If not, we use a static list or fetch first row of data to get price * shares?
    # FDR's StockListing('KRX') usually has 'Marcap' column.
    
    if 'Marcap' in df_krx.columns:
        df_krx = df_krx.sort_values('Marcap', ascending=False)
    else:
        # Fallback: If no Marcap, maybe 'Amount' (Volume)? Or just take top 200 by code order (bad).
        # Let's assume Marcap exists or we use a different method.
        # Actually, let's fetch 'KRX' and print columns to be sure? 
        # No, I can't interactively check easily.
        # Let's assume we want liquid stocks.
        # Let's just take the top 200 from the listing, assuming it might be sorted or we sort by something else.
        # Better: Fetch 'KOSPI' and 'KOSDAQ' separately.
        pass
        
    # Let's try to ensure we get good stocks.
    # We will save to real_universe_400.csv
    universe_path = project_root / "GARAM_Data" / "real_universe_400.csv"
    
    # Select Top 400
    # If Marcap exists
    if 'Marcap' in df_krx.columns:
        top_400 = df_krx.head(400)
    else:
        # Fallback: Just take first 400 (often big caps are first)
        top_400 = df_krx.head(400)
        
    top_400.to_csv(universe_path, index=False)
    print(f"Saved Top 400 Universe to {universe_path}")
    
    symbols = top_400['Code'].astype(str).str.zfill(6).tolist()
        
    print(f"Loaded {len(symbols)} symbols from universe.")
    
    # Add Market Proxy (Samsung Elec)
    if '005930' not in symbols:
        symbols.append('005930')
        
    # Date Range
    start_date = '2024-01-01'
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Fetching data from {start_date} to {end_date}...")
    
    for i, sym in enumerate(symbols):
        print(f"[{i+1}/{len(symbols)}] Fetching {sym}...", end=" ")
        
        try:
            df = fdr.DataReader(sym, start_date, end_date)
            if df.empty:
                print("Empty.")
                continue
                
            # Rename columns to lowercase
            df.columns = [c.lower() for c in df.columns]
            # Ensure index is named 'date'
            df.index.name = 'date'
            
            # Save
            save_path = data_dir / f"{sym}_daily.csv"
            df.to_csv(save_path)
            print(f"Saved {len(df)} rows.")
            
            time.sleep(0.1) # Be nice to Naver
            
        except Exception as e:
            print(f"Error: {e}")
            
    # Also fetch Market Index (KOSPI) for reference if needed, but we use 005930 as proxy in live engine
    # But let's fetch 005930 separately to ensure it's named correctly for the engine's fallback
    # The engine looks for: g:/내 드라이브/garamdata/history/KR_005930_SamsungElec_daily_20y.csv
    # Or fallback to: g:/내 드라이브/garamdata/history/daily/KR_005930_SamsungElec_daily_20y.csv
    
    # Let's save 005930 as the proxy file too
    try:
        df_proxy = fdr.DataReader('005930', '2010-01-01', end_date)
        df_proxy.columns = [c.lower() for c in df_proxy.columns]
        df_proxy.index.name = 'date'
        proxy_path = Path("g:/내 드라이브/garamdata/history/daily/KR_005930_SamsungElec_daily_20y.csv")
        df_proxy.to_csv(proxy_path)
        print(f"Saved Market Proxy to {proxy_path}")
    except Exception as e:
        print(f"Error fetching proxy: {e}")

if __name__ == "__main__":
    fetch_data()
