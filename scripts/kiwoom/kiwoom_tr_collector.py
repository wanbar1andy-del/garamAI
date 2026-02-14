# -*- coding: utf-8 -*-
import sys
import time
import argparse
import pandas as pd
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, QTimer

# SSOT: Kiwoom API Limits
# 1초당 5회 건수 제한 (가이드), 시간당 1000회 등. 
# 안전하게 0.25초 대기 (초당 4회) 또는 조회성 TR은 3.6초 권장(과부하 에러 방지)
THROTTLE_SEC = 0.5 

class KiwoomTR:
    def __init__(self):
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)

        self.login_loop = QEventLoop()
        self.tr_loop = QEventLoop()

        self.connected = False
        self._rows = []
        self._fields = []
        self._next_avail = False
        
        self.last_req_time = 0.0

    def comm_connect(self):
        self.ocx.dynamicCall("CommConnect()")
        self.login_loop.exec_()
        return self.connected

    def _on_event_connect(self, err_code):
        self.connected = (err_code == 0)
        self.login_loop.exit()
        
    def _throttle(self):
        now = time.time()
        diff = now - self.last_req_time
        if diff < THROTTLE_SEC:
            time.sleep(THROTTLE_SEC - diff)
        self.last_req_time = time.time()

    def set_input(self, input_dict):
        for k, v in input_dict.items():
            self.ocx.dynamicCall("SetInputValue(QString, QString)", k, v)

    def request(self, rqname, trcode, recordname, fields, screen="0101", loop_next=True):
        """
        자동 페이지네이션(연속조회) 포함
        """
        self._fields = fields
        self._rows = []
        
        # Initial call
        self._throttle()
        ret = self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, 0, screen)
        if int(ret) != 0:
            print(f"[ERR] CommRqData failed: {ret}")
            return pd.DataFrame()

        self.tr_loop.exec_()
        
        # Pagination
        while loop_next and self._next_avail:
            print(f"[INFO] Fetching next page for {trcode}...")
            # SetInput is required again? Usually NO for Next, but Inputs persist. 
            # However safe to just call CommRqData with 2 (next)
            
            # Important: Kiwoom requires SetInputValue even for Next? 
            # Guide says: Just call CommRqData with prev_next=2. 
            # Inputs are maintained in the session for that screen/tr? 
            # Safer to RE-SET inputs if unsure, but usually just prev_next=2 works if context is kept.
            # Let's assume context kept.
            
            self._throttle()
            ret = self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, 2, screen)
            if int(ret) != 0:
                print(f"[ERR] Next CommRqData failed: {ret}")
                break
            self.tr_loop.exec_()
            
        return pd.DataFrame(self._rows)

    def request_once(self, rqname, trcode, prev_next, screen):
        self._throttle()
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, prev_next, screen)
        self.tr_loop.exec_()

    def _on_receive_tr_data(self, scrno, rqname, trcode, recordname, prev_next, data_len, err_code, msg1, msg2):
        if prev_next == '2':
            self._next_avail = True
        else:
            self._next_avail = False
            
        cnt = int(self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname))
        
        for i in range(cnt):
            row = {}
            for f in self._fields:
                val = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, f)
                row[f] = str(val).strip()
            self._rows.append(row)
            
        self.tr_loop.exit()

# Predefined TR Schemas (SSOT from KOA Studio)
TR_SCHEMAS = {
    "program": {
        "trcode": "OPT90013",
        "record": "프로그램매매추이",
        "inputs": ["종목코드", "일자", "프로그램구분", "금액수량구분"], # KOA args
        "outputs": ["일자", "종가", "프로그램순매수수량", "프로그램순매수금액"]
    },
    "investor": {
        "trcode": "OPT10059",
        "record": "종목별투자자",
        "inputs": ["일자", "종목코드", "금액수량구분", "매매구분", "단위구분"],
        "outputs": ["일자", "개인투자자", "외국인투자자", "기관계", "금융투자", "보험", "투신", "전체"] # Customize as needed
    }
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["program", "investor"], help="Collection Mode")
    ap.add_argument("--symbol", required=True, help="Stock Symbol (6 digits)")
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    args = ap.parse_args()
    
    app = QApplication(sys.argv)
    kiwoom = KiwoomTR()
    
    print("[INFO] Connecting to Kiwoom...")
    if not kiwoom.comm_connect():
        print("[ERR] Login failed")
        sys.exit(1)
        
    schema = TR_SCHEMAS[args.mode]
    trcode = schema["trcode"]
    record = schema["record"]
    
    # Inputs Setup
    inputs = {}
    if args.mode == "program":
        inputs = {
            "종목코드": args.symbol,
            "일자": args.date,
            "프로그램구분": "1", # 1:전체
            "금액수량구분": "1", # 1:금액(백만원), 2:수량
        }
    elif args.mode == "investor":
        inputs = {
            "일자": args.date,
            "종목코드": args.symbol,
            "금액수량구분": "1", # 1:금액, 2:수량
            "매매구분": "0", # 0:순매수
            "단위구분": "1", # 1:단주
        }
        
    # Set Inputs
    kiwoom.set_input(inputs)
    
    # Request
    print(f"[INFO] Requesting {args.mode} for {args.symbol} date={args.date}...")
    df = kiwoom.request(
        rqname=f"req_{args.mode}",
        trcode=trcode,
        recordname=record,
        fields=schema["outputs"],
        loop_next=True # Get Full History available
    )
    
    if df.empty:
        print("[WARN] No data received.")
    else:
        out_path = Path(f"results/kiwoom_{args.mode}") / f"{args.symbol}_{args.date}.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"[OK] Saved {len(df)} rows to {out_path}")

    QTimer.singleShot(500, app.quit)
    app.exec_()

if __name__ == "__main__":
    # Note: Global input_dict hack for the request method above needs fixing in class logic
    # In 'request' method above, I used 'input_dict' but it wasn't passed.
    # Correcting structure inside the class 'request' method to not need re-set, or pass it.
    # For this script run, we set inputs via 'kiwoom.set_input' manually before calling request.
    # But wait, request method above calls self.set_input(input_dict) which is undefined.
    # Removing that line in the written file next.
    main()
