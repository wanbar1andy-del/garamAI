# -*- coding: utf-8 -*-
"""
키움 데이터 수집 및 관리 시스템 (통합 버전)
- 기존 CLI 스크립트들의 파편화 문제를 해결하기 위해 GUI 기반으로 통합.
- 윈도우 이벤트 루프(QAxWidget)를 사용하여 안정적인 로그인 및 TR 송수신 보장.
- 400개 종목에 대한 증분 수집 및 자동 업데이트 기능 포함.
"""

import sys
import os
import struct
import logging
import time
import ctypes
import json
from pathlib import Path
from datetime import datetime, timezone
import uuid
import queue
import threading
from collections import deque

# [CRITICAL] Data libraries
import pandas as pd
import numpy as np

# Define Project Root (SSOT)
project_root = Path(__file__).resolve().parent.parent.parent

# --- SSOT Logging Configuration ---
log_dir = project_root / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
LOG_FILE = log_dir / "kiwoom_ingest.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
    ],
    force=True
)

# Force flush on existing handlers (Best Effort)
for h in logging.getLogger().handlers:
    try:
        h.flush()
    except Exception:
        pass

# --- [CRITICAL] 32-bit hard guard (MUST be before PyQt5 / QAxWidget imports) ---
def _ensure_32bit_or_reexec():
    bits = struct.calcsize("P") * 8
    if bits == 32:
        return

    # Check common 32-bit python paths or use env var
    py32 = os.environ.get("GARAM_PY32", r"C:\Python39-32\python.exe")
    if not Path(py32).exists():
        logging.critical(f"[FATAL] Kiwoom must run on 32-bit Python. Current={sys.executable} ({bits}-bit)")
        logging.critical(f"[FATAL] Set env var GARAM_PY32 to your 32-bit python.exe. Tried: {py32}")
        sys.exit(1)

    logging.info(f"[REEXEC] 64-bit detected ({sys.executable}). Re-exec with 32-bit: {py32}")
    try:
        # Flush before exec
        for h in logging.getLogger().handlers:
            h.flush()
            
        # Quote explicit path to handle spaces if needed, but execv args list is safer
        os.execv(py32, [py32] + sys.argv)
    except OSError as e:
        logging.critical(f"[FATAL] Re-exec failed: {e}")
        sys.exit(1)

_ensure_32bit_or_reexec()
# --- end guard ---

# PyQt5 임포트 (32-bit verified)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                             QVBoxLayout, QWidget, QMessageBox, QTextEdit, 
                             QProgressBar, QHBoxLayout, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, QTime, QEventLoop, QThread
from PyQt5.QAxContainer import QAxWidget

# --- [NEW] Auto Login Watcher ---
class LoginWatchdog(QThread):
    def run(self):
        user32 = ctypes.windll.user32
        
        # Define callback type for EnumWindows
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        
        def enum_window_callback(hwnd, lParam):
            if not user32.IsWindowVisible(hwnd):
                return True
                
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
                
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
            
            # Fuzzy Matching Logic
            if "Garam" in title or "가람" in title:
                return True
                
            confirm_keywords = ["Open API Login", "Open API 로그인", "Open API Password", "업그레이드 확인"]
            
            is_target = False
            for k in confirm_keywords:
                if k in title: 
                    is_target = True
                    break
            
            if is_target:
                print(f"[AutoLogin] Detected Popup '{title}' (HWND: {hwnd}). Focus & Enter...")
                sys.stdout.flush()
                
                # 1. Restore if minimized
                user32.ShowWindow(hwnd, 9) # SW_RESTORE = 9
                
                # 2. Force Foreground (Focus)
                # AttachThreadInput might be needed if foreground lock is active, but try direct first.
                user32.SetForegroundWindow(hwnd)
                time.sleep(0.2)
                
                # 3. Send Physical Key Event (More robust than PostMessage)
                # VK_RETURN = 0x0D
                # keybd_event(bVk, bScan, dwFlags, dwExtraInfo)
                # 0 = Down, 2 = Up
                user32.keybd_event(0x0D, 0, 0, 0) # Enter Down
                time.sleep(0.1)
                user32.keybd_event(0x0D, 0, 2, 0) # Enter Up
                
                time.sleep(1) 
                
            return True

        cb_proto = WNDENUMPROC(enum_window_callback)
        
        while True:
            try:
                user32.EnumWindows(cb_proto, 0)
            except Exception as e:
                print(f"[AutoLogin] Scan Error: {e}")
            
            time.sleep(2) # Check every 2s

# 프로젝트 루트 경로 설정 (c:\garam\garam)
# 프로젝트 루트 경로 설정 (c:\garam\garam) - pipeline/01_ingest/ 에서 3단계 위
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# --- [SSOT V2] Ingest Wrapper Imports ---
from pipeline._01_ingest.paths import get_ingest_paths
from pipeline._01_ingest.write_csv import write_minute_csv

# --- [SSOT V2] Ingest Wrapper Imports ---
from pipeline._01_ingest.paths import get_ingest_paths
from pipeline._01_ingest.write_csv import write_minute_csv

# 로깅 설정 (한글 로그 파일) - Removed Duplicate BasicConfig (SSOT)
logger = logging.getLogger(__name__)

