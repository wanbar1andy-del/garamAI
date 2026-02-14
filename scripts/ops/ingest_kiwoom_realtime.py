# scripts/ops/ingest_kiwoom_realtime.py
# Phase 30-3: Kiwoom Realtime Ingester (Stocks Only / TICK Only)
# Output: feed_live.jsonl (RealtimeEvent-like JSON, Engine-agnostic)

import os
import sys
import json
import time
import uuid
import queue
import signal
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from PyQt5.QtCore import QEventLoop, QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget


# -------------------------
# Utilities
# -------------------------
def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def safe_mkdir(p: str) -> None:
    Path(p).parent.mkdir(parents=True, exist_ok=True)

def load_universe_csv(path: str, limit: Optional[int] = None) -> List[str]:
    """
    Universe file expected: first column contains stock code (e.g., 005930).
    You can adapt parsing to your existing UniverseLoader if you want,
    but keep this file decoupled from engine modules by design.
    """
    codes: List[str] = []
    if not os.path.exists(path):
         print(f"WARN: Universe file not found at {path}")
         return []
         
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            # naive: split by comma and take first token
            code = s.split(",")[0].strip().strip('"')
            if code and code.isdigit():
                codes.append(code)
            if limit and len(codes) >= limit:
                break
    return codes


# -------------------------
# Writer Thread (deque -> batch -> flush+fsync)
# -------------------------
class JsonlDurableWriter(threading.Thread):
    def __init__(
        self,
        feed_path: str,
        dq: deque,
        stop_event: threading.Event,
        batch_size: int = 200,
        flush_interval_sec: float = 0.25,
        max_bytes: int = 0,  # 0 to disable rotation by default (simpler ops)
        heartbeat_interval_sec: float = 5.0,
    ):
        super().__init__(daemon=True)
        self.feed_path = feed_path
        self.dq = dq
        self.stop_event = stop_event
        self.batch_size = batch_size
        self.flush_interval_sec = flush_interval_sec
        self.max_bytes = max_bytes
        self.heartbeat_interval_sec = heartbeat_interval_sec

        self._last_flush = time.time()
        self._last_hb = time.time()

        safe_mkdir(self.feed_path)

    def _rotate_if_needed(self, fp):
        try:
            if self.max_bytes <= 0:
                return fp
            fp.flush()
            os.fsync(fp.fileno())
            size = os.path.getsize(self.feed_path)
            if size < self.max_bytes:
                return fp

            # Rotate: feed_live.jsonl -> feed_live.jsonl.YYYYmmdd_HHMMSS
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated = f"{self.feed_path}.{ts}"
            fp.close()
            os.replace(self.feed_path, rotated)
            # reopen
            return open(self.feed_path, "a", encoding="utf-8", buffering=1)
        except Exception:
            # Fail-open: rotation failure should not kill ingester
            return fp

    def run(self):
        # Open in append mode
        fp = open(self.feed_path, "a", encoding="utf-8", buffering=1)  # line-buffer
        try:
            while not self.stop_event.is_set():
                wrote_any = False
                n = 0

                # Batch drain
                while n < self.batch_size:
                    try:
                        evt = self.dq.popleft()
                    except IndexError:
                        break

                    fp.write(json.dumps(evt, ensure_ascii=False) + "\n")
                    wrote_any = True
                    n += 1

                now = time.time()

                # Periodic heartbeat event for observability (Engine can ignore CONTROL/HEARTBEAT)
                if (now - self._last_hb) >= self.heartbeat_interval_sec:
                    hb = {
                        "event_id": f"hb_{uuid.uuid4().hex}",
                        "event_type": "HEARTBEAT",
                        "event_time": utcnow_iso(),
                        "ingest_time": utcnow_iso(),
                        "symbol": None,
                        "payload": {
                            "writer_queue_depth": len(self.dq),
                        },
                    }
                    fp.write(json.dumps(hb, ensure_ascii=False) + "\n")
                    wrote_any = True
                    self._last_hb = now

                # Flush policy: flush+fsync on interval OR if wrote batch
                if wrote_any and ((now - self._last_flush) >= self.flush_interval_sec):
                    fp.flush()
                    os.fsync(fp.fileno())
                    self._last_flush = now
                    fp = self._rotate_if_needed(fp)

                if not wrote_any:
                    time.sleep(0.01)

            # Final flush
            fp.flush()
            os.fsync(fp.fileno())
        finally:
            try:
                fp.close()
            except Exception:
                pass


