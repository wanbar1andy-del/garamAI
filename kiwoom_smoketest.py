# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, QTimer

class Kiwoom:
    def __init__(self):
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.login_loop = QEventLoop()
        self.connected = False
        self.err_code = None

    def comm_connect(self):
        self.ocx.dynamicCall("CommConnect()")
        self.login_loop.exec_()
        return self.connected, self.err_code

    def _on_event_connect(self, err_code):
        self.err_code = err_code
        self.connected = (err_code == 0)
        self.login_loop.exit()

    def get_connect_state(self) -> int:
        return int(self.ocx.dynamicCall("GetConnectState()"))

    def get_login_info(self, tag: str) -> str:
        return str(self.ocx.dynamicCall("GetLoginInfo(QString)", tag))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()

    ok, err = kiwoom.comm_connect()
    state = kiwoom.get_connect_state()

    print(f"[LOGIN] ok={ok} err={err} state={state}")
    if not ok:
        print("로그인 실패. (HTS/KOA Studio 버전처리 팝업/동시 실행 충돌 여부 확인)")
        sys.exit(1)

    acc_cnt = kiwoom.get_login_info("ACCOUNT_CNT")
    accounts = kiwoom.get_login_info("ACCLIST")  # 세미콜론 구분
    user = kiwoom.get_login_info("USER_NAME")

    print(f"[INFO] USER_NAME={user}")
    print(f"[INFO] ACCOUNT_CNT={acc_cnt}")
    print(f"[INFO] ACCLIST={accounts}")

    print("[OK] Kiwoom OpenAPI+ 연결 완료")
    QTimer.singleShot(200, app.quit)
    app.exec_()
