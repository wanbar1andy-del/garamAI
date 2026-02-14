# scripts/ops/antigravity_monitor_gui.py
# -*- coding: utf-8 -*-
import sys
import os
import glob
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QFileDialog, QMessageBox, QGroupBox, QHBoxLayout
)

def _now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def _parse_iso_dt(s: str):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

def _read_json(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def _tail_text(path: Path, max_bytes: int = 200_000):
    """
    큰 로그도 빠르게 보기 위해 파일 끝에서 max_bytes만 읽음.
    """
    if not path.exists():
        return ""
    try:
        with path.open("rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            start = max(0, size - max_bytes)
            f.seek(start, os.SEEK_SET)
            data = f.read()
        try:
            return data.decode("utf-8", errors="replace")
        except Exception:
            return data.decode("cp949", errors="replace")
    except Exception as e:
        return f"[ERR] tail failed: {e}"

def _latest_log(log_dir: Path, prefix: str):
    """
    prefix: "stderr_" or "stdout_"
    """
    pats = str(log_dir / f"{prefix}*.log")
    files = glob.glob(pats)
    if not files:
        return None
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return Path(files[0])

def _open_in_explorer(path: Path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))
        else:
            # mac/linux fallback
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(path)])
    except Exception:
        pass

class MonitorGUI(QMainWindow):
    def __init__(self, status_json: Path, logs_dir: Path, heartbeat_timeout_sec: int):
        super().__init__()
        self.setWindowTitle("AntiGravity Monitor (Kiwoom Ops)")
        self.resize(1200, 800)

        self.status_json = status_json
        self.logs_dir = logs_dir
        self.heartbeat_timeout_sec = heartbeat_timeout_sec

        self._watchdog_proc = None  # subprocess.Popen

        root = QWidget()
        self.setCentralWidget(root)
        grid = QGridLayout(root)

        # ===== Top: Paths =====
        gb_paths = QGroupBox("SSOT Paths")
        gb_paths_layout = QGridLayout(gb_paths)

        self.ed_status = QLineEdit(str(self.status_json))
        self.ed_logs = QLineEdit(str(self.logs_dir))

        btn_pick_status = QPushButton("Select status_json")
        btn_pick_logs = QPushButton("Select logs_dir")
        btn_open_status = QPushButton("Open status folder")
        btn_open_logs = QPushButton("Open logs folder")

        btn_pick_status.clicked.connect(self.pick_status_json)
        btn_pick_logs.clicked.connect(self.pick_logs_dir)
        btn_open_status.clicked.connect(lambda: _open_in_explorer(Path(self.ed_status.text()).parent))
        btn_open_logs.clicked.connect(lambda: _open_in_explorer(Path(self.ed_logs.text())))

        gb_paths_layout.addWidget(QLabel("status_json"), 0, 0)
        gb_paths_layout.addWidget(self.ed_status, 0, 1)
        gb_paths_layout.addWidget(btn_pick_status, 0, 2)
        gb_paths_layout.addWidget(btn_open_status, 0, 3)

        gb_paths_layout.addWidget(QLabel("logs_dir"), 1, 0)
        gb_paths_layout.addWidget(self.ed_logs, 1, 1)
        gb_paths_layout.addWidget(btn_pick_logs, 1, 2)
        gb_paths_layout.addWidget(btn_open_logs, 1, 3)

        grid.addWidget(gb_paths, 0, 0, 1, 2)

        # ===== Middle: Status =====
        gb_status = QGroupBox("Live Status (from status_json)")
        gb_status_layout = QGridLayout(gb_status)

        self.lb_step = QLabel("-")
        self.lb_hb = QLabel("-")
        self.lb_hb_age = QLabel("-")
        self.lb_day = QLabel("-")
        self.lb_done = QLabel("-")
        self.lb_last = QLabel("-")
        self.lb_err = QLabel("-")

        for lb in [self.lb_step, self.lb_hb, self.lb_hb_age, self.lb_day, self.lb_done, self.lb_last, self.lb_err]:
            lb.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lb.setFont(QFont("Consolas", 10))

        gb_status_layout.addWidget(QLabel("step"), 0, 0)
        gb_status_layout.addWidget(self.lb_step, 0, 1)

        gb_status_layout.addWidget(QLabel("heartbeat_at"), 1, 0)
        gb_status_layout.addWidget(self.lb_hb, 1, 1)

        gb_status_layout.addWidget(QLabel("hb_age_sec"), 2, 0)
        gb_status_layout.addWidget(self.lb_hb_age, 2, 1)

        gb_status_layout.addWidget(QLabel("current_day"), 3, 0)
        gb_status_layout.addWidget(self.lb_day, 3, 1)

        gb_status_layout.addWidget(QLabel("done/total"), 4, 0)
        gb_status_layout.addWidget(self.lb_done, 4, 1)

        gb_status_layout.addWidget(QLabel("last_result"), 5, 0)
        gb_status_layout.addWidget(self.lb_last, 5, 1)

        gb_status_layout.addWidget(QLabel("last_error"), 6, 0)
        gb_status_layout.addWidget(self.lb_err, 6, 1)

        grid.addWidget(gb_status, 1, 0, 1, 1)

        # ===== Right: Controls =====
        gb_ctl = QGroupBox("Controls")
        gb_ctl_layout = QGridLayout(gb_ctl)

        self.ed_watchdog_cmd = QLineEdit("")
        self.ed_watchdog_cmd.setPlaceholderText('watchdog 실행 커맨드 전체 (따옴표 포함), 예: C:\\Python39-32\\python.exe scripts\\ops\\antigravity_watchdog.py ...')

        btn_start = QPushButton("Start Watchdog (optional)")
        btn_stop = QPushButton("Stop Watchdog")
        btn_refresh = QPushButton("Refresh Now")

        btn_start.clicked.connect(self.start_watchdog)
        btn_stop.clicked.connect(self.stop_watchdog)
        btn_refresh.clicked.connect(self.refresh_all)

        gb_ctl_layout.addWidget(QLabel("watchdog_cmd"), 0, 0)
        gb_ctl_layout.addWidget(self.ed_watchdog_cmd, 1, 0, 1, 2)
        gb_ctl_layout.addWidget(btn_start, 2, 0)
        gb_ctl_layout.addWidget(btn_stop, 2, 1)
        gb_ctl_layout.addWidget(btn_refresh, 3, 0, 1, 2)

        self.lb_watchdog_state = QLabel("watchdog: idle")
        self.lb_watchdog_state.setFont(QFont("Consolas", 10))
        gb_ctl_layout.addWidget(self.lb_watchdog_state, 4, 0, 1, 2)

        grid.addWidget(gb_ctl, 1, 1, 1, 1)

        # ===== Bottom: Logs =====
        gb_logs = QGroupBox("Logs (auto: newest stderr/stdout)")
        gb_logs_layout = QGridLayout(gb_logs)

        self.tx_stderr = QTextEdit()
        self.tx_stdout = QTextEdit()
        self.tx_stderr.setReadOnly(True)
        self.tx_stdout.setReadOnly(True)
        self.tx_stderr.setFont(QFont("Consolas", 9))
        self.tx_stdout.setFont(QFont("Consolas", 9))

        gb_logs_layout.addWidget(QLabel("stderr (newest)"), 0, 0)
        gb_logs_layout.addWidget(QLabel("stdout (newest)"), 0, 1)
        gb_logs_layout.addWidget(self.tx_stderr, 1, 0)
        gb_logs_layout.addWidget(self.tx_stdout, 1, 1)

        grid.addWidget(gb_logs, 2, 0, 1, 2)

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_all)
        self.timer.start(1000)  # 1s

        self.refresh_all()

    def pick_status_json(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Select status_json", "", "JSON (*.json);;All (*.*)")
        if fn:
            self.ed_status.setText(fn)

    def pick_logs_dir(self):
        dn = QFileDialog.getExistingDirectory(self, "Select logs_dir", "")
        if dn:
            self.ed_logs.setText(dn)

    def start_watchdog(self):
        cmd = self.ed_watchdog_cmd.text().strip()
        if not cmd:
            QMessageBox.warning(self, "Need command", "watchdog_cmd가 비어 있습니다.\n원하면 watchdog 실행 커맨드를 붙여 넣으세요.")
            return
        if self._watchdog_proc and self._watchdog_proc.poll() is None:
            QMessageBox.information(self, "Already running", "watchdog가 이미 실행 중입니다.")
            return

        try:
            # 콘솔창에서 실행되는 것을 전제로 함. (로그는 watchdog가 파일로 남김)
            self._watchdog_proc = subprocess.Popen(cmd, shell=True)
            self.lb_watchdog_state.setText(f"watchdog: running (pid={self._watchdog_proc.pid})")
        except Exception as e:
            QMessageBox.critical(self, "Start failed", str(e))

    def stop_watchdog(self):
        if not self._watchdog_proc or self._watchdog_proc.poll() is not None:
            self.lb_watchdog_state.setText("watchdog: idle")
            return
        try:
            self._watchdog_proc.terminate()
            self.lb_watchdog_state.setText("watchdog: terminating...")
        except Exception:
            try:
                self._watchdog_proc.kill()
            except Exception:
                pass
            self.lb_watchdog_state.setText("watchdog: killed")

    def refresh_all(self):
        status_path = Path(self.ed_status.text().strip())
        logs_dir = Path(self.ed_logs.text().strip())

        st = _read_json(status_path) or {}

        step = st.get("step", "-")
        hb = st.get("heartbeat_at", "")
        prog = st.get("progress", {}) or {}
        last_err = st.get("last_error", None)

        self.lb_step.setText(str(step))
        self.lb_hb.setText(str(hb) if hb else "-")
        self.lb_day.setText(str(prog.get("current_day", "-")))
        self.lb_done.setText(f"{prog.get('done_days', 0)}/{prog.get('total_days', 0)}")
        self.lb_last.setText(str(prog.get("last_result", "-")))
        self.lb_err.setText(str(last_err) if last_err else "-")

        # hb age
        hb_dt = _parse_iso_dt(hb) if hb else None
        age_sec = None
        if hb_dt:
            try:
                age_sec = (datetime.now().astimezone() - hb_dt).total_seconds()
            except Exception:
                age_sec = None

        if age_sec is None:
            self.lb_hb_age.setText("-")
            self.lb_hb_age.setStyleSheet("")
        else:
            self.lb_hb_age.setText(f"{age_sec:.1f}")
            # 색상 경고
            if age_sec > self.heartbeat_timeout_sec:
                self.lb_hb_age.setStyleSheet("color: white; background-color: #b00020; padding: 2px;")
            elif age_sec > self.heartbeat_timeout_sec * 0.6:
                self.lb_hb_age.setStyleSheet("color: black; background-color: #ffd54f; padding: 2px;")
            else:
                self.lb_hb_age.setStyleSheet("")

        # watchdog state text
        if self._watchdog_proc and self._watchdog_proc.poll() is None:
            self.lb_watchdog_state.setText(f"watchdog: running (pid={self._watchdog_proc.pid})")
        elif self._watchdog_proc:
            self.lb_watchdog_state.setText(f"watchdog: exited (rc={self._watchdog_proc.poll()})")
        else:
            self.lb_watchdog_state.setText("watchdog: idle")

        # logs (newest)
        stderr_p = _latest_log(logs_dir, "stderr_") if logs_dir.exists() else None
        stdout_p = _latest_log(logs_dir, "stdout_") if logs_dir.exists() else None

        if stderr_p:
            self.tx_stderr.setPlainText(_tail_text(stderr_p))
        else:
            self.tx_stderr.setPlainText("(no stderr log found)")

        if stdout_p:
            self.tx_stdout.setPlainText(_tail_text(stdout_p))
        else:
            self.tx_stdout.setPlainText("(no stdout log found)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status_json", default="results/ops/status/kiwoom_flow_job.json")
    ap.add_argument("--logs_dir", default="results/ops/logs")
    ap.add_argument("--heartbeat_timeout_sec", type=int, default=120)
    args = ap.parse_args()

    app = QApplication(sys.argv)
    gui = MonitorGUI(Path(args.status_json), Path(args.logs_dir), args.heartbeat_timeout_sec)
    gui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
