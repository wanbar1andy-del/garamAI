"""
Fetch Champion Universe Data (v2)
- Target: Top 50 Liquid Stocks from Universe
- Period: 2025.05.01 ~ 2025.10.31 (6 Months)
- Data: Minute (1m) OHLCV
- Source: Kiwoom OpenAPI+ (Real Connection)
"""

import sys
import os
from pathlib import Path
import pandas as pd
import time
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop

# Ensure 32-bit
if sys.maxsize > 2**32:
    print("Error: This script must be run in 32-bit Python.")
    sys.exit(1)

class KiwoomFetcher(QAxWidget):
    def __init__(self):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.OnEventConnect.connect(self.on_connect)
        self.OnReceiveTrData.connect(self.on_receive_tr_data)
        
        self.login_loop = QEventLoop()
        self.request_loop = QEventLoop()
        self.data = []
        self.remained_data = False
        
    def login(self):
        self.dynamicCall("CommConnect()")
        self.login_loop.exec_()

    def on_connect(self, err_code):
        if err_code == 0:
            print("Connected to Kiwoom.")
        else:
            print(f"Connection Failed: {err_code}")
        self.login_loop.exit()

    def on_receive_tr_data(self, screen_no, rq_name, tr_code, record_name, prev_next, data_len, err_code, msg1, msg2):
        if rq_name == "opt10080_req":
            count = self.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, rq_name)
            
            for i in range(count):
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "체결시간").strip()
                open_ = abs(int(self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "시가").strip()))
                high = abs(int(self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "고가").strip()))
                low = abs(int(self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "저가").strip()))
                close = abs(int(self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "현재가").strip()))
                volume = abs(int(self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "거래량").strip()))
                
                self.data.append({
                    'date': date, # YYYYMMDDHHMMSS
                    'open': open_,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': volume
                })
            
            self.remained_data = (prev_next == "2")
            self.request_loop.exit()

    def fetch_minute_data(self, code, target_date_limit):
        self.data = []
        self.remained_data = True
        
        # Initial Request
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "틱범위", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10080_req", "opt10080", 0, "0101")
        self.request_loop.exec_()
        
        while self.remained_data:
            time.sleep(0.6) # Increased to 0.6s (Kiwoom limit is strictly 5 req / 1 sec burst, but sustained should be slower)
            
            # Check date limit
            if self.data:
                last_date = self.data[-1]['date'][:8]
                if last_date < target_date_limit:
                    break
            
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.dynamicCall("SetInputValue(QString, QString)", "틱범위", "1")
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10080_req", "opt10080", 2, "0101")
            self.request_loop.exec_()
            
            print(f"  Fetched {len(self.data)} rows... Last: {self.data[-1]['date']}")
            
        return pd.DataFrame(self.data)

def main():
    app = QApplication(sys.argv)
    fetcher = KiwoomFetcher()
    fetcher.login()
    
    # 1. Load Universe
    universe_path = Path("configs/universe_top100.csv")
    if not universe_path.exists():
        print("Universe file not found.")
        sys.exit(1)
        
    df = pd.read_csv(universe_path)
    # Sort by Market Cap or Volume (Assuming 'market_cap' or similar column exists, or just take top 50)
    # If no sorting column, take top 50 as is (assuming file is already sorted)
    top_50 = df.head(50)['symbol'].astype(str).str.zfill(6).tolist()
    
    print(f"Targeting Top 50 Symbols: {top_50[:5]} ...")
    
    target_dir = Path("g:/내 드라이브/garamdata/history/minute")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Target: 2 Years (2023.11.01 ~ )
    target_date = "20231101"
    
    for i, sym in enumerate(top_50):
        print(f"[{i+1}/{len(top_50)}] Fetching {sym}...")
        
        save_path = target_dir / f"{sym}_1m.csv"
        
        # Force re-fetch for longer history (Disable skip)
        # if save_path.exists(): ...
        
        try:
            data = fetcher.fetch_minute_data(sym, target_date)
            
            # Process
            data['date'] = pd.to_datetime(data['date'], format='%Y%m%d%H%M%S')
            data.sort_values('date', inplace=True)
            data = data.drop_duplicates(subset=['date'])
            
            # Filter by date range (just in case)
            data = data[data['date'] >= pd.to_datetime(target_date)]
            
            data.to_csv(save_path, index=False)
            print(f"  Saved {len(data)} rows to {save_path}")
            
            time.sleep(5.0) # Increased to 5.0s to cool down between stocks
            
        except Exception as e:
            print(f"  Error fetching {sym}: {e}")
            continue
            
    print("All Done.")
    sys.exit()

if __name__ == "__main__":
    main()
