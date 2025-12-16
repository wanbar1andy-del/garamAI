"""
Fetch 20-Year Historical Data via Kiwoom API
Must be run in a 32-bit Python environment.
"""

import sys
import os
import time
import pandas as pd
from datetime import datetime
import pandas as pd
from datetime import datetime
import PyQt5
from PyQt5.QtWidgets import QApplication

# Fix for Qt platform plugin "windows" not found
dirname = os.path.dirname(PyQt5.__file__)
plugin_path = os.path.join(dirname, 'Qt5', 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
print(f"[DEBUG] Set QT_QPA_PLATFORM_PLUGIN_PATH to: {plugin_path}")

from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop

# Add project root to path
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root.parent))

from garam.config import PATHS

class KiwoomDataFetcher(QAxWidget):
    def __init__(self):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        
        self.login_loop = QEventLoop()
        self.request_loop = QEventLoop()
        
        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveTrData.connect(self._on_receive_tr_data)
        
        self.data = []
        self.remained_data = False
        
    def login(self):
        self.dynamicCall("CommConnect()")
        self.login_loop.exec_()
        
    def _on_event_connect(self, err_code):
        if err_code == 0:
            print("Connected to Kiwoom.")
        else:
            print(f"Connection Failed: {err_code}")
        self.login_loop.exit()
        
    def fetch_daily_data(self, code, date, output_file, is_index=False):
        print(f"Fetching data for {code} starting from {date} (Index: {is_index})...")
        self.data = []
        self.remained_data = True
        
        tr_code = "opt20006" if is_index else "opt10081"
        rq_name = f"{tr_code}_req"
        
        # Initial Request
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드" if not is_index else "업종코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)
        if not is_index:
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rq_name, tr_code, 0, "0101")
        self.request_loop.exec_()
        
        while self.remained_data:
            time.sleep(0.5) # Rate limit increased for stability
            print("Requesting next page...")
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드" if not is_index else "업종코드", code)
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)
            if not is_index:
                self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
                
            self.dynamicCall("CommRqData(QString, QString, int, QString)", rq_name, tr_code, 2, "0101")
            self.request_loop.exec_()
            
            # Optimization: Stop after 2 pages (~1200 days) for speed
            # We only need 6 months for this task.
            if len(self.data) >= 1200:
                print("Reached limit (1200 rows). Stopping fetch.")
                self.remained_data = False
                break
            
        # Save
        df = pd.DataFrame(self.data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y%m%d')
            df = df.sort_values('timestamp')
            
            # Ensure directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            df.to_csv(output_path, index=False)
            print(f"Saved {len(df)} rows to {output_path}")
        else:
            print(f"No data fetched for {code}")

    def fetch_top_volume_stocks(self, market_code="001"):
        """
        Fetch Top 10 stocks by volume.
        market_code: "001" (KOSPI), "101" (KOSDAQ)
        """
        print(f"Fetching Top 10 Volume Stocks for Market {market_code}...")
        self.data = []
        self.remained_data = False
        
        # opt10030: 당일거래량상위요청
        # 시장구분: 001(코스피), 정렬구분: 1(거래량), 관리종목포함: 0, 신용구분: 0, 거래량구분: 0, 가격구분: 0, 거래대금구분: 0
        self.dynamicCall("SetInputValue(QString, QString)", "시장구분", market_code)
        self.dynamicCall("SetInputValue(QString, QString)", "정렬구분", "1") 
        self.dynamicCall("SetInputValue(QString, QString)", "관리종목포함", "0") 
        
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10030_req", "opt10030", 0, "0101")
        self.request_loop.exec_()
        
        top_stocks = []
        for item in self.data:
            code = item['code']
            name = item['name']
            top_stocks.append((code, name))
            if len(top_stocks) >= 10:
                break
                
        return top_stocks
                
        return top_stocks

    def _on_receive_tr_data(self, screen_no, rq_name, tr_code, record_name, prev_next, data_len, err_code, msg1, msg2):
        if rq_name == "opt10030_req":
            count = self.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, rq_name)
            print(f"Received {count} rows for Top Volume.")
            
            for i in range(count):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "종목코드").strip()
                name = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "종목명").strip()
                
                self.data.append({
                    "code": code,
                    "name": name
                })
            self.request_loop.exit()
            
        elif rq_name in ["opt10081_req", "opt20006_req"]:
            count = self.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, rq_name)
            print(f"Received {count} rows. PrevNext: {prev_next}")
            
            for i in range(count):
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "일자").strip()
                open_ = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "시가").strip()
                high = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "고가").strip()
                low = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "저가").strip()
                close = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "현재가").strip()
                volume = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "거래량" if not "opt20006" in rq_name else "거래량").strip() 
                
                self.data.append({
                    "timestamp": date,
                    "open": abs(float(open_)) if "opt20006" in rq_name else abs(int(open_)), 
                    "high": abs(float(high)) if "opt20006" in rq_name else abs(int(high)),
                    "low": abs(float(low)) if "opt20006" in rq_name else abs(int(low)),
                    "close": abs(float(close)) if "opt20006" in rq_name else abs(int(close)),
                    "volume": abs(int(volume))
                })
                
            self.remained_data = (prev_next == "2")
            self.request_loop.exit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    fetcher = KiwoomDataFetcher()
    fetcher.login()
    
    # Target Directory: g:/내 드라이브/garamdata/history/daily
    target_dir = Path("g:/내 드라이브/garamdata/history/daily")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime("%Y%m%d")
    
    # Load Universe
    universe_path = Path("c:/garam/garam/configs/universe_top100.csv")
    target_stocks = {}
    
    if universe_path.exists():
        print(f"Loading universe from {universe_path}...")
        import csv
        with open(universe_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                target_stocks[row['symbol']] = row['name']
    else:
        print("Universe file not found. Using default list.")
        target_stocks = {
            "005930": "SamsungElec",
            "000660": "SKHynix"
        }

    print(f"\nTotal Stocks to Fetch: {len(target_stocks)}")
    
    # Fetch Data
    for i, (code, name) in enumerate(target_stocks.items()):
        # Sanitize name
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
        output_file = target_dir / f"{code}_daily.csv"
        
        print(f"[{i+1}/{len(target_stocks)}] Fetching {code} ({name})...")
        
        # Skip if recently fetched (today)
        if output_file.exists():
            mtime = datetime.fromtimestamp(output_file.stat().st_mtime).strftime("%Y%m%d")
            if mtime == today:
                print(f"  Skipping {code} (Already fetched today)")
                continue
        
        fetcher.fetch_daily_data(code, today, output_file, is_index=False)
        time.sleep(0.6) # Rate limit

    print("All downloads complete.")
    sys.exit()
