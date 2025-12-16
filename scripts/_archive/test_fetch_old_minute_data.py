"""
Test Fetch Old Minute Data (2 Years Ago)
Target: 005930 (Samsung Electronics)
Goal: Verify if Kiwoom provides minute data beyond 1 year.
"""

import sys
import time
import pandas as pd
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop

# Ensure 32-bit
if sys.maxsize > 2**32:
    print("Error: This script must be run in 32-bit Python.")
    sys.exit(1)

class KiwoomTester(QAxWidget):
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
        if rq_name == "test_minute_req":
            count = self.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, rq_name)
            
            # Get first and last date in this block for logging
            first_date = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "체결시간").strip()
            last_date = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, count-1, "체결시간").strip()
            
            print(f"  Received Block: {count} rows. Range: {first_date} ~ {last_date}")
            
            for i in range(count):
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "체결시간").strip()
                close = abs(int(self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "현재가").strip()))
                self.data.append({'date': date, 'close': close})
            
            self.remained_data = (prev_next == "2")
            self.request_loop.exit()

    def fetch_data(self, code, target_date):
        self.data = []
        self.remained_data = True
        
        print(f"Fetching data for {code} until {target_date}...")
        
        # Initial Request
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "틱범위", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "test_minute_req", "opt10080", 0, "0101")
        self.request_loop.exec_()
        
        while self.remained_data:
            time.sleep(0.5)
            
            last_date = self.data[-1]['date'][:8]
            if last_date < target_date:
                print(f"Reached target date {target_date}. Stopping.")
                break
                
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.dynamicCall("SetInputValue(QString, QString)", "틱범위", "1")
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "test_minute_req", "opt10080", 2, "0101")
            self.request_loop.exec_()
            
        return pd.DataFrame(self.data)

def main():
    app = QApplication(sys.argv)
    tester = KiwoomTester()
    tester.login()
    
    # Target: 005930, 2 Years ago (20231101)
    df = tester.fetch_data("005930", "20231101")
    
    print("-" * 30)
    print(f"Total Rows: {len(df)}")
    if not df.empty:
        print(f"Date Range: {df.iloc[0]['date']} ~ {df.iloc[-1]['date']}")
    
    # Save for inspection
    df.to_csv("test_old_data_005930.csv", index=False)
    print("Saved to test_old_data_005930.csv")
    
    sys.exit()

if __name__ == "__main__":
    main()
