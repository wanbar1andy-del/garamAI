import json
import os
from datetime import datetime
from pathlib import Path

# Define path relative to this script
# Script is in c:\garam\garam\scripts
# We want c:\garam\GARAM_Data\plans
BASE_DIR = Path(__file__).resolve().parent.parent # c:\garam\garam
DATA_DIR = BASE_DIR.parent / "GARAM_Data" # c:\garam\GARAM_Data
PLANS_DIR = DATA_DIR / "plans"

os.makedirs(PLANS_DIR, exist_ok=True)

today_str = datetime.now().strftime("%Y%m%d")
file_path = PLANS_DIR / f"daily_plan_{today_str}.json"

data = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "regime": "BULL_TREND (Simulated)",
    "targets": [
        {
            "symbol": "005930",
            "name": "Samsung Elec",
            "action": "BUY",
            "size_pct": 0.1,
            "entry_range": [75000, 75500],
            "stop_loss": 74000,
            "target_price": 78000,
            "reason": "Strong foreign buying (Simulated)"
        },
        {
            "symbol": "000660",
            "name": "SK Hynix",
            "action": "HOLD",
            "size_pct": 0.15,
            "entry_range": [0, 0],
            "stop_loss": 180000,
            "target_price": 200000,
            "reason": "Trend continuation (Simulated)"
        }
    ]
}

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Created dummy plan at {file_path}")