# -------------------------
# Kiwoom OCX Wrapper
# -------------------------
class KiwoomIngester:
    """
    Kiwoom OCX -> TICK events -> deque -> Jsonl writer
    Engine-agnostic by design.
    """
    def __init__(
        self,
        feed_path: str,
        universe_csv: str,
        stop_event: threading.Event,
        universe_limit: Optional[int] = None,
        screen_no: str = "1000",
        batch_register_size: int = 80,
    ):
        self.feed_path = feed_path
        self.universe_csv = universe_csv
        self.universe_limit = universe_limit
        self.screen_no = screen_no
        self.batch_register_size = batch_register_size

        self.stop_event = stop_event
        self.dq: deque = deque(maxlen=200_000)  # backpressure buffer (ingester-side)
        self.writer = JsonlDurableWriter(feed_path, self.dq, stop_event)

        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        # Event loops
        self._login_loop: Optional[QEventLoop] = None

        # Runtime state
        self.codes: List[str] = []
        self._last_tick_wall = time.time()
        self._subscribed = False

        # Connect signals
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveRealData.connect(self._on_receive_realdata)

        # Safety timers (watchdog-like)
        self._health_timer = QTimer()
        self._health_timer.timeout.connect(self._health_check)

        # Minimal FID set for TICK (주식체결)
        # FID refs: https://wikidocs.net/4243
        self.tick_fids = {
            "trade_time": "20",    # 체결시간 (HHMMSS)
            "price": "10",         # 현재가
            "volume": "15",        # 거래량(체결량)
            "cum_volume": "13",    # 누적거래량
            # "side": ???           # 매수/매도 구분은 리얼 데이터에 없을 수 있음(호가/체결구분 별도)
        }

    # ---- Kiwoom API calls helpers ----
    def _call(self, name: str, *args):
        return self.ocx.dynamicCall(name, *args)

    def start(self):
        # Start writer first (so login/subscription issues are still logged)
        self.writer.start()

        # Load universe
        self.codes = load_universe_csv(self.universe_csv, self.universe_limit)
        if not self.codes:
            print(f"WARN: Universe is empty or file missing: {self.universe_csv}")
            # Still proceed to allow testing control events

        self._emit_control("INGESTER_START", {
            "feed_path": self.feed_path,
            "universe_size": len(self.codes),
            "screen_no": self.screen_no,
        })

        # Login
        self._login()

        # Subscribe realtime
        self._subscribe_realtime()

        # Start health check timer
        self._health_timer.start(1000)  # 1s tick

    def stop(self):
        self._emit_control("INGESTER_STOP", {})
        try:
            self._unsubscribe_realtime()
        except Exception:
            pass

    def _login(self):
        ret = self._call("CommConnect()")
        self._login_loop = QEventLoop()
        self._login_loop.exec_()

    def _on_event_connect(self, err_code: int):
        if err_code != 0:
            self._emit_control("LOGIN_FAIL", {"err_code": int(err_code)})
        else:
            self._emit_control("LOGIN_OK", {})
        if self._login_loop is not None:
            self._login_loop.exit()

    def _subscribe_realtime(self):
        """
        RegisterRealtime: SetRealReg(screen_no, codes, fids, optType)
        - optType: "0" 기존등록삭제 후 신규, "1" 기존 유지 + 추가
        Kiwoom은 한번에 등록 가능한 코드 수 제한이 있으므로 batch 등록 권장.
        """
        if not self.codes:
            return

        fids = ";".join(self.tick_fids.values())
        codes = self.codes

        # Clear screen first (opt)
        try:
            self._call("SetRealRemove(QString, QString)", self.screen_no, "ALL")
        except Exception:
            pass

        for i in range(0, len(codes), self.batch_register_size):
            chunk = codes[i:i + self.batch_register_size]
            code_str = ";".join(chunk)
            # "0": overwrite per screen, "1": append - 여기서는 첫 chunk는 0, 이후 1
            opt = "0" if i == 0 else "1"
            self._call("SetRealReg(QString, QString, QString, QString)", self.screen_no, code_str, fids, opt)

        self._subscribed = True
        self._emit_control("REALREG_OK", {"codes": len(codes), "fids": fids})

    def _unsubscribe_realtime(self):
        if not self._subscribed:
            return
        self._call("SetRealRemove(QString, QString)", self.screen_no, "ALL")
        self._subscribed = False
        self._emit_control("REALREG_REMOVE", {"screen_no": self.screen_no})

    def _get_real(self, code: str, fid: str) -> str:
        # GetCommRealData(code, fid)
        return str(self._call("GetCommRealData(QString, int)", code, int(fid))).strip()

    def _on_receive_realdata(self, code: str, real_type: str, real_data: str):
        """
        핵심: TICK Only. BAR 생성하지 않음.
        Fail-safe: 이 콜백에서 절대 블로킹 I/O 하지 않음 (deque push만).
        """
        try:
            # 관심 real_type은 보통 "주식체결" 등 (문서에 따름)
            # 필터링이 필요하면 여기에 real_type 체크를 넣어도 됨.
            price_raw = self._get_real(code, self.tick_fids["price"])
            vol_raw = self._get_real(code, self.tick_fids["volume"])
            tt_raw = self._get_real(code, self.tick_fids["trade_time"])
            cumv_raw = self._get_real(code, self.tick_fids["cum_volume"])

            # Normalize
            def to_int(x: str) -> int:
                try:
                    # 키움 현재가는 부호/콤마 포함 가능
                    return int(str(x).replace(",", "").strip().lstrip("+"))
                except Exception:
                    return 0

            price = abs(to_int(price_raw))
            volume = abs(to_int(vol_raw))
            cum_volume = abs(to_int(cumv_raw))

            evt = {
                "event_id": uuid.uuid4().hex,
                "event_type": "TICK",
                "event_time": utcnow_iso(),   # source time이 있으면 여기로 매핑 권장(아래 보완 참고)
                "ingest_time": utcnow_iso(),
                "symbol": str(code),
                "payload": {
                    "price": price,
                    "volume": volume,
                    "cum_volume": cum_volume,
                    "trade_time": tt_raw,   # HHMMSS (source hint)
                    "real_type": str(real_type),
                }
            }

            self.dq.append(evt)
            self._last_tick_wall = time.time()

            # Ingester-side backpressure safety (최악 시 drop policy)
            # Engine은 loss 0이 목표이므로, drop 대신 dq maxlen을 충분히 크게 잡고
            # 운영 시 lag 경보를 올리는 방향이 정석.
            if len(self.dq) >= self.dq.maxlen - 1000:
                self._emit_control("INGESTER_BACKPRESSURE", {
                    "queue_depth": len(self.dq),
                    "maxlen": self.dq.maxlen,
                })

        except Exception as e:
            # Fail-open: callback error should not crash process
            self._emit_control("INGESTER_TICK_ERR", {"err": repr(e), "code": str(code), "real_type": str(real_type)})

    def _health_check(self):
        """
        SLA 관찰: Tick silence / queue depth
        실제 “end-to-end latency”는 Engine events.jsonl와 교차 분석이 필요하지만,
        Ingester만으로도 1차 경보는 가능.
        """
        if self.stop_event.is_set():
            return

        now = time.time()
        silent_sec = now - self._last_tick_wall

        # If no ticks for too long during market hours, raise warning (여기선 단순)
        if silent_sec > 10:
            self._emit_control("INGESTER_TICK_SILENCE", {"silent_sec": round(silent_sec, 3)})

        # Queue depth monitoring
        qd = len(self.dq)
        if qd > 50_000:
            self._emit_control("INGESTER_QUEUE_HIGH", {"queue_depth": qd})

    def _emit_control(self, name: str, payload: Dict[str, Any]):
        evt = {
            "event_id": f"ctl_{uuid.uuid4().hex}",
            "event_type": "CONTROL",
            "event_time": utcnow_iso(),
            "ingest_time": utcnow_iso(),
            "symbol": None,
            "payload": {"name": name, **payload}
        }
        # Do not block; just queue
        self.dq.append(evt)


def main():
    # Hard-coded defaults to keep decoupled & simple (can be CLI-argged later)
    ROOT = os.getcwd()
    feed_path = os.path.join(ROOT, "feed_live.jsonl")
    universe_csv = os.path.join(ROOT, "GARAM_Data", "real_universe_400.csv") # Aligned with Engine

    # Optional: limit for early smoke test
    universe_limit = None  # e.g., 50

    stop_event = threading.Event()

    def _sig_handler(signum, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    app = QApplication(sys.argv)
    ing = KiwoomIngester(
        feed_path=feed_path,
        universe_csv=universe_csv,
        stop_event=stop_event,
        universe_limit=universe_limit,
        screen_no="1000",
    )

    try:
        ing.start()
        # Qt main loop
        while not stop_event.is_set():
            app.processEvents()
            time.sleep(0.01)
    finally:
        try:
            ing.stop()
        except Exception:
            pass
        stop_event.set()
        # Writer thread will exit on stop_event; give it a moment
        time.sleep(0.5)

if __name__ == "__main__":
    main()
