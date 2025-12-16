"""
Verify Kiwoom 6-Month Minute Data Availability
Fetches opt10080 (Minute Data) for 005930 (Samsung Elec) to check history depth.
"""

import sys
import os
import time
from datetime import datetime, timedelta
import PyQt5
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop

# Fix for Qt platform plugin
dirname = os.path.dirname(PyQt5.__file__)
plugin_path = os.path.join(dirname, 'Qt5', 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

class KiwoomVerifier(QAxWidget):
    def __init__(self):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.login_loop = QEventLoop()
        self.request_loop = QEventLoop()
        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveTrData.connect(self._on_receive_tr_data)
        
        self.oldest_date = None
        self.remained_data = False
        self.target_date = datetime.now() - timedelta(days=180) # 6 months ago
        self.reached_target = False
        
    def login(self):
        print("Logging in...")
        self.dynamicCall("CommConnect()")
        self.login_loop.exec_()
        
    def _on_event_connect(self, err_code):
        if err_code == 0:
            print("Connected to Kiwoom.")
        else:
            print(f"Connection Failed: {err_code}")
        self.login_loop.exit()
        
    def verify_history(self, code="005930"):
        print(f"Verifying history depth for {code} (Target: {self.target_date.strftime('%Y-%m-%d')})...")
        
        # Initial Request
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "tick", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10080_req", "opt10080", 0, "0101")
        self.request_loop.exec_()
        
        page = 1
        while self.remained_data and not self.reached_target:
            time.sleep(0.3) # Rate limit
            print(f"Requesting page {page} (Oldest: {self.oldest_date})...")
            
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.dynamicCall("SetInputValue(QString, QString)", "tick", "1")
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10080_req", "opt10080", 2, "0101")
            self.request_loop.exec_()
            page += 1
            
            if page > 500: # Safety break (approx 500 * 900 bars = 450k bars ~ 1 year)
                print("Safety limit reached (500 pages).")
                break
                
        print("-" * 50)
        print(f"Verification Complete.")
        print(f"Oldest Date Reached: {self.oldest_date}")
        if self.oldest_date and datetime.strptime(self.oldest_date, "%Y%m%d%H%M%S") <= self.target_date:
            print("RESULT: SUCCESS (6 Months Data Available)")
        else:
            print("RESULT: FAIL (Less than 6 Months Data)")
            
    def _on_receive_tr_data(self, screen_no, rq_name, tr_code, record_name, prev_next, data_len, err_code, msg1, msg2):
        if rq_name == "opt10080_req":
            count = self.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, rq_name)
            
            if count > 0:
                # Check the last item (oldest in this batch)
                last_date = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, count-1, "체결시간").strip()
                self.oldest_date = last_date
                
                last_dt = datetime.strptime(last_date, "%Y%m%d%H%M%S")
                if last_dt <= self.target_date:
                    self.reached_target = True
            
            self.remained_data = (prev_next == "2")
            self.request_loop.exit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    verifier = KiwoomVerifier()
    verifier.login()
    verifier.verify_history()
    sys.exit()
