"""
Direct KR Intraday Data Collection
Collects 1-minute data from Kiwoom using direct QAxWidget (no pandas dependency).
"""

import sys
import os
import csv
import time
from datetime import datetime
from pathlib import Path
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QEventLoop, QTimer

# Setup paths
project_root = Path(__file__).parent.parent
data_dir = project_root / "GARAM_Data" / "minute" / "kr"
data_dir.mkdir(parents=True, exist_ok=True)

class KiwoomCollector:
    def __init__(self):
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.login_loop = QEventLoop()
        self.tr_loop = QEventLoop()
        
        # Connect signals
        self.ocx.OnEventConnect.connect(self._on_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
        
        self.remained_data = False
        self.received_data = []
        
    def _on_connect(self, err_code):
        if err_code == 0:
            print("[INFO] Connected to Kiwoom")
        else:
            print(f"[ERROR] Connection failed: {err_code}")
        self.login_loop.exit()
        
    def _on_receive_tr_data(self, screen_no, rq_name, tr_code, record_name, prev_next, data_len, err_code, msg1, msg2):
        if rq_name == "opt10080_req":
            self.remained_data = (prev_next == '2')
            count = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, rq_name)
            print(f"[INFO] Received {count} records")
            
            for i in range(count):
                # Format: current_price, volume, time, open, high, low
                # Note: Prices are absolute values (remove +/- sign)
                time_str = self._get_comm_data(tr_code, rq_name, i, "체결시간")
                open_price = abs(int(self._get_comm_data(tr_code, rq_name, i, "시가")))
                high_price = abs(int(self._get_comm_data(tr_code, rq_name, i, "고가")))
                low_price = abs(int(self._get_comm_data(tr_code, rq_name, i, "저가")))
                close_price = abs(int(self._get_comm_data(tr_code, rq_name, i, "현재가")))
                volume = abs(int(self._get_comm_data(tr_code, rq_name, i, "거래량")))
                
                self.received_data.append({
                    'datetime': time_str,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                })
                
            self.tr_loop.exit()

    def _get_comm_data(self, tr_code, rq_name, index, item_name):
        return self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, index, item_name).strip()

    def login(self):
        self.ocx.dynamicCall("CommConnect()")
        self.login_loop.exec_()

    def collect_stock_data(self, code, date_str):
        print(f"[INFO] Collecting data for {code}...")
        self.received_data = []
        
        # Set input
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "틱범위", "1:1분")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        
        # Request
        ret = self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10080_req", "opt10080", 0, "0101")
        if ret != 0:
            print(f"[ERROR] Failed to request data: {ret}")
            return
            
        self.tr_loop.exec_()
        time.sleep(0.5)  # Rate limit
        
        # Save to CSV
        if self.received_data:
            filename = data_dir / f"{code}.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['datetime', 'open', 'high', 'low', 'close', 'volume'])
                writer.writeheader()
                writer.writerows(self.received_data)
            print(f"[SUCCESS] Saved {len(self.received_data)} rows to {filename}")
        else:
            print("[WARN] No data received")

def main():
    app = QApplication(sys.argv)
    collector = KiwoomCollector()
    
    print("Logging in...")
    collector.login()
    
    # Test with Samsung Electronics
    collector.collect_stock_data("005930", datetime.now().strftime("%Y%m%d"))
    
    sys.exit(0)

if __name__ == "__main__":
    main()
