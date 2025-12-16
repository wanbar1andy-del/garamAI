# garam_core/live/kiwoom_wrapper.py
from __future__ import annotations

from typing import List, Dict, Any, Callable
from pathlib import Path

from PyQt5.QtCore import QEventLoop, QObject
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget

import pandas as pd
from datetime import datetime


class KiwoomWrapper(QAxWidget):
    """
    Kiwoom OpenAPI+ Wrapper.
    Handles Login, Realtime Data (Tick), TR Requests (Orders, Balance).
    """

    def __init__(
        self,
        on_tick: Callable[[str, float, int, datetime], None],
        on_position_update: Callable[[str, float], None],
        on_cash_update: Callable[[float], None],
        app: QApplication | None = None,
    ):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

        self._on_tick = on_tick
        self._on_position_update = on_position_update
        self._on_cash_update = on_cash_update
        self._app = app

        self.connected = False
        self.account_no: str | None = None

        self._login_loop: QEventLoop | None = None
        self._tr_loop: QEventLoop | None = None

        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.OnReceiveRealData.connect(self._on_receive_real_data)
        self.OnReceiveChejanData.connect(self._on_receive_chejan_data)

    def login(self):
        self.dynamicCall("CommConnect()")
        self._login_loop = QEventLoop()
        self._login_loop.exec_()

        accounts = self.dynamicCall("GetLoginInfo(QString)", "ACCNO")
        if accounts:
            self.account_no = accounts.split(";")[0]
        else:
            print("[KIWOOM] No account found.")

    def _on_event_connect(self, err_code):
        if err_code == 0:
            print("[KIWOOM] Login success")
            self.connected = True
        else:
            print(f"[KIWOOM] Login failed: {err_code}")
            self.connected = False

        if self._login_loop is not None:
            self._login_loop.exit()

    def register_realtime(self, screen_no: str, symbols: List[str]):
        # Example FID list: 10(Price), 15(Vol), 20(Time)
        fid_list = "10;15;20" 
        code_list = ";".join(symbols)
        self.dynamicCall(
            "SetRealReg(QString, QString, QString, QString)",
            screen_no,
            code_list,
            fid_list,
            "0",  # 0: Replace
        )

    def unregister_realtime_all(self):
        self.dynamicCall("SetRealRemove(QString, QString)", "ALL", "ALL")

    def _request_tr(self, rqname: str, trcode: str, next_: int, screen_no: str):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next_, screen_no)
        self._tr_loop = QEventLoop()
        self._tr_loop.exec_()

    def request_account_balance(self):
        if not self.account_no:
            return
        
        # Example: opw00018
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_no)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "") 
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")

        self._request_tr("ACCOUNT_BALANCE", "opw00018", 0, "2000")

    def request_deposit(self):
        if not self.account_no:
            return
        
        # Example: opw00004
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_no)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")

        self._request_tr("DEPOSIT", "opw00004", 0, "2001")

    def send_order_wrapper(
        self,
        rqname: str,
        screen_no: str,
        order_type: int, # 1:Buy, 2:Sell
        code: str,
        qty: int,
        price: int,
        hoga: str,       # "00":Limit, "03":Market
        org_order_no: str,
    ):
        if not self.account_no:
            return -1

        ret = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            rqname,
            screen_no,
            self.account_no,
            order_type,
            code,
            qty,
            price,
            hoga,
            org_order_no,
        )
        return ret

    def _on_receive_tr_data(self, scr_no, rqname, trcode, recordname, prev_next, data_len, err_code, msg1, msg2):
        if rqname == "ACCOUNT_BALANCE":
            cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            for i in range(cnt):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목번호").strip()
                qty = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "보유수량").strip()
                code = code.replace("A", "")
                try:
                    self._on_position_update(code, float(qty))
                except ValueError:
                    pass

        elif rqname == "DEPOSIT":
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "예수금").strip()
            try:
                self._on_cash_update(float(deposit))
            except ValueError:
                pass
        
        if self._tr_loop:
            self._tr_loop.exit()

    def _on_receive_real_data(self, code, real_type, real_data):
        if real_type == "주식체결":
            # FID 10: Price, 15: Volume
            p_str = self.dynamicCall("GetCommRealData(QString, int)", code, 10).strip()
            v_str = self.dynamicCall("GetCommRealData(QString, int)", code, 15).strip()
            
            try:
                # Kiwoom price can be negative (abs is price, sign is direction)
                price = abs(float(p_str))
                volume = abs(int(v_str))
                self._on_tick(code, price, volume, datetime.now())
            except ValueError:
                pass

    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        # Implement real-time order/balance update logic here
        pass