# --- [NEW] JsonlDurableWriter for Realtime Feed ---
class JsonlDurableWriter(threading.Thread):
    def __init__(
        self,
        feed_path: str,
        dq: deque,
        stop_event: threading.Event,
        batch_size: int = 200,
        flush_interval_sec: float = 0.25,
        max_bytes: int = 0, # 0 to disable rotation by default
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
        
        # Ensure dir exists
        Path(self.feed_path).parent.mkdir(parents=True, exist_ok=True)

    def _rotate_if_needed(self, fp):
        try:
            if self.max_bytes <= 0:
                return fp
            fp.flush()
            os.fsync(fp.fileno())
            size = os.path.getsize(self.feed_path)
            if size < self.max_bytes:
                return fp

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated = f"{self.feed_path}.{ts}"
            fp.close()
            os.replace(self.feed_path, rotated)
            return open(self.feed_path, "a", encoding="utf-8", buffering=1)
        except Exception:
            return fp

    def run(self):
        fp = open(self.feed_path, "a", encoding="utf-8", buffering=1)
        try:
            while not self.stop_event.is_set():
                wrote_any = False
                n = 0
                while n < self.batch_size:
                    try:
                        evt = self.dq.popleft()
                    except IndexError:
                        break
                    
                    fp.write(json.dumps(evt, ensure_ascii=False) + "\n")
                    wrote_any = True
                    n += 1

                now = time.time()
                if (now - self._last_hb) >= self.heartbeat_interval_sec:
                    hb = {
                        "event_id": f"hb_{uuid.uuid4().hex}",
                        "event_type": "HEARTBEAT",
                        "event_time": datetime.now(timezone.utc).isoformat(),
                        "ingest_time": datetime.now(timezone.utc).isoformat(),
                        "symbol": None,
                        "payload": {"writer_queue_depth": len(self.dq)},
                    }
                    fp.write(json.dumps(hb, ensure_ascii=False) + "\n")
                    wrote_any = True
                    self._last_hb = now

                if wrote_any and ((now - self._last_flush) >= self.flush_interval_sec):
                    fp.flush()
                    os.fsync(fp.fileno())
                    self._last_flush = now
                    fp = self._rotate_if_needed(fp)

                if not wrote_any:
                    time.sleep(0.01)
            
            fp.flush()
            os.fsync(fp.fileno())
        finally:
            try: fp.close()
            except: pass

class KiwoomSystemWindow(QMainWindow):
    # Absolute Path based on project_root (SSOT)
    STATUS_JSON_PATH = project_root / "results/ops/status/kiwoom_ingest.json"

    def _update_status(self, step="RUNNING", status_msg=""):
        try:
            self.STATUS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            payload = {
                "step": step,
                "heartbeat_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "progress": {
                     "processed": self.processed_count,
                     "total": self.total_targets,
                     "current": self.current_symbol,
                     "fail_count": self.fail_count
                },
                "last_message": status_msg,
                "server_type": getattr(self, "server_type", "UNKNOWN")
            }
            
            # Atomic Write
            tmp = self.STATUS_JSON_PATH.with_suffix(".json.tmp")
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            
            if tmp.exists():
                tmp.replace(self.STATUS_JSON_PATH)
                
        except Exception as e:
            # Don't let status write fail the whole app, just log to stderr
            print(f"[Warn] Status write failed: {e}", file=sys.stderr)

    def log_msg(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {msg}"
        self.log_view.append(formatted)
        
        # Safe logging for Windows cp949
        safe_msg = formatted
        try:
            safe_msg.encode('cp949')
        except UnicodeEncodeError:
            # Replace common emojis with text
            replacements = {
                "🎯": "[TARGET]", "🚀": "[GO]", "❌": "[FAIL]", 
                "⚡": "[FILL]", "⚠️": "[WARN]", "🟢": "[ON]", "🔴": "[OFF]"
            }
            for k, v in replacements.items():
                safe_msg = safe_msg.replace(k, v)
            
            # If still failing, drop characters that cannot be encoded in cp949
            safe_msg = safe_msg.encode('cp949', 'ignore').decode('cp949')
            
        logging.info(safe_msg)
        
        # Auto-scroll
        cursor = self.log_view.textCursor()
        cursor.movePosition(cursor.End)
        self.log_view.setTextCursor(cursor)
        
        # Trigger Heartbeat on Log (Optional but good)
        self._update_status(step="RUNNING", status_msg=msg)

    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("GARAM Kiwoom Ingest System (Integrated)")
        self.setGeometry(100, 100, 700, 600)
        
        # Init Watchdog for Login Windows
        self.login_watcher = LoginWatchdog()
        self.login_watcher.start()
        
        # --- 상태 변수 ---
        self.is_collecting = False          # 수집 진행 중 여부
        self.collection_queue = []          # 수집 대기열 [(우선순위, 코드, 사유), ...]
        self.current_symbol = ""            # 현재 수집 중인 종목
        self.current_page = 0               # 현재 페이지 (TR 페이징)
        self.current_data_buffer = []       # 수집 데이터 임시 저장소
        self.total_targets = 0              # 전체 대상 수
        self.processed_count = 0            # 처리된 수
        self.success_count = 0              # 성공 수
        self.fail_count = 0                 # 실패 수
        
        # 데이터 저장 경로 확인 (FIXED: Use correct GARAM_Data location)
        # 데이터 저장 경로 확인 (Standard Path)
        self.output_dir = project_root / "GARAM_Data/history/minute"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # --- 설정 상수 (Health Care: 유지보수 용이성 확보) ---
        self.PAGE_DELAY_MS = 800        # 페이지 넘김 간격 (0.8초 - 안정성 강화)
        self.SYMBOL_DELAY_MS = 2000     # 종목 변경 간격 (2.0초 - 안정성 강화)
        self.MAX_RETRY_COUNT = 3        # 최대 재시도 횟수
        
        # Telegram Config (Load from Env or Config)
        # Security Fix: Removed hardcoded tokens.
        import os
        self.BOT_TOKEN = os.environ.get('GARAM_BOT_TOKEN', '')
        self.CHAT_ID = os.environ.get('GARAM_CHAT_ID', '')

        # --- [NEW] Realtime Feed State ---
        self.feed_path = str(project_root / "GARAM_Data/feed/feed_live.jsonl")
        self.tick_fids = {
            "trade_time": "20", "price": "10", "volume": "15", "cum_volume": "13"
        }
        # [SHORT_DATA] Output Dir
        self.short_dir = project_root / "GARAM_Data/history/short_daily"
        self.short_dir.mkdir(parents=True, exist_ok=True)

        self.real_dq = deque(maxlen=200000)
        self.feed_stop_event = threading.Event()
        self.feed_writer = JsonlDurableWriter(self.feed_path, self.real_dq, self.feed_stop_event)
        self.feed_writer.start() # Start Writer Thread immediately

        
        # --- UI 초기화 ---
        self.init_ui()
        # Removed redundant check_system_architecture()
        
        # --- 키움 OCX 컨트롤 생성 ---
        try:
            self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
            self.ocx.OnEventConnect.connect(self._on_event_connect)        # 로그인 이벤트
            self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)     # TR 데이터 수신
            self.ocx.OnReceiveMsg.connect(self._on_receive_msg)            # 메시지 수신
            self.ocx.OnReceiveChejanData.connect(self._on_receive_chejan_data) # [NEW] 체결/잔고 수신
            self.ocx.OnReceiveRealData.connect(self._on_receive_realdata)     # [NEW] Realtime Feed
        except Exception as e:
            self.log_msg(f"[치명적 오류] 키움 OpenAPI 컨트롤 생성 실패: {e}")
            self.log_msg("OpenAPI가 올바르게 설치되지 않았거나 레지스트리 문제가 있을 수 있습니다.")
            QMessageBox.critical(self, "오류", "키움 OpenAPI 컨트롤 생성 실패.\n설치 상태를 확인하세요.")

        # 타이머 설정 (타임아웃 감지용)
        self.tr_timer = QTimer(self)
        self.tr_timer.setSingleShot(True)
        self.tr_timer.timeout.connect(self._on_tr_timeout)

        # [CRITICAL] Dedicated Heartbeat Timer (Every 10s intervals)
        self.heartbeat_timer = QTimer(self)
        # Assuming lambda usage or define a slot. Using direct lambda here if imported, 
        # but to be safe and consistent with previous edit instructions which use lambda:
        self.heartbeat_timer.timeout.connect(lambda: self._update_status(step="RUNNING", status_msg="heartbeat"))
        self.heartbeat_timer.start(10000)

        # [NEW] Schedule Timer (08:30 Restart, 16:00 Shutdown)
        self.start_time = datetime.now()
        self.schedule_timer = QTimer(self)
        self.schedule_timer.timeout.connect(self._check_schedule)
        self.schedule_timer.start(60000) # Check every 1 minute
        
        # 자동 로그인 트리거 (1초 후)
        QTimer.singleShot(1000, self.try_login)
        
        # 주문 감시 타이머 (0.5초 간격)
        self.order_timer = QTimer(self)
        self.order_timer.timeout.connect(self._check_order_files)
        self.order_timer.start(500)
        
        self.order_dir = project_root / "GARAM_Data/orders"
        self.order_dir.mkdir(parents=True, exist_ok=True)
        # Ensure subdirs
        (self.order_dir / "inbox").mkdir(exist_ok=True)
        (self.order_dir / "archive").mkdir(exist_ok=True)
        (self.order_dir / "ack").mkdir(exist_ok=True)
        (self.order_dir / "rej").mkdir(exist_ok=True)
        (self.order_dir / "processing").mkdir(exist_ok=True) # Lock folder

        # Initial status
        self._update_status(step="INIT", status_msg="Starting up...")

    def init_ui(self):
        """UI 구성 (한글화 적용)"""
        self.setWindowTitle('가람(Garam) - 키움 데이터 통합 시스템')
        self.setGeometry(100, 100, 650, 750)
        
        # 스타일시트 적용
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; color: #ffffff; }
            QLabel { color: #dddddd; font-size: 13px; }
            QGroupBox { border: 1px solid #555; margin-top: 10px; font-weight: bold; color: #aaa; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 10px; }
            QTextEdit { background-color: #1e1e1e; color: #00ff00; border: 1px solid #444; font-family: 'Consolas', '맑은 고딕'; }
            QPushButton { background-color: #3d3d3d; border: 1px solid #555; color: #fff; padding: 5px; min-height: 25px; }
            QPushButton:hover { background-color: #4d4d4d; }
            QPushButton:pressed { background-color: #2d2d2d; }
            QPushButton:disabled { background-color: #252525; color: #555; }
            QProgressBar { border: 1px solid #444; text-align: center; color: white; }
            QProgressBar::chunk { background-color: #2196F3; }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        
        # 1. 헤더 및 상태 표시
        header_layout = QHBoxLayout()
        title = QLabel('Garam Trading System')
        title.setStyleSheet('font-size: 20px; font-weight: bold; color: #4CAF50;')
        
        status_box = QHBoxLayout()
        self.status_led = QLabel('🔴')
        self.status_text = QLabel('미연결')
        self.status_text.setStyleSheet("font-weight: bold;")
        status_box.addWidget(self.status_led)
        status_box.addWidget(self.status_text)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addLayout(status_box)
        main_layout.addLayout(header_layout)
        
        # 2. 제어 패널
        control_group = QGroupBox("시스템 제어")
        control_layout = QHBoxLayout()
        
        self.btn_login = QPushButton("로그인")
        self.btn_login.clicked.connect(self.try_login)
        self.btn_login.setStyleSheet("background-color: #4CAF50; border: none;")
        
        self.btn_start = QPushButton("데이터 수집 시작")
        self.btn_start.clicked.connect(self.start_collection)
        self.btn_start.setEnabled(False)
        self.btn_start.setStyleSheet("background-color: #2196F3; border: none;")
        
        self.btn_stop = QPushButton("작업 중지")
        self.btn_stop.clicked.connect(self.stop_collection)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("background-color: #f44336; border: none;")
        
        control_layout.addWidget(self.btn_login)
        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # 3. 진행 상황 표시
        progress_group = QGroupBox("작업 진행 상황")
        progress_layout = QVBoxLayout()
        
        self.lbl_progress = QLabel("대기 중...")
        self.progress_bar = QProgressBar()
        
        progress_layout.addWidget(self.lbl_progress)
        progress_layout.addWidget(self.progress_bar)
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # 4. 로그 뷰어
        log_group = QGroupBox("시스템 로그")
        log_layout = QVBoxLayout()
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        log_layout.addWidget(self.log_view)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # 5. 하단 버튼
        footer_layout = QHBoxLayout()
        btn_exit = QPushButton("종료 (Exit)")
        btn_exit.clicked.connect(self.close)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_exit)
        main_layout.addLayout(footer_layout)


    def send_telegram(self, message):
        """Telegram 알림 전송"""
        if not self.BOT_TOKEN or not self.CHAT_ID:
            return  # 미설정이면 아무것도 안 함 (운영 안전)

        try:
            import requests
            url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage"
            data = {'chat_id': self.CHAT_ID, 'text': message}
            # Timeout 2초로 단축
            requests.post(url, json=data, timeout=2)
        except:
            pass

    def check_system_architecture(self):
        """32비트 환경 체크"""
        if sys.maxsize > 2**32:
            self.log_msg("[오류] 64-bit Python이 감지되었습니다! 키움 API는 32-bit Python 환경에서만 작동합니다.")
            self.log_msg("C:\\Python39-32\\python.exe 등을 사용하여 실행해주세요.")
            # Blocking Popup Removed for Operational Safety
            sys.exit(1)

    # --- 키움 연결 관련 ---
    def try_login(self):
        """로그인 시도"""
        if self.ocx.dynamicCall("GetConnectState()") == 1:
            self.log_msg("이미 연결되어 있습니다. (자동 시작 트리거)")
            # [Fix] 이미 연결된 상태면 수동으로 이벤트 트리거
            self._on_event_connect(0)
            return
        
        self.log_msg("키움증권 로그인 시도 중...")
        self.ocx.dynamicCall("CommConnect()")

    def _on_event_connect(self, err_code):
        """로그인 이벤트 콜백"""
        if err_code == 0:
            # Server Type Check
            gubun = self.ocx.dynamicCall("GetLoginInfo(QString)", "GetServerGubun").strip()
            self.server_type = "MOCK" if gubun == "1" else "REAL"
            
            self.log_msg(f"로그인 성공! (세션 연결됨) - 서버: {self.server_type}")
            self.status_led.setText('🟢')
            self.status_text.setText('연결됨')
            self.btn_login.setEnabled(False)
            self.btn_login.setText("로그인 완료")
            self.btn_start.setEnabled(True)
            self._create_session_flag()
            
            # [NEW] Auto-Subscribe Realtime Feed
            QTimer.singleShot(2000, self._subscribe_realtime_feed)
            
            # 자동 수집 시작 안내
            self.log_msg("[자동화] 5초 후 데이터 수집을 자동으로 시작합니다.")
            QTimer.singleShot(5000, self.start_collection)
        else:
            self.log_msg(f"로그인 실패 (에러 코드: {err_code})")
            self.status_led.setText('🔴')
            self.status_text.setText('실패')

    def _create_session_flag(self):
        """다른 프로세스가 세션 상태를 알 수 있도록 플래그 파일 생성"""
        try:
            flag_path = project_root / "GARAM_Data/kiwoom_ready.flag"
            flag_path.parent.mkdir(exist_ok=True)
            flag_path.touch()
        except Exception:
            pass
            
    def closeEvent(self, event):
        """종료 시 플래그 파일 삭제"""
        flag_path = project_root / "GARAM_Data/kiwoom_ready.flag"
        if flag_path.exists():
            flag_path.unlink()
        event.accept()

    # --- 주문 실행 로직 (Phase 4: EXECUTION) ---
    # --- 주문 실행 로직 (Phase 4: EXECUTION) ---
    def _sweep_stale_processing(self, max_age_sec: int = 120):
        """120초 이상 Processing에 머문 파일 강제 REJ 처리 (Stuck Reaper)"""
        try:
            now = time.time()
            proc_dir = self.order_dir / "processing"
            if not proc_dir.exists(): return
            
            for f in proc_dir.glob("req_*.json"):
                if f.name.endswith(".tmp"): continue
                
                try:
                    age = now - f.stat().st_mtime
                    if age > max_age_sec:
                        idem = f.stem[4:] if f.stem.startswith("req_") else f.stem
                        self.log_msg(f"⚠️ [STALE] processing stuck {f.name} age={int(age)}s -> REJ(manual)")
                        self._archive_order(f, {"idempotency_key": idem}, False, f"STALE_PROCESSING>{max_age_sec}s")
                except OSError:
                    pass
        except Exception:
            pass

    def _check_order_files(self):
        """주문 요청 파일 감시 (Processing Lock + Schema Check + FIFO)"""
        try:
            # 0. Clean Stale Processing (Zombie files)
            self._sweep_stale_processing(max_age_sec=120)

            # 1. json 파일 스캔 (Inbox & Root support)
            # Filter out .tmp and hidden files
            all_files = list(self.order_dir.glob("req_*.json")) + list((self.order_dir / "inbox").glob("req_*.json"))
            files = [p for p in all_files if not p.name.endswith(".tmp") and not p.name.startswith(".")]
            
            if not files:
                return
                
            # 2. FIFO 정렬 (mtime 기준 + Name deterministic tie-breaker) 
            # 파일명이 hash라 랜덤하므로 반드시 시간으로 정렬해야 함
            files.sort(key=lambda p: (p.stat().st_mtime_ns, p.name))
            target_file_inbox = files[0]
            
            # [HOTFIX 3] Move to 'processing' to Lock
            processing_dir = self.order_dir / "processing"
            target_file = processing_dir / target_file_inbox.name
            
            try:
                import shutil, os
                # Atomic Move
                os.replace(str(target_file_inbox), str(target_file))
            except Exception:
                # Race condition: someone else took it
                return

            order_data = {}
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    import json
                    order_data = json.load(f)
                    
                self.log_msg(f"📝 [주문감지] {order_data.get('symbol')} {order_data.get('order_type')} {order_data.get('qty')}주")
                
                # [HOTFIX 3] Schema Validation
                valid, reject_reason = self._validate_order(order_data)
                
                if not valid:
                     self.log_msg(f"⚠️ [주문거절] 유효성 검사 실패: {reject_reason}")
                     self._archive_order(target_file, order_data, False, f"REJ: {reject_reason}")
                     return

                # 3. 주문 전송
                success, msg = self._send_kiwoom_order(order_data)
                
                # 4. 처리 완료 (Archive + ACK/REJ)
                self._archive_order(target_file, order_data, success, msg)
                
            except json.JSONDecodeError:
                self.log_msg(f"⚠️ [주문오류] JSON 파싱 실패 (Corrupted). REJ 처리.")
                # Clean Idem Extraction for REJ filename
                stem = target_file.stem
                idem = stem[4:] if stem.startswith("req_") else stem
                self._archive_order(target_file, {"idempotency_key": idem}, False, "JSONDecodeError")
                
            except Exception as e:
                self.log_msg(f"[주문오류] 처리 중 예외: {e}")
                self._archive_order(target_file, order_data, False, f"Exception: {e}")

        except Exception as e:
            self.log_msg(f"[주문오류] 파일 감지/처리 중 실패: {e}")

    def _validate_order(self, d: dict) -> tuple[bool, str]:
        sym = str(d.get("symbol","")).strip()
        if not (sym.isdigit() and len(sym) == 6):
            return False, f"invalid symbol={sym}"
        ot = str(d.get("order_type","")).lower().strip()
        if ot not in ("buy","sell"):
            return False, f"invalid order_type={ot}"
        try:
            qty = int(d.get("qty", 0))
        except:
            return False, "qty not int"
        if qty <= 0:
            return False, f"qty<=0 ({qty})"
        pt = str(d.get("price_type","03")).strip()
        if pt not in ("03",):  # MVP Market Only check
            return False, f"unsupported price_type={pt}"
        return True, "ok"

    def _archive_order(self, file_path, order_data, success, message):
        """주문 파일 Archive 및 ACK/REJ 생성"""
        try:
            import shutil
            
            file_path = Path(file_path)
            
            # 1. Move to Archive
            archive_dir = self.order_dir / "archive"
            dest = archive_dir / file_path.name
            if dest.exists(): dest.unlink()
            shutil.move(str(file_path), str(dest))
            
            # 2. Generate ACK/REJ
            import json
            idem_key = order_data.get('idempotency_key', file_path.stem)
            
            result_data = {
                "original_request": order_data,
                "process_time": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "status": "SUCCESS" if success else "FAILURE",
                "message": message
            }
            
            res_dir = self.order_dir / ("ack" if success else "rej")
            res_prefix = "ack" if success else "rej"
            out_path = res_dir / f"{res_prefix}_{idem_key}.json"
            
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=4, ensure_ascii=False)
                
            self.log_msg(f"  -> {out_path.name} 생성 완료")
            
        except Exception as e:
            self.log_msg(f"[Archive Critical] {e}")

    def _send_kiwoom_order(self, order_data):
        """실제 키움 주문 전송 (SendOrder) -> returns (bool, msg)"""
        # GetConnectState 확인
        if self.ocx.dynamicCall("GetConnectState()") != 1:
            return False, "키움 미연결 상태"

        rq_name = f"Order_{order_data.get('timestamp', int(time.time()))}"
        screen_no = "1000" 
        
        # 계좌번호 조회
        acc_no = ""
        acc_list = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO").split(';')
        acc_list = [a.strip() for a in acc_list if a.strip()]
        if acc_list:
            acc_no = acc_list[0]
            
        if not acc_no:
            return False, "유효한 계좌번호 없음"

        order_type_map = {'buy': 1, 'sell': 2}
        nOrderType = order_type_map.get(order_data.get('order_type'), 1)
        
        # SendOrder
        symbol = order_data.get('symbol', '')
        qty = int(order_data.get('qty', 0))
        price = int(order_data.get('price', 0))
        price_type = order_data.get('price_type', '03') # 03:시장가
        
        if qty <= 0:
             return False, f"수량 0 이하 ({qty})"
        
        ret = self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [rq_name, screen_no, acc_no, nOrderType, symbol, 
             qty, price, price_type, ""]
        )
        
        if ret == 0:
            msg = f"주문전송성공: {symbol} {qty}주"
            self.log_msg(f"🚀 {msg}")
            return True, msg
        else:
            msg = f"주문전송실패 ErrorCode: {ret}"
            self.log_msg(f"❌ {msg}")
            return False, msg

    # --- 데이터 수집 로직 ---
    def start_collection(self):
        """데이터 수집 시작 진입점"""
        if self.is_collecting:
            return
            
        self.is_collecting = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        self.log_msg("="*50)
        self.log_msg("데이터 수집 엔진 가동 (Health Optimized)")
        self.log_msg(f"- 페이지 간격: {self.PAGE_DELAY_MS/1000}초")
        self.log_msg(f"- 종목 간 간격: {self.SYMBOL_DELAY_MS/1000}초")
        self.log_msg("="*50)
        
        # 파일 상태 분석 시작 (UI 멈춤 방지를 위해 짧은 딜레이 후 실행)
        self.log_msg("종목 및 파일 상태 분석 중... (잠시만 기다려주세요)")
        QTimer.singleShot(100, self._scan_targets)

    def stop_collection(self):
        """작업 중지"""
        self.is_collecting = False
        self.log_msg("[중단] 사용자에 의한 작업 중지 요청.")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _scan_targets(self):
        """대상 종목 스캔 및 우선순위 큐 생성"""
        try:
            universe_path = project_root / "GARAM_Data/real_universe_400.csv"
            if not universe_path.exists():
                self.log_msg(f"[오류] 유니버스 파일이 없습니다: {universe_path}")
                self.stop_collection()
                return

            # Read CSV with flexible column handling
            try:
                universe_df = pd.read_csv(universe_path)
                col = None
                for c in ["Code", "symbol", "code", "Symbol"]:
                    if c in universe_df.columns:
                        col = c
                        break
                
                if col is None:
                    self.log_msg(f"[오류] 유니버스 파일 컬럼 인식 실패: {universe_df.columns.tolist()}")
                    self.stop_collection()
                    return

                all_symbols = universe_df[col].astype(str).str.zfill(6).unique().tolist()
            except Exception as e:
                self.log_msg(f"[오류] 유니버스 파일 읽기 실패: {e}")
                self.stop_collection()
                return
            
            queue = []
            today_date = datetime.now().date()
            
            self.log_msg(f"총 관리 종목 수: {len(all_symbols)}개")
            
            # --- [Priority Check] Targeted Re-collection ---
            recollect_file = project_root / "recollect_targets.txt"
            target_list_mode = False
            
            if recollect_file.exists():
                self.log_msg(f"🎯 [긴급] 재수집 타겟 파일 감지됨! (recollect_targets.txt)")
                try:
                    with open(recollect_file, "r", encoding="utf-8") as f:
                        targets = [line.strip().zfill(6) for line in f if line.strip().isdigit()]
                    
                    if targets:
                        self.log_msg(f"-> {len(targets)}개 종목을 우선수집 큐에 등록합니다.")
                        for sym in targets:
                            queue.append((0, sym, "Targeted Re-collection"))
                        target_list_mode = True
                    else:
                         self.log_msg(f"-> [주의] 타겟 파일이 비어있거나 유효한 종목이 없습니다. 전체 스캔으로 전환합니다.")
                        
                except Exception as e:
                    self.log_msg(f"[경고] 타겟 파일 읽기 실패 ({e}), 전체 스캔으로 전환합니다.")

            # If no target queue (or empty target file), build full queue
            if not queue:
                # 일반 전체 스캔 (Smart Gap Fill 적용)
                for sym in all_symbols:
                    queue.append((5, sym, "Routine Scan"))
                    
            # 큐 정렬
            queue.sort(key=lambda x: x[0])
            self.collection_queue = queue
            self.total_targets = len(queue)
            
            self.log_msg(f"작업 큐 생성 완료: {self.total_targets}개")
            if target_list_mode:
                 self.log_msg(f"모드: 타겟 집중 수집 (Target List Only)")
            else:
                 self.log_msg(f"모드: 전체 유니버스 스마트 수집 (Smart Gap Fill)")

            self.success_count = 0
            self.fail_count = 0
            self.processed_count = 0
            
            self.progress_bar.setRange(0, self.total_targets)
            self.progress_bar.setValue(0)
            
            # 첫 번째 종목 처리 시작
            QTimer.singleShot(500, self._process_next_item)

        except Exception as e:
            self.log_msg(f"[치명적 오류] 작업 스캔 중 예외 발생: {e}")
            import traceback
            self.log_msg(traceback.format_exc())
            self.stop_collection()
            
            self.collection_queue = queue
            self.total_targets = len(queue)
            self.processed_count = 0
            self.success_count = 0
            self.fail_count = 0
            
            self.log_msg(f"수집 대상: {self.total_targets}개 (나머지는 최신 상태)")
            self.progress_bar.setMaximum(self.total_targets)
            self.progress_bar.setValue(0)
            
            if self.total_targets == 0:
                self.log_msg("모든 데이터가 최신입니다. 작업을 종료합니다.")
                self.stop_collection()
                return
                
            # 수집 시작
            self._process_next_item()
            
        except Exception as e:
            self.log_msg(f"[오류] 스캔 중 치명적 오류: {e}")
            self.stop_collection()

    def _process_next_item(self):
        """큐에서 다음 종목을 꺼내 처리"""
        if not self.is_collecting:
            return
            
        if not self.collection_queue:
            self.log_msg("="*50)
            self.log_msg(f"사이클 완료! (성공:{self.success_count} 실패:{self.fail_count})")
            
            # Continuous Loop Logic
            now = datetime.now()
            # Market hours: 09:00 ~ 15:30 (Simplified check: Stop after 15:35)
            # If current time is before 15:35, we restart.
            is_market_open = (now.hour < 15) or (now.hour == 15 and now.minute <= 35)
            
            if is_market_open:
                delay_sec = 60
                self.log_msg(f"[Continuous] 장 운영 중입니다. {delay_sec}초 후 다시 스캔합니다...")
                self.log_msg("="*50)
                QTimer.singleShot(delay_sec * 1000, self._scan_targets)
                return
            else:
                self.log_msg("[종료] 장 마감 시간 경과. 수집을 완전 종료합니다.")
                self.log_msg("="*50)
                self.stop_collection()
                return
            
        # 큐에서 하나 꺼내기
        priority, symbol, reason = self.collection_queue.pop(0)
        self.current_symbol = symbol
        self.current_page = 0
        self.current_data_buffer = [] # 버퍼 초기화
        self.retry_count = 0
        
        self.processed_count += 1
        self.progress_bar.setValue(self.processed_count)
        self.lbl_progress.setText(f"진행: {self.processed_count}/{self.total_targets} - 현재종목: {symbol} ({reason})")
        self.log_msg(f"[{self.processed_count}/{self.total_targets}] {symbol} 데이터 요청 시작... ({reason})")
        
        # TR 요청 시작 (0페이지)
        self._request_kiwoom_data(symbol, self.current_page)

    def _request_kiwoom_data(self, symbol, page):
        """TR 요청 전송"""
        if not self.is_collecting: return

        # 입력값 설정 (opt10080: 주식분봉차트조회)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", symbol)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "틱범위", "1")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        
        # TR 요청
        # prev_next: 0(초기), 2(연속)
        prev_next = 2 if page > 0 else 0
        
        ret = self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", 
                                   "opt10080", "opt10080", prev_next, "0101")
        
        if ret != 0:
            self.log_msg(f"[오류] TR 요청 실패 (코드: {ret})")
            self.fail_count += 1
            # 실패 시 약간 대기 후 다음 종목으로
            QTimer.singleShot(1000, self._process_next_item)
        else:
            # 타임아웃 타이머 시작 (20초 - 안정성 강화)
            self.tr_timer.start(20000)

    def _on_tr_timeout(self):
        """TR 응답 타임아웃 처리"""
        if not self.is_collecting: return
            
        self.retry_count += 1
        self.log_msg(f"[지연] {self.current_symbol} 응답 없음. 재시도 ({self.retry_count}/3)")
        
        if self.retry_count <= 3:
            # 2초 후 재요청
            QTimer.singleShot(2000, lambda: self._request_kiwoom_data(self.current_symbol, self.current_page))
        else:
            self.log_msg(f"[실패] {self.current_symbol} 3회 재시도 실패. 건너뜁니다.")
            self.fail_count += 1
            self._process_next_item()

    # --- [NEW] Chejan (Execution/Balance) Handler ---
    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """
        체결/잔고 데이터 수신 (Gubun: 0=주문체결/접수, 1=잔고, 3=특수)
        """
        try:
            # We focus on Gubun 0 (Execution) for Fills
            if gubun == "0":
                # FIDs: 9203:Order ID, 9001:Symbol, 913:Status, 905:Side, 911:FilledQty, 910:Price
                status = self.ocx.dynamicCall("GetChejanData(int)", 913).strip()
                if not status: return

                order_id = self.ocx.dynamicCall("GetChejanData(int)", 9203).strip()
                symbol = self.ocx.dynamicCall("GetChejanData(int)", 9001).strip()
                if symbol.startswith("A"): symbol = symbol[1:] # A005930 -> 005930
                
                side_raw = self.ocx.dynamicCall("GetChejanData(int)", 905).strip()
                side = "BUY" if "매수" in side_raw else "SELL"
                
                filled_qty = self.ocx.dynamicCall("GetChejanData(int)", 911).strip()
                filled_price = self.ocx.dynamicCall("GetChejanData(int)", 910).strip()
                
                # Kiwoom returns empty string if 0
                if not filled_qty: filled_qty = "0"
                if not filled_price: filled_price = "0"
                
                fq = int(filled_qty)
                
                # Log only if there is a fill quantity > 0 (Execution)
                if fq > 0:
                    self.log_msg(f"⚡ [체결] {symbol} {side} {fq}주 @ {filled_price}")
                    
                    # Write to File (CSV Append)
                    fill_file = project_root / "GARAM_Data/orders/chejan_fills.csv"
                    # CSV Schema: ts, order_id, symbol, side, price, qty
                    
                    try:
                        import csv
                        is_new = not fill_file.exists()
                        # Ensure dir
                        fill_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(fill_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            if is_new:
                                writer.writerow(["ts", "order_id", "symbol", "side", "price", "qty"])
                            
                            writer.writerow([
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                order_id,
                                symbol,
                                side,
                                filled_price,
                                str(fq)
                            ])
                    except Exception as e:
                        print(f"[Chejan] Write Error: {e}")
                        
        except Exception as e:
            print(f"[Chejan] Error: {e}")

    def _on_receive_msg(self, scr_no, rq_name, tr_code, msg):
        """서버 메시지 수신"""
        # "조회완료" 같은 단순 메시지는 로그 생략 가능하지만 일단 출력
        if "조회완료" not in msg:
            self.log_msg(f"[서버메시지] {msg.strip()} (코드: {tr_code})")

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, prev_next, data_len, err_code, msg1, msg2):
        """데이터 수신 처리"""
        if rqname == "opt10014_req":
            self.tr_timer.stop()
            self._on_receive_tr_data_short(trcode, record_name)
            return

        if rqname != "opt10080":
            return
            
        # 타이머 정지
        self.tr_timer.stop()
            
        if not self.is_collecting: return
            
        try:
            # 1. 데이터 개수 확인
            count = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, record_name)
            
            if count == 0:
                self._finish_symbol_processing()
                return
                
            # 2. 데이터 파싱
            rows = []
            for i in range(count):
                date = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "체결시간").strip()
                open_ = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "시가").strip() or 0))
                high = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "고가").strip() or 0))
                low = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "저가").strip() or 0))
                close = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "현재가").strip() or 0))
                vol = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "거래량").strip() or 0))
                
                rows.append({
                    'date': date, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': vol
                })
                
            if rows:
                self.current_data_buffer.append(pd.DataFrame(rows))
                
            # 3. 다음 페이지 조회 여부 결정
            # Smart Backfill Logic (Incremental Stop)
            out_file = self.output_dir / f"{self.current_symbol}.csv"
            max_limit = 1200 # Default to Deep Backfill
            should_stop_early = False
            
            if out_file.exists():
                try:
                    # Check coverage
                    # We need to read the LAST line (oldest date) to check span
                    # Efficient reading of last line?
                    # For now, just read CSV. It's safe for 2-year 1m data (~20MB).
                    df_check = pd.read_csv(out_file)
                    if not df_check.empty and 'date' in df_check.columns:
                        dates = pd.to_datetime(df_check['date'].astype(str), format='%Y%m%d%H%M%S', errors='coerce')
                        start_dt = dates.min()
                        end_dt = dates.max()
                        
                        # --- [NEW] Strict Incremental Stop ---
                        # If the oldest date in current received batch is NEWER or EQUAL to existing file's latest date,
                        # it means we have fully bridged the gap. We can stop.
                        # Wait, Kiwoom sends data newest to oldest. 
                        # Rows[0] is newest, Rows[-1] is oldest in this batch.
                        if rows:
                            batch_oldest_str = rows[-1]['date'] # YYYYMMDDHHMMSS
                            batch_oldest_dt = datetime.strptime(batch_oldest_str, '%Y%m%d%H%M%S')
                            
                            if pd.notna(end_dt) and batch_oldest_dt <= end_dt:
                                self.log_msg(f"  [Smart] 데이터 연결 완료 ({batch_oldest_str} <= {end_dt}). 수집 중단.")
                                should_stop_early = True
                        
                        if pd.notna(start_dt) and pd.notna(end_dt):
                            days_covered = (end_dt - start_dt).days
                            if days_covered > 600:
                                # self.log_msg(f"  [Info] 2년치 데이터 보유중 ({days_covered}일). 업데이트 모드 전환.")
                                max_limit = 50 # Update only
                except Exception as e:
                    # self.log_msg(f"Smart check error: {e}")
                    pass
            
            has_next = (prev_next == '2') and (self.current_page < max_limit) and (not should_stop_early)
            
            if has_next:
                self.current_page += 1
                QTimer.singleShot(self.PAGE_DELAY_MS, lambda: self._request_kiwoom_data(self.current_symbol, self.current_page))
            else:
                self._finish_symbol_processing()
                
        except Exception as e:
            self.log_msg(f"[오류] 데이터 파싱 실패: {e}")
            self.fail_count += 1
            QTimer.singleShot(2000, self._process_next_item)
    def _process_short_data(self):
        """[Step 2] 공매도 데이터 요청 (opt10014)"""
        symbol = self.current_symbol
        today = datetime.now().strftime("%Y%m%d")
        
        # Check if today's short data already exists
        short_file = self.short_dir / f"{symbol}.csv"
        need_update = True
        
        if short_file.exists():
            try:
                # Read first line or check mod time
                # If modified today, maybe skip? But let's overwrite to be safe for "Today's Close"
                pass
            except:
                pass
                
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", symbol)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "시간별구분", "1") # 1: 일별
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "일자", today)     # End Date
        
        # Request
        # RQName must be unique or distinct from opt10080
        ret = self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", 
                                   "opt10014_req", "opt10014", 0, "0101")
        
        if ret != 0:
            self.log_msg(f"[Short] 요청 실패: {ret} -> Skip")
            # Fail silently and move next
            self._finish_symbol_processing()
        else:
            # Wait for TR (Timer reuse)
            self.tr_timer.start(5000) # Short data is small, 5s timeout enough

    def _finish_symbol_processing(self):

        """종목 수집 완료 및 저장"""
        try:
            symbol = self.current_symbol
            out_file = self.output_dir / f"{symbol}.csv"
            
            if self.current_data_buffer:
                # 버퍼 병합
                new_df = pd.concat(self.current_data_buffer, ignore_index=True)
                
                # 기존 파일과 병합
                if out_file.exists():
                     try:
                        old_df = pd.read_csv(out_file)
                        
                        # 컬럼명 통일 (혹시 모를 한글 컬럼 처리)
                        rename_map = {
                            '체결시간': 'date', '시가': 'open', '고가': 'high', 
                            '저가': 'low', '현재가': 'close', '거래량': 'volume',
                            'datetime': 'date' # Support migration format
                        }
                        old_df.rename(columns=rename_map, inplace=True)
                        
                        # TYPE UNIFICATION (CRITICAL FIX)
                        old_df['date'] = old_df['date'].astype(str)
                        new_df['date'] = new_df['date'].astype(str)
                        
                        combined = pd.concat([old_df, new_df], ignore_index=True)
                        combined = combined.drop_duplicates(subset=['date'], keep='first')
                        combined = combined.sort_values('date', ascending=False)
                        
                        # VALIDATION: Data Integrity Check
                        if len(combined) < len(old_df):
                            raise ValueError(f"Data loss detected! Old: {len(old_df)}, New Combined: {len(combined)}")
                            
                     except Exception as e:
                        self.log_msg(f"  [오류] 병합 실패! 건너뜁니다: {e}")
                        self.fail_count += 1
                        # Fail Fast: Do not save corrupted data
                        QTimer.singleShot(self.SYMBOL_DELAY_MS, self._process_next_item)
                        return
                else:
                    combined = new_df
                    combined['date'] = combined['date'].astype(str) # Ensure string for new files too
                
                # 최종 저장
                # 컬럼 순서 고정
                cols = ['date', 'open', 'high', 'low', 'close', 'volume']
                valid_cols = [c for c in cols if c in combined.columns]
                combined = combined[valid_cols]
                
                # --- [SSOT V2] Atomic Write via Wrapper ---
                paths = get_ingest_paths()
                final_path = write_minute_csv(symbol, combined, paths.minute_dir)
                self.log_msg(f"  -> 저장 완료 (Standard): {final_path} (총 {len(combined)}건)")
                self.success_count += 1
            else:
                self.log_msg(f"  -> 수신된 데이터 없음")
                self.fail_count += 1
                
            # Telegram Report (Every 50)
            if self.processed_count % 50 == 0:
                msg = f"📊 [Garam 수집] {self.processed_count}/{self.total_targets} 완료. (성공:{self.success_count})"
                self.send_telegram(msg)
                
        except Exception as e:
            self.log_msg(f"[저장 오류] {e}")
            self.fail_count += 1
            
        # [CHAINING] 분봉 수집 완료 -> 공매도 수집 시작
        # QTimer.singleShot(self.SYMBOL_DELAY_MS, self._process_next_item)
        
        # Check if we should collect short data (Always ON for now or separate flag?)
        # Let's chain it. 
        QTimer.singleShot(500, self._process_short_data)

    def _on_receive_tr_data_short(self, trcode, record_name):
        """공매도 데이터 수신 (opt10014)"""
        try:
            count = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, record_name)
            if count == 0:
                self._finish_symbol_processing_final()
                return

            rows = []
            # Recent 100 days is enough for Short Squeeze Hunter
            limit = min(count, 100) 
            
            for i in range(limit):
                date = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "일자").strip()
                close = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "종가").strip() or 0))
                short_vol = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "공매도수량").strip() or 0))
                short_amt = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "공매도금액").strip() or 0))
                short_ratio = float(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "공매도비중").strip() or 0.0)
                avg_price = abs(int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "공매도평균가").strip() or 0))
                
                rows.append({
                    "date": date,
                    "close": close,
                    "short_vol": short_vol,
                    "short_amt": short_amt,
                    "short_ratio": short_ratio,
                    "short_avg_price": avg_price
                })
                
            if rows:
                df = pd.DataFrame(rows)
                out_path = self.short_dir / f"{self.current_symbol}.csv"
                df.to_csv(out_path, index=False, encoding='utf-8')
                # self.log_msg(f"  -> [Short] {len(rows)}일치 저장 완료")
                
        except Exception as e:
            self.log_msg(f"[Short] 파싱 오류: {e}")
            
        self._finish_symbol_processing_final()

    def _finish_symbol_processing_final(self):
        """진짜 완료 -> 다음 종목"""
        QTimer.singleShot(self.SYMBOL_DELAY_MS, self._process_next_item)


    # --- [NEW] Realtime Feed Handlers (Hotfix Injection) ---
    def _subscribe_realtime_feed(self):
        """Register all universe symbols for Realtime Tick Data"""
        self.log_msg("[Realtime] Subscribing to 400 symbols...")
        # Use existing logic logic from previous failed attempt
        universe_path = project_root / "GARAM_Data/real_universe_400.csv"
        codes = []
        if universe_path.exists():
            with open(universe_path, 'r', encoding='utf-8') as f:
                 for line in f:
                     c = line.split(',')[0].strip()
                     if c: codes.append(c)
        else:
            self.log_msg(f"[Warn] Universe file not found: {universe_path}")
            return

        # Batch Register
        fids = ";".join(self.tick_fids.values())
        screen_no = "1000"
        BATCH_SIZE = 80
        
        # Clear first
        self.ocx.dynamicCall("SetRealRemove(QString, QString)", screen_no, "ALL")
        
        for i in range(0, len(codes), BATCH_SIZE):
            chunk = codes[i:i+BATCH_SIZE]
            code_str = ";".join(chunk)
            opt = "0" if i==0 else "1"
            self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_no, code_str, fids, opt)
            
        self.log_msg(f"[Realtime] Registered {len(codes)} symbols for TICK feed.")

    def _on_receive_realdata(self, code, real_type, real_data):
        """Handle Realtime Ticks -> Push to Deque"""
        try:
            # Only care about ticks (Price/Vol)
            price_fid = self.tick_fids["price"]
            vol_fid = self.tick_fids["volume"]
            
            def get_fid(fid): # Helper
                return self.ocx.dynamicCall("GetCommRealData(QString, int)", code, int(fid)).strip()
            
            price_raw = get_fid(price_fid)
            vol_raw = get_fid(vol_fid)
            
            if not price_raw: return 
            
            # Normalize
            price = int(str(price_raw).replace(",","").lstrip("+-"))
            volume = int(str(vol_raw).replace(",","").lstrip("+-")) if vol_raw else 0
            
            evt = {
                "event_id": uuid.uuid4().hex,
                "event_type": "TICK",
                "event_time": datetime.now(timezone.utc).isoformat(),
                "ingest_time": datetime.now(timezone.utc).isoformat(),
                "symbol": code,
                "payload": {
                    "price": price,
                    "volume": volume,
                    "real_type": real_type
                }
            }
            self.real_dq.append(evt)
            
        except Exception as e:
            # Fail silently to avoid GUI lag
            pass

    
    def _check_schedule(self):
        """Schedule Check (08:30 Re-login, 16:00 Shutdown)"""
        now = datetime.now()
        
        # 1. 08:30 Re-login (Restart)
        # Condition: Time is 08:30 AND App has been running for > 10 mins (avoid restart loop)
        if now.hour == 8 and now.minute == 30:
            runtime = (now - self.start_time).total_seconds()
            if runtime > 600: 
                self.log_msg("⏰ [스케줄] 08:30 정기 재로그인(재시작)을 수행합니다.")
                import sys, os
                os.execl(sys.executable, sys.executable, *sys.argv)
        
        # 2. 16:00 Shutdown (Lockout)
        elif now.hour == 16 and now.minute == 0:
            self.log_msg("⏰ [스케줄] 16:00 장 마감 후 자동 종료(Lockout)를 수행합니다.")
            QTimer.singleShot(3000, self.close) # Graceful Close

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = KiwoomSystemWindow()
    window.show()
    sys.exit(app.exec_())
