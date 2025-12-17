# -*- coding: utf-8 -*-
"""
키움 데이터 수집 및 관리 시스템 (통합 버전)
- 기존 CLI 스크립트들의 파편화 문제를 해결하기 위해 GUI 기반으로 통합.
- 윈도우 이벤트 루프(QAxWidget)를 사용하여 안정적인 로그인 및 TR 송수신 보장.
- 400개 종목에 대한 증분 수집 및 자동 업데이트 기능 포함.
"""

import sys
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime
import time

# PyQt5 임포트
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                             QVBoxLayout, QWidget, QMessageBox, QTextEdit, 
                             QProgressBar, QHBoxLayout, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QAxContainer import QAxWidget

# 프로젝트 루트 경로 설정 (c:\garam\garam)
# 프로젝트 루트 경로 설정 (c:\garam\garam) - pipeline/01_ingest/ 에서 3단계 위
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# --- [SSOT V2] Ingest Wrapper Imports ---
from pipeline._01_ingest.paths import get_ingest_paths
from pipeline._01_ingest.write_csv import write_minute_csv

# 로깅 설정 (한글 로그 파일)
logger = logging.getLogger(__name__)
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "kiwoom_system_log.txt", mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class KiwoomSystemWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # --- 상태 변수 ---
        self.is_collecting = False          # 수집 진행 중 여부
        self.collection_queue = []          # 수집 대기열 [(우선순위, 코드, 사유), ...]
        self.current_symbol = None          # 현재 수집 중인 종목
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
        self.PAGE_DELAY_MS = 600        # 페이지 넘김 간격 (0.6초 - 안전)
        self.SYMBOL_DELAY_MS = 1500     # 종목 변경 간격 (1.5초 - 안전)
        self.MAX_RETRY_COUNT = 3        # 최대 재시도 횟수
        
        # Telegram Config
        self.BOT_TOKEN = '8284381258:AAENGcOgH6B6otI36C9L-AX1MrS_X-pPXRs'
        self.CHAT_ID = '8362308273'

        
        # --- UI 초기화 ---
        self.init_ui()
        self.check_system_architecture()
        
        # --- 키움 OCX 컨트롤 생성 ---
        try:
            self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
            self.ocx.OnEventConnect.connect(self._on_event_connect)        # 로그인 이벤트
            self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)     # TR 데이터 수신
            self.ocx.OnReceiveMsg.connect(self._on_receive_msg)            # 메시지 수신
        except Exception as e:
            self.log_msg(f"[치명적 오류] 키움 OpenAPI 컨트롤 생성 실패: {e}")
            self.log_msg("OpenAPI가 올바르게 설치되지 않았거나 레지스트리 문제가 있을 수 있습니다.")
            QMessageBox.critical(self, "오류", "키움 OpenAPI 컨트롤 생성 실패.\n설치 상태를 확인하세요.")

        # 타이머 설정 (타임아웃 감지용)
        self.tr_timer = QTimer(self)
        self.tr_timer.setSingleShot(True)
        self.tr_timer.timeout.connect(self._on_tr_timeout)

        # 하트비트 (세션 플래그 생성, 1분 간격)
        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(self._create_session_flag)
        self.heartbeat_timer.start(60000)
        
        # 자동 로그인 트리거 (1초 후)
        QTimer.singleShot(1000, self.try_login)
        
        # 주문 감시 타이머 (0.5초 간격)
        self.order_timer = QTimer(self)
        self.order_timer.timeout.connect(self._check_order_files)
        self.order_timer.start(500)
        
        self.order_dir = project_root / "garamdata/orders"
        self.order_dir.mkdir(parents=True, exist_ok=True)

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

    def log_msg(self, msg):
        """로그 출력 함수 (화면 + 파일)"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        full_msg = f"{timestamp} {msg}"
        self.log_view.append(full_msg)
        
        # 자동 스크롤
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())
        
        logger.info(msg)

    def send_telegram(self, message):
        """Telegram 알림 전송"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage"
            data = {'chat_id': self.CHAT_ID, 'text': message}
            requests.post(url, json=data, timeout=3)
        except:
            pass

    def check_system_architecture(self):
        """32비트 환경 체크"""
        if sys.maxsize > 2**32:
            self.log_msg("[오류] 64-bit Python이 감지되었습니다! 키움 API는 32-bit Python 환경에서만 작동합니다.")
            self.log_msg("C:\\Python39-32\\python.exe 등을 사용하여 실행해주세요.")
            QMessageBox.critical(self, "환경 오류", "이 프로그램은 32-bit Python이 필요합니다.")

    # --- 키움 연결 관련 ---
    def try_login(self):
        """로그인 시도"""
        if self.ocx.dynamicCall("GetConnectState()") == 1:
            self.log_msg("이미 연결되어 있습니다.")
            return
        
        self.log_msg("키움증권 로그인 시도 중...")
        self.ocx.dynamicCall("CommConnect()")

    def _on_event_connect(self, err_code):
        """로그인 이벤트 콜백"""
        if err_code == 0:
            self.log_msg("로그인 성공! (세션 연결됨)")
            self.status_led.setText('🟢')
            self.status_text.setText('연결됨')
            self.btn_login.setEnabled(False)
            self.btn_login.setText("로그인 완료")
            self.btn_start.setEnabled(True)
            self._create_session_flag()
            
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
    def _check_order_files(self):
        """주문 요청 파일 감시"""
        try:
            # 1. json 파일 스캔
            files = list(self.order_dir.glob("req_*.json"))
            if not files:
                return
                
            # 2. 가장 오래된 요청부터 처리
            files.sort()
            target_file = files[0]
            
            with open(target_file, 'r', encoding='utf-8') as f:
                import json
                order_data = json.load(f)
                
            self.log_msg(f"📝 [주문감지] {order_data['symbol']} {order_data['order_type']} {order_data['qty']}주")
            
            # 3. 주문 전송
            self._send_kiwoom_order(order_data)
            
            # 4. 처리 완료 파일 삭제 (또는 archived로 이동)
            target_file.unlink()
            
        except Exception as e:
            self.log_msg(f"[주문오류] 파일 처리 중 실패: {e}")

    def _send_kiwoom_order(self, order_data):
        """실제 키움 주문 전송 (SendOrder)"""
        # GetConnectState 확인
        if self.ocx.dynamicCall("GetConnectState()") != 1:
            self.log_msg("[주문실패] 키움 미연결 상태")
            return

        rq_name = f"Order_{order_data['timestamp']}"
        screen_no = "1000" # 주문 화면번호
        acc_no = "" # 계좌번호 (필요 시 config에서 로드하거나 하드코딩)
        # TODO: 계좌번호 조회 로직 필요 (GetLoginInfo)
        
        # 임시: 첫 번째 계좌 사용
        acc_list = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO").split(';')
        if acc_list:
            acc_no = acc_list[0]
            
        if not acc_no:
            self.log_msg("[주문실패] 유효한 계좌번호 없음")
            return

        order_type_map = {'buy': 1, 'sell': 2}
        nOrderType = order_type_map.get(order_data['order_type'], 1)
        
        # SendOrder(
        #  sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo
        # )
        ret = self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [rq_name, screen_no, acc_no, nOrderType, order_data['symbol'], 
             int(order_data['qty']), int(order_data['price']), order_data['price_type'], ""]
        )
        
        if ret == 0:
            self.log_msg(f"🚀 [주문전송성공] {order_data['symbol']}")
        else:
            self.log_msg(f"❌ [주문전송실패] Error Code: {ret}")

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

            universe_df = pd.read_csv(universe_path)
            all_symbols = universe_df['Code'].astype(str).str.zfill(6).tolist()
            
            queue = []
            today_date = datetime.now().date()
            
            self.log_msg(f"총 관리 종목 수: {len(all_symbols)}개")
            
            # --- [Priority Check] Targeted Re-collection ---
            recollect_file = project_root / "recollect_targets.txt"
            if recollect_file.exists():
                self.log_msg(f"🎯 [긴급] 재수집 타겟 파일 감지됨! (recollect_targets.txt)")
                with open(recollect_file, "r") as f:
                    targets = [line.strip() for line in f if line.strip()]
                    
                self.log_msg(f"-> {len(targets)}개 종목을 우선수집 큐에 등록합니다.")
                for sym in targets:
                    queue.append((0, sym, "Targeted Re-collection"))
                
                # 타겟 파일이 있으면 전체 스캔을 할 필요가 있는가? 
                # 사용자 의도는 "누락분만" 이므로 여기서 큐 구성을 마치고 바로 리턴해도 됨.
                # 하지만 기존 로직(전체 스캔)과 병행하려면... 
                # 일단 타겟 파일이 있으면 그것만 처리하도록 하겠습니다 (집중).
                
                queue.sort(key=lambda x: x[0])
                self.collection_queue = queue
                self.total_targets = len(queue)
                
                self.log_msg(f"수집 대상: {self.total_targets}개 (Target List Only)")
                self.progress_bar.setMaximum(self.total_targets)
                self.progress_bar.setValue(0)
                self._process_next_item()
                return

            # 수집 한도 설정 (하루 200개, 혹은 전체)
            # 여기서는 전수 조사를 기본으로 하되, 최신 데이터가 있으면 건너뛰는 방식
            
            for symbol in all_symbols:
                fpath = self.output_dir / f"{symbol}.csv"
                
                # 1. 파일이 아예 없는 경우 (최우선)
                if not fpath.exists():
                    queue.append((0, symbol, "신규 파일 생성"))
                    continue
                    
                # 2. 파일 검사
                try:
                    df = pd.read_csv(fpath)
                    
                    # 컬럼 확인 (체결시간)
                    time_col = None
                    if 'date' in df.columns: time_col = 'date'
                    elif '체결시간' in df.columns: time_col = '체결시간'
                        
                    if df.empty or time_col is None:
                        self.log_msg(f"  [경고] {symbol} 파일 손상 감지 -> 삭제 후 재수집")
                        fpath.unlink(missing_ok=True)
                        queue.append((0, symbol, "파일 손상/자동복구"))
                        continue
                        
                    # 마지막 날짜 확인
                    times = pd.to_datetime(df[time_col], format='%Y%m%d%H%M%S', errors='coerce')
                    last_dt = times.max()
                    
                    if pd.isna(last_dt) or last_dt.date() < today_date:
                         queue.append((1, symbol, f"업데이트 필요 (마지막: {last_dt.date()})"))
                    else:
                        # 이미 오늘 데이터가 있음 -> 건너뜀
                        pass
                except:
                    self.log_msg(f"  [경고] {symbol} 파일 읽기 실패 -> 삭제 후 재수집")
                    if fpath.exists(): fpath.unlink(missing_ok=True)
                    queue.append((0, symbol, "읽기 오류/재수집"))

            # 우선순위 정렬 (0: 긴급, 1: 업데이트)
            queue.sort(key=lambda x: x[0])
            
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
            # 타임아웃 타이머 시작 (15초)
            self.tr_timer.start(15000)

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

    def _on_receive_msg(self, scr_no, rq_name, tr_code, msg):
        """서버 메시지 수신"""
        # "조회완료" 같은 단순 메시지는 로그 생략 가능하지만 일단 출력
        if "조회완료" not in msg:
            self.log_msg(f"[서버메시지] {msg.strip()} (코드: {tr_code})")

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, prev_next, data_len, err_code, msg1, msg2):
        """데이터 수신 처리"""
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
            
        # 다음 종목 처리
        QTimer.singleShot(self.SYMBOL_DELAY_MS, self._process_next_item)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = KiwoomSystemWindow()
    window.show()
    sys.exit(app.exec_())
