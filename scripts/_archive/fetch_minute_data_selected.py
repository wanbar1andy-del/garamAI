import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, QTimer

# Ensure 32-bit
if sys.maxsize > 2**32:
    print("Error: This script must be run in 32-bit Python.")
    sys.exit(1)

class KiwoomMinuteFetcher(QAxWidget):
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
            time.sleep(0.25) # Rate limit (3.6s per 1000? No, 0.2s is safe for 1 TR)
            
            # Check date limit
            if self.data:
                last_date = self.data[-1]['date'][:8]
                if last_date < target_date_limit:
                    print(f"Reached target date {last_date}. Stopping.")
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
    fetcher = KiwoomMinuteFetcher()
    fetcher.login()
    
    # Load Selected Symbols
    symbols_df = pd.read_csv("results/dgefinal_6m_portfolio_15pct/selected_symbols.csv")
    symbols = symbols_df['symbol'].astype(str).str.zfill(6).tolist()
    
    target_dir = Path("g:/내 드라이브/garamdata/history/minute")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Target: 6 months ago (20250501)
    target_date = "20250501"
    
    for sym in symbols:
        print(f"Fetching minute data for {sym}...")
        df = fetcher.fetch_minute_data(sym, target_date)
        
        # Save
        # Format date column to datetime for easier usage later
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S')
        df.sort_values('date', inplace=True)
        df.to_csv(target_dir / f"{sym}_1m.csv", index=False)
        print(f"Saved {len(df)} rows to {sym}_1m.csv")
        
    sys.exit()

if __name__ == "__main__":
    main()
