# scripts/kiwoom/collect_tr_daily_range.py
# -*- coding: utf-8 -*-
import sys
import time
import json
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

# Robust Path Setup & 32-bit Enforcement
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.runtime32 import ensure_32bit_or_reexec
ensure_32bit_or_reexec()

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QEventLoop, QTimer
from PyQt5.QAxContainer import QAxWidget

def _now_kst_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")

def write_status(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    # PowerShell(5.1) 표시 안정성 위해 utf-8-sig 권장
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8-sig")
    tmp.replace(path)

def append_save(df_new: pd.DataFrame, out_path: Path, key_cols):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        df_old = pd.read_csv(out_path, dtype=str, encoding="utf-8-sig")
        df = pd.concat([df_old, df_new.astype(str)], ignore_index=True)
        if key_cols:
            df = df.drop_duplicates(subset=key_cols, keep="last")
    else:
        df = df_new.astype(str)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

class KiwoomTR:
    def __init__(self):
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.login_loop = QEventLoop()
        self.tr_loop = QEventLoop()
        self.connected = False
        self._fields = []
        self._rows = []
        self._timed_out = False

    def comm_connect(self):
        self.ocx.dynamicCall("CommConnect()")
        self.login_loop.exec_()
        return self.connected

    def _on_event_connect(self, err_code):
        self.connected = (err_code == 0)
        self.login_loop.exit()

    def set_input(self, k, v):
        self.ocx.dynamicCall("SetInputValue(QString, QString)", k, v)

    def request(self, rqname, trcode, fields, screen="0101", timeout_ms=60000):
        self._fields = fields
        self._rows = []
        self._timed_out = False

        ret = self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, 0, screen)
        if int(ret) != 0:
            raise RuntimeError(f"CommRqData failed ret={ret}")

        def _timeout():
            self._timed_out = True
            if self.tr_loop.isRunning():
                self.tr_loop.exit()

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(_timeout)
        timer.start(int(timeout_ms))

        self.tr_loop.exec_()
        timer.stop()

        if self._timed_out:
            raise TimeoutError(f"TR timeout: rqname={rqname} trcode={trcode}")

        return pd.DataFrame(self._rows)

    def _on_receive_tr_data(self, scrno, rqname, trcode, recordname, prev_next, data_len, err_code, msg1, msg2):
        # recordname 기반이 더 안전한 케이스가 존재하므로, 둘 다 시도
        try:
            cnt = int(self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, recordname))
        except Exception:
            cnt = int(self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname))

        rows = []
        for i in range(cnt):
            row = {}
            for f in self._fields:
                # recordname 우선
                val = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, recordname, i, f)
                s = str(val).strip()
                if s == "":
                    # rqname fallback
                    val2 = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, f)
                    s = str(val2).strip()
                row[f] = s
            rows.append(row)

        self._rows = rows
        self.tr_loop.exit()

