
import sys
import struct
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from datetime import datetime

def main():
    print(f"[Verify] Python: {sys.version}")
    bits = struct.calcsize("P") * 8
    print(f"[Verify] Bits: {bits}-bit")
    
    if bits != 32:
        print("[Verify] ERROR: Must run on 32-bit Python.")
        sys.exit(1)

    app = QApplication(sys.argv)
    ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
    
    # Check Connect State
    state = ocx.dynamicCall("GetConnectState()")
    print(f"[Verify] Connect State: {state} (1=Connected, 0=Disconnected)")
    
    if state == 1:
        # Check Server Type
        # GetLoginInfo("GetServerGubun") -> "1": Mock, Others(Empty): Real
        gubun = ocx.dynamicCall("GetLoginInfo(QString)", "GetServerGubun")
        print(f"[Verify] GetServerGubun: '{gubun}'")
        
        if gubun == "1":
            print(">>> [RESULT] MOCK SERVER (모의투자) <<<")
        else:
            print(">>> [RESULT] REAL SERVER (실전투자) <<<")
            
        # Optional: Masked Account
        acc = ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO").split(';')[0]
        if acc:
            masked = acc[:-3] + "***"
            print(f"[Verify] Account: {masked}")
            
    else:
        print("[Verify] Not Connected. Please login via Ingester UI first.")
        
    # Exit loop
    sys.exit(0)

if __name__ == "__main__":
    main()
