
import json
import csv
from datetime import datetime
from pathlib import Path

class ComplianceLogger:
    """
    [COMPLIANCE]
    Automated Justification & Audit Logger.
    Proves that every trade was based on OSS Logic, not manipulation.
    """
    LOG_DIR = Path("logs/compliance")
    
    def __init__(self):
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.daily_log_file = self.LOG_DIR / f"trade_justification_{datetime.now().strftime('%Y%m%d')}.csv"
        self._init_csv()
        
    def _init_csv(self):
        if not self.daily_log_file.exists():
            with open(self.daily_log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Symbol", "Action", "Price", "Logic_ID", "Market_Condition", "OSS_Diagnosis", "Justification_Hash"])

    def log_trade(self, symbol, action, price, logic_id, market_data: dict, oss_diagnosis: str):
        ts = datetime.now().isoformat()
        
        # Snapshot of Market Data at decision time
        condition_str = json.dumps(market_data)
        
        # Generate Integrity Hash (Proof of Immutable Logic)
        raw_proof = f"{ts}{symbol}{action}{price}{logic_id}{oss_diagnosis}"
        import hashlib
        justification_hash = hashlib.sha256(raw_proof.encode()).hexdigest()[:16]
        
        entry = [ts, symbol, action, price, logic_id, condition_str, oss_diagnosis, justification_hash]
        
        with open(self.daily_log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(entry)
            
        print(f"   [COMPLIANCE] Trade Logged: {justification_hash} | Reason: {oss_diagnosis}")