def load_spec(spec_json: Path) -> dict:
    # spec 파일은 utf-8-sig로 저장 권장(윈도우 편의)
    txt = spec_json.read_text(encoding="utf-8-sig")
    return json.loads(txt)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trcode", required=False)
    ap.add_argument("--rqname", required=False)
    ap.add_argument("--start_yyyymmdd", required=False)
    ap.add_argument("--end_yyyymmdd", required=False)
    ap.add_argument("--out_csv", required=False)

    ap.add_argument("--spec_json", required=False, help="TR spec (inputs/output_fields/key_cols) JSON")
    ap.add_argument("--status_json", default="results/ops/status/kiwoom_flow_job.json")
    ap.add_argument("--timeout_ms", type=int, default=60000)
    ap.add_argument("--sleep_sec", type=float, default=0.4)
    args = ap.parse_args()

    spec = {}
    if args.spec_json:
        spec = load_spec(Path(args.spec_json))
    
    # Merge args with spec (CLI takes precedence, but if None, use Spec)
    args.trcode = args.trcode or spec.get("trcode")
    args.rqname = args.rqname or spec.get("rqname")
    args.start_yyyymmdd = args.start_yyyymmdd or spec.get("start_yyyymmdd")
    args.end_yyyymmdd = args.end_yyyymmdd or spec.get("end_yyyymmdd")
    args.out_csv = args.out_csv or spec.get("out_csv")

    if not (args.trcode and args.rqname and args.start_yyyymmdd and args.end_yyyymmdd and args.out_csv):
         raise ValueError("Missing required params (trcode/rqname/start/end/out_csv). Provide via CLI or --spec_json")

    inputs = spec.get("static_inputs", spec.get("inputs", {}))
    output_fields = spec.get("output_fields", [])
    key_cols = spec.get("key_cols", ["일자"])

    if not output_fields:
        raise ValueError("spec_json.output_fields is empty")

    status_path = Path(args.status_json)
    out_path = Path(args.out_csv)

    app = QApplication(sys.argv)
    kw = KiwoomTR()

    # INIT status
    write_status(status_path, {
        "step": "INIT",
        "heartbeat_at": _now_kst_iso(),
        "job": {
            "trcode": args.trcode,
            "rqname": args.rqname,
            "range": [args.start_yyyymmdd, args.end_yyyymmdd],
            "out_csv": str(out_path).replace("\\", "/"),
            "spec_json": str(Path(args.spec_json)).replace("\\", "/"),
            "output_fields": output_fields,
            "inputs_template": inputs,
        },
        "progress": {"total_days": 0, "done_days": 0, "current_day": None, "last_result": None},
        "last_error": None
    })

    if not kw.comm_connect():
        write_status(status_path, {
            "step": "FAILED",
            "heartbeat_at": _now_kst_iso(),
            "last_error": {"type": "LOGIN_FAILED", "msg": "Kiwoom login failed"}
        })
        sys.exit(1)

    # date loop (B-day)
    dates = pd.date_range(pd.to_datetime(args.start_yyyymmdd), pd.to_datetime(args.end_yyyymmdd), freq="B")
    total = len(dates)
    done = 0

    write_status(status_path, {
        "step": "LOGIN_OK",
        "heartbeat_at": _now_kst_iso(),
        "progress": {"total_days": total, "done_days": 0, "current_day": None, "last_result": None},
        "last_error": None
    })

    for d in dates:
        ymd = d.strftime("%Y%m%d")
        # DAY_START
        write_status(status_path, {
            "step": "DAY_START",
            "heartbeat_at": _now_kst_iso(),
            "progress": {"total_days": total, "done_days": done, "current_day": ymd, "last_result": None},
            "last_error": None
        })

        try:
            # inputs 적용 (date placeholder 치환)
            for k, v in inputs.items():
                vv = str(v).replace("{date}", ymd)
                kw.set_input(k, vv)

            # request 직전/직후 heartbeat 갱신 (멈춤 감지용)
            write_status(status_path, {
                "step": "DAY_REQ",
                "heartbeat_at": _now_kst_iso(),
                "progress": {"total_days": total, "done_days": done, "current_day": ymd, "last_result": None},
                "last_error": None
            })

            df = kw.request(args.rqname, args.trcode, output_fields, timeout_ms=args.timeout_ms)

            write_status(status_path, {
                "step": "DAY_RSP",
                "heartbeat_at": _now_kst_iso(),
                "progress": {"total_days": total, "done_days": done, "current_day": ymd, "last_result": {"ymd": ymd, "rows": int(len(df))}},
                "last_error": None
            })

            if df is None or df.empty:
                # 빈 응답: 정상일 수도 있으나 기록은 남김
                write_status(status_path, {
                    "step": "DAY_EMPTY",
                    "heartbeat_at": _now_kst_iso(),
                    "progress": {"total_days": total, "done_days": done, "current_day": ymd, "last_result": {"ymd": ymd, "rows": 0}},
                    "last_error": None
                })
            else:
                # Gate C: 값 무결성 체크 (전부 공백이면 실패)
                all_blank = True
                for c in output_fields:
                    if c in df.columns and df[c].astype(str).str.strip().ne("").any():
                        all_blank = False
                        break
                if all_blank:
                    raise ValueError("INTEGRITY_FAIL: all fields blank. Check output_fields/recordname/encoding.")

                append_save(df, out_path, key_cols=key_cols)
                done += 1
                write_status(status_path, {
                    "step": "DAY_OK",
                    "heartbeat_at": _now_kst_iso(),
                    "progress": {"total_days": total, "done_days": done, "current_day": ymd, "last_result": {"ymd": ymd, "rows": int(len(df))}},
                    "last_error": None
                })

        except Exception as e:
            write_status(status_path, {
                "step": "DAY_ERR",
                "heartbeat_at": _now_kst_iso(),
                "progress": {"total_days": total, "done_days": done, "current_day": ymd, "last_result": None},
                "last_error": {"type": type(e).__name__, "msg": str(e)}
            })
            # 운영 규율: 실패면 즉시 종료 (watchdog가 재시도/중단)
            sys.exit(2)

        time.sleep(args.sleep_sec)

    write_status(status_path, {
        "step": "DONE",
        "heartbeat_at": _now_kst_iso(),
        "progress": {"total_days": total, "done_days": done, "current_day": dates[-1].strftime("%Y%m%d") if total else None, "last_result": None},
        "last_error": None
    })

    QTimer.singleShot(200, app.quit)
    app.exec_()

if __name__ == "__main__":
    main()
