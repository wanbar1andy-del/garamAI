
import json
from pathlib import Path
from datetime import datetime
import time

# 프로젝트 루트
project_root = Path(__file__).resolve().parent.parent.parent
order_dir = project_root / "garamdata/orders"
order_dir.mkdir(parents=True, exist_ok=True)

class OrderManager:
    """
    [Phase 4: EXECUTION]
    주문 요청 생성기.
    직접 Kiwoom API를 호출하지 않고, '요청 파일'을 생성하여
    GUI 프로세스(run_ingest_kiwoom.py)가 처리하도록 위임함.
    (QAxWidget 스레드 제약 해결 패턴)
    """
    
    def send_order(self, symbol, order_type, qty, price=0, price_type="00"):
        """
        주문 요청 파일 생성
        :param order_type: 'buy', 'sell'
        :param price_type: '00'(지정가), '03'(시장가)
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = f"req_{timestamp}_{symbol}.json"
        
        request_data = {
            "timestamp": timestamp,
            "symbol": symbol,
            "order_type": order_type, # buy/sell
            "qty": qty,
            "price": price,
            "price_type": price_type,
            "status": "pending"
        }
        
        file_path = order_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(request_data, f, indent=4)
            
        return str(file_path)

order_manager = OrderManager()
