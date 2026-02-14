
"""
Script: Ingest Short Selling History (2026)
Target: 2026-01-01 ~ 2026-12-31
TR: opt10014 (공매도추이요청)
"""
import sys
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QTimer, QEventLoop

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "GARAM_Data"
SHORT_DIR = DATA_DIR / "history" / "short_selling" / "2026"
SHORT_DIR.mkdir(parents=True, exist_ok=True)

class ShortSellingIngester:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self.on_connect)
        self.ocx.OnReceiveTrData.connect(self.on_receive_tr_data)
        
        self.loop = QEventLoop()
        self.tr_event_loop = QEventLoop()
        
        self.targets = self.load_universe()
        self.current_idx = 0
        self.delay_ms = 600
        
        self.summary_rows = []

    def load_universe(self):
        path = DATA_DIR / "real_universe_400.csv"
        if path.exists():
            df = pd.read_csv(path, dtype=str)
            if "symbol" in df.columns:
                return df["symbol"].tolist()
            elif len(df.columns) >= 1:
                 return df.iloc[:,0].tolist()
        return ["005930"] 

    def start(self):
        print("Logging in...")
        self.ocx.dynamicCall("CommConnect()")
        self.loop.exec_()
    
    def on_connect(self, err_code):
        if err_code == 0:
            print("Connected.")
            QTimer.singleShot(1000, self.process_next)
        else:
            print(f"Login Failed: {err_code}")
            sys.exit(1)

    def process_next(self):
        if self.current_idx >= len(self.targets):
            self.finish()
            return

        symbol = self.targets[self.current_idx]
        
        save_path = SHORT_DIR / f"{symbol}.csv"
        if save_path.exists():
            print(f"[{self.current_idx+1}/{len(self.targets)}] Skipping {symbol} (Already Exists)")
            self.current_idx += 1
            QTimer.singleShot(0, self.process_next)
            return
            
        print(f"[{self.current_idx+1}/{len(self.targets)}] Requesting Short Selling Data (2026) for {symbol}...")
        
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", symbol)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "시간구분", "1")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "시작일자", "20260101")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "종료일자", "20261231")
        
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", "req_short", "opt10014", 0, "1000")
        
        self.tr_event_loop.exec_()
        
        self.current_idx += 1
        QTimer.singleShot(self.delay_ms, self.process_next)

    def on_receive_tr_data(self, screen_no, rq_name, tr_code, record_name, prev_next, data_len, err_code, msg, splm_msg):
        if tr_code == "opt10014":
            symbol = self.targets[self.current_idx] 
            
            rows = []
            count = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, rq_name)
            
            total_short_vol = 0
            total_short_val = 0
            
            for i in range(count):
                date = self.get_comm_data(tr_code, rq_name, i, "일자")
                close = self.get_comm_data(tr_code, rq_name, i, "종가")
                short_vol = self.get_comm_data(tr_code, rq_name, i, "공매도수량")
                short_val = self.get_comm_data(tr_code, rq_name, i, "공매도금액")
                short_ratio = self.get_comm_data(tr_code, rq_name, i, "공매도거래비중")
                avg_price = self.get_comm_data(tr_code, rq_name, i, "공매도평균가")
                
                if not date.startswith("2026"): 
                     continue
                     
                sv = int(short_vol or 0)
                sval = int(short_val or 0)
                
                rows.append({
                    "date": date,
                    "close": int(close or 0),
                    "short_vol": sv,
                    "short_val": sval,
                    "short_ratio": float(short_ratio or 0.0),
                    "avg_price": int(avg_price or 0)
                })
                
                total_short_vol += sv
                total_short_val += sval
                
            if rows:
                df = pd.DataFrame(rows)
                df = df.sort_values("date")
                df.to_csv(SHORT_DIR / f"{symbol}.csv", index=False)
                
            self.summary_rows.append({
                "symbol": symbol,
                "total_short_vol_2026": total_short_vol,
                "total_short_val_2026": total_short_val,
                "data_points": len(rows)
            })
                
            self.tr_event_loop.quit()

    def get_comm_data(self, tr_code, rq_name, index, item_name):
        return self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, index, item_name).strip()

    def finish(self):
        print("All Done.")
        if self.summary_rows:
            map_df = pd.DataFrame(self.summary_rows)
            map_path = DATA_DIR / "short_selling_map_2026.csv"
            map_df.to_csv(map_path, index=False)
            print(f"Map Saved: {map_path}")
            
        self.loop.quit()
        sys.exit(0)

if __name__ == "__main__":
    ingester = ShortSellingIngester()
    ingester.start()
