import json
from pathlib import Path
from datetime import datetime

def check_json(path_str):
    p = Path(path_str)
    print(f"Checking {p}...")
    if not p.exists():
        print(" [FAIL] Not found")
        return
    try:
        txt = p.read_text(encoding="utf-8-sig")
        data = json.loads(txt)
        print(" [OK] JSON Parsed")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f" [FAIL] Error: {e}")

check_json("results/ops/status/switching_ts_job.json")
check_json("results/ops/status/kiwoom_flow_job.json")
