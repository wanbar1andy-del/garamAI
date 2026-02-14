# scripts/ops/status_dashboard.py
# -*- coding: utf-8 -*-
import sys
import json
import argparse
from typing import Optional
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QFileDialog, QPushButton, QGroupBox, QGridLayout
)
from PyQt5.QtCore import QTimer, Qt

import pandas as pd
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
try:
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
except ImportError:
    NavigationToolbar = None

# Matplotlib Korean Font Support (Windows)
# plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

import logging
logging.basicConfig(filename='dashboard_debug.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s', force=True)

def log_debug(msg):
    logging.debug(msg)

def log_error(msg):
    logging.error(msg)


def _read_json(path: Path):
    if not path.exists():
        log_error(f"status_json not found: {path.absolute()}")
        return None, f"status_json not found: {path.as_posix()}"
    try:
        # BOM 안전 처리
        txt = path.read_text(encoding="utf-8-sig")
        d = json.loads(txt)
        log_debug(f"Read OK: {path} step={d.get('step')}")
        return d, None
    except Exception as e:
        log_error(f"Read Error on {path}: {e}")
        return None, f"status_json read error: {e}"


def _parse_iso(dt_str: str):
    # 기대 포맷: 2025-12-29T10:37:00+09:00 (collector가 isoformat으로 기록)
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None


def _now_local():
    # 로컬 타임존 기준(Windows KST 가정)
    return datetime.now().astimezone()


def _tail_text(path: Path, max_lines: int = 200):
    if not path.exists():
        return f"(log not found) {path.as_posix()}"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        if len(lines) <= max_lines:
            return "\n".join(lines)
        return "\n".join(lines[-max_lines:])
    except Exception as e:
        return f"(log read error) {e}"


def _latest_log(log_dir: Path, pattern: str):
    if not log_dir.exists():
        return None
    files = list(log_dir.glob(pattern))
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


class PlotContainer(QWidget):
    def __init__(self, fig, parent_layout):
        super().__init__()
        self._parent_layout = parent_layout
        self._is_floating = False
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Canvas
        self.canvas = FigureCanvas(fig)
        
        # Toolbar
        self.toolbar = None
        if NavigationToolbar:
            self.toolbar = NavigationToolbar(self.canvas, self)
            
        # Header (Restore Button - only visible when floating)
        self.header = QWidget()
        hbox = QHBoxLayout(self.header)
        hbox.setContentsMargins(5, 5, 5, 5)
        self.btn_restore = QPushButton("화면 복귀 (Restore)")
        self.btn_restore.clicked.connect(self.dock_in)
        hbox.addStretch(1)
        hbox.addWidget(self.btn_restore)
        
        self.layout.addWidget(self.header, 0)
        if self.toolbar:
            self.layout.addWidget(self.toolbar, 0)
        # Give canvas stretch priority 1 to fill remaining space
        self.layout.addWidget(self.canvas, 1)
        
        self.header.hide()

    def pop_out(self):
        if self._is_floating:
            return
        self.setParent(None)
        self.setWindowFlags(Qt.Window)
        self.header.show()
        self.showFullScreen()
        self._is_floating = True

    def dock_in(self):
        if not self._is_floating:
            return
        self.setWindowFlags(Qt.Widget)
        self.header.hide()
        self._parent_layout.addWidget(self)
        self.show()
        self._is_floating = False
    
    def keyPressEvent(self, event):
        # ESC to restore
        if self._is_floating and event.key() == Qt.Key_Escape:
            self.dock_in()
        else:
            super().keyPressEvent(event)


class Dashboard(QWidget):
    def __init__(self, status_json: Path, log_dir: Path, flow_metrics_csv: Optional[Path],
                 refresh_ms: int, timeout_sec: int, tail_lines: int):
        super().__init__()

        self.status_json = status_json
        self.log_dir = log_dir
        self.flow_metrics_csv = flow_metrics_csv
        self.refresh_ms = refresh_ms
        self.timeout_sec = timeout_sec
        self.tail_lines = tail_lines

        self._last_status_mtime = None
        self._last_flow_mtime = None
        self._flow_df = None

        self.setWindowTitle("AntiGravity Ops Dashboard (Kiwoom) — SSOT Monitor")
        self.resize(1200, 760)

        # ===== Header controls
        self.btn_pick_status = QPushButton("status_json 변경…")
        self.btn_pick_status.clicked.connect(self.pick_status_json)

        self.btn_pick_flow = QPushButton("flow_metrics_csv 변경…")
        self.btn_pick_flow.clicked.connect(self.pick_flow_csv)

        self.lbl_paths = QLabel()
        self.lbl_paths.setTextInteractionFlags(Qt.TextSelectableByMouse)

        header = QHBoxLayout()
        header.addWidget(self.btn_pick_status)
        header.addWidget(self.btn_pick_flow)
        
        # Fullscreen Button in Header
        self.btn_fs = QPushButton("🔍 그래프 전체화면 (Zoom)")
        # We need self.plot_container initialized first, so we'll connect later or init logic order change
        # Let's initialize btn_fs here but connect later
        header.addWidget(self.btn_fs)
        
        header.addStretch(1)

        # ===== Status box
        box_status = QGroupBox("Status JSON (SSOT)")
        grid = QGridLayout()

        self.v_step = QLabel("-")
        self.v_hb = QLabel("-")
        self.v_hb_age = QLabel("-")
        self.v_progress = QLabel("-")
        self.v_last = QLabel("-")
        self.v_error = QLabel("-")

        for w in (self.v_step, self.v_hb, self.v_hb_age, self.v_progress, self.v_last, self.v_error):
            w.setTextInteractionFlags(Qt.TextSelectableByMouse)

        grid.addWidget(QLabel("step"), 0, 0); grid.addWidget(self.v_step, 0, 1)
        grid.addWidget(QLabel("heartbeat_at"), 1, 0); grid.addWidget(self.v_hb, 1, 1)
        grid.addWidget(QLabel("heartbeat_age_sec"), 2, 0); grid.addWidget(self.v_hb_age, 2, 1)
        grid.addWidget(QLabel("progress"), 3, 0); grid.addWidget(self.v_progress, 3, 1)
        grid.addWidget(QLabel("last_result"), 4, 0); grid.addWidget(self.v_last, 4, 1)
        grid.addWidget(QLabel("last_error"), 5, 0); grid.addWidget(self.v_error, 5, 1)

        box_status.setLayout(grid)

        # ===== Log box
        box_log = QGroupBox("stderr tail (사후감사 SSOT)")
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        vlog = QVBoxLayout()
        vlog.addWidget(self.log_view)
        box_log.setLayout(vlog)

        # ===== Flow plot
        box_flow = QGroupBox("Flow Z-Score (Program/Investor) Plot")
        self.fig = plt.Figure()
        vflow = QVBoxLayout()
        # Plot Container (Canvas + Toolbar + Logic)
        self.plot_container = PlotContainer(self.fig, vflow)
        vflow.addWidget(self.plot_container)
        box_flow.setLayout(vflow)

        # ===== Layout
        left = QVBoxLayout()
        left.addLayout(header)
        left.addWidget(self.lbl_paths)
        left.addWidget(box_status, 0)

        # Connect Fullscreen Button (now that plot_container exists)
        self.btn_fs.clicked.connect(self.plot_container.pop_out)

        right = QVBoxLayout()
        right.addWidget(box_flow, 3)
        right.addWidget(box_log, 2)

        main = QHBoxLayout()
        main.addLayout(left, 2)
        main.addLayout(right, 3)

        root = QVBoxLayout()
        root.addLayout(main)
        self.setLayout(root)

        self._refresh_paths_label()

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(self.refresh_ms)

        # initial
        self.refresh(force=True)

    def _refresh_paths_label(self):
        flow = self.flow_metrics_csv.as_posix() if self.flow_metrics_csv else "(none)"
        self.lbl_paths.setText(
            f"status_json: {self.status_json.as_posix()}\n"
            f"log_dir   : {self.log_dir.as_posix()}\n"
            f"flow_csv  : {flow}\n"
            f"refresh_ms={self.refresh_ms} timeout_sec={self.timeout_sec} tail_lines={self.tail_lines}"
        )

    def pick_status_json(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Select status_json", "", "JSON (*.json);;All (*.*)")
        if fn:
            self.status_json = Path(fn)
            self._last_status_mtime = None
            self._refresh_paths_label()
            self.refresh(force=True)

    def pick_flow_csv(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Select flow_metrics_csv", "", "CSV (*.csv);;All (*.*)")
        if fn:
            self.flow_metrics_csv = Path(fn)
            self._last_flow_mtime = None
            self._flow_df = None
            self._refresh_paths_label()
            self.refresh(force=True)

    def refresh(self, force: bool = False):
        self._refresh_status(force=force)
        self._refresh_log(force=force)
        self._refresh_flow_plot(force=force)

    def _refresh_status(self, force: bool = False):
        try:
            mtime = self.status_json.stat().st_mtime if self.status_json.exists() else None
        except Exception:
            mtime = None

        if (not force) and (mtime is not None) and (self._last_status_mtime == mtime):
            # 변경 없음
            return

        self._last_status_mtime = mtime

        st, err = _read_json(self.status_json)
        if err:
            self.v_step.setText("NA")
            self.v_error.setText(err)
            self.v_hb.setText("-")
            self.v_hb_age.setText("-")
            self.v_progress.setText("-")
            self.v_last.setText("-")
            self._set_health(bad=True)
            return

        step = (st or {}).get("step", "NA")
        hb = (st or {}).get("heartbeat_at")
        prog = (st or {}).get("progress", {})
        last_res = (prog or {}).get("last_result")
        last_err = (st or {}).get("last_error")

        self.v_step.setText(str(step))
        self.v_hb.setText(str(hb) if hb else "-")
        self.v_progress.setText(json.dumps(prog, ensure_ascii=False))
        self.v_last.setText(json.dumps(last_res, ensure_ascii=False) if last_res else "-")
        self.v_error.setText(str(last_err) if last_err else "-")

        # Heartbeat age
        bad = False
        age_sec = None
        if hb:
            dt = _parse_iso(str(hb))
            if dt:
                age_sec = int((_now_local() - dt).total_seconds())
        if age_sec is None:
            self.v_hb_age.setText("NA")
            bad = True
        else:
            self.v_hb_age.setText(str(age_sec))
            if age_sec > self.timeout_sec:
                bad = True

        # step 기반 상태 색
        if str(step) in ("FAILED",):
            bad = True

        self._set_health(bad=bad)

    def _set_health(self, bad: bool):
        # 운영자에게 즉시 시그널(배경색만 약하게)
        if bad:
            self.setStyleSheet("QWidget { background-color: #2b1d1d; } QLabel { color: #ffffff; }")
        else:
            self.setStyleSheet("QWidget { background-color: #1d2b1d; } QLabel { color: #ffffff; }")

    def _refresh_log(self, force: bool = False):
        # 최신 stderr 로그 tail
        p = _latest_log(self.log_dir, "stderr_*.log")
        if p is None:
            self.log_view.setPlainText(f"(no stderr log) {self.log_dir.as_posix()}")
            return

        # 너무 자주 전체 리로드하지 않기 위해 mtime 체크
        try:
            mtime = p.stat().st_mtime
        except Exception:
            mtime = None

        key = (p.as_posix(), mtime)
        if (not force) and hasattr(self, "_last_log_key") and self._last_log_key == key:
            return
        self._last_log_key = key

        self.log_view.setPlainText(_tail_text(p, self.tail_lines))

    def _load_flow_df_if_needed(self):
        if not self.flow_metrics_csv:
            return None
        if not self.flow_metrics_csv.exists():
            return None

        try:
            mtime = self.flow_metrics_csv.stat().st_mtime
        except Exception:
            mtime = None

        if self._flow_df is not None and (mtime is not None) and (self._last_flow_mtime == mtime):
            return self._flow_df

        # ===== reload (BOM 안전 + 컬럼명 클린) =====
        try:
            df = pd.read_csv(self.flow_metrics_csv, encoding="utf-8-sig")
        except Exception:
            return None

        # 컬럼명: BOM/공백 제거
        df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]

        # date 컬럼 정규화
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        elif "일자" in df.columns:
            df["date"] = pd.to_datetime(df["일자"].astype(str), format="%Y%m%d", errors="coerce")
        else:
            # 최후의 수단: 첫 번째 컬럼을 date로 가정
            c0 = df.columns[0] if len(df.columns) > 0 else None
            if c0 is None:
                return None
            df["date"] = pd.to_datetime(df[c0], errors="coerce")

        df = df.dropna(subset=["date"]).sort_values("date")

        # ===== 플롯 컬럼 자동 탐지 =====
        # 우선순위: 정확히 z_score -> z 포함 -> 수치형 컬럼
        z_cols = []
        if "z_score" in df.columns:
            z_cols = ["z_score"]
        else:
            # 'z' 들어간 컬럼들(외국인_z, 기관_z, z_foreigner 등)
            z_cols = [c for c in df.columns if c != "date" and ("z" in c.lower())]

        # 그래도 없으면 수치형 컬럼 후보(원시 flow_amt 같은 걸 그릴 수도 있으니 운영자가 확인)
        if not z_cols:
            cand = [c for c in df.columns if c != "date"]
            # 숫자로 변환 가능한 컬럼만 남김
            tmp = df[cand].apply(lambda s: pd.to_numeric(s, errors="coerce"))
            z_cols = [c for c in tmp.columns if tmp[c].notna().sum() > 0]

        if not z_cols:
            # 그릴 게 없음
            self._flow_df = None
            self._last_flow_mtime = mtime
            self._flow_cols = []
            return None

        # 숫자 변환
        for c in z_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        # 전부 NaN이면 제외
        df = df.dropna(subset=z_cols, how="all")
        if df.empty:
            self._flow_df = None
            self._last_flow_mtime = mtime
            self._flow_cols = z_cols
            return None

        self._flow_df = df
        self._flow_cols = z_cols
        self._last_flow_mtime = mtime
        return df

    def _refresh_flow_plot(self, force: bool = False):
        df = self._load_flow_df_if_needed()
        self.fig.clear()

        ax = self.fig.add_subplot(111)
        ax.set_title("Investor Flow Z-Scores (Foreigner/Inst/Pension)")

        # Canvas draw call via container
        # Note: self.canvas is now inside self.plot_container
        canvas = self.plot_container.canvas 

        if df is None or df.empty:
            ax.text(
                0.05, 0.5,
                "flow_metrics_csv not loaded / empty\n"
                f"file={self.flow_metrics_csv.as_posix() if self.flow_metrics_csv else '(none)'}",
                transform=ax.transAxes
            )
            canvas.draw()
            return

        cols = getattr(self, "_flow_cols", [])
        if not cols:
            ax.text(0.05, 0.5, f"no plot columns found. columns={list(df.columns)}", transform=ax.transAxes)
            canvas.draw()
            return

        # 다중 라인 플롯 + legend
        for c in cols:
            ax.plot(df["date"], df[c], label=c)

        ax.axhline(1.0, linewidth=1, color='gray', linestyle='--')
        ax.axhline(-1.0, linewidth=1, color='gray', linestyle='--')

        ax.legend(loc="upper left", fontsize=8)
        ax.tick_params(axis="x", rotation=30)
        self.fig.tight_layout()
        canvas.draw()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status_json", required=True)
    ap.add_argument("--log_dir", default="results/ops/logs")
    ap.add_argument("--flow_metrics_csv", default="")
    ap.add_argument("--refresh_ms", type=int, default=1000)
    ap.add_argument("--timeout_sec", type=int, default=120)
    ap.add_argument("--tail_lines", type=int, default=200)
    args = ap.parse_args()

    flow = Path(args.flow_metrics_csv) if args.flow_metrics_csv.strip() else None

    app = QApplication(sys.argv)
    # Global High Contrast Dark Style
    app.setStyleSheet("""
        QWidget {
            background-color: #2b2b2b;
            color: #f0f0f0;
            font-size: 10pt;
        }
        QGroupBox {
            border: 1px solid #555555;
            margin-top: 20px;
            font-weight: bold;
            color: #40a0ff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QLabel {
            color: #f0f0f0;
        }
        QPushButton {
            background-color: #3d3d3d;
            border: 1px solid #555;
            padding: 5px;
            color: #ffffff;
        }
        QPushButton:hover {
            background-color: #4d4d4d;
        }
        QPlainTextEdit {
            background-color: #1e1e1e;
            color: #00ff00;
            font-family: Consolas, monospace;
            border: 1px solid #444;
        }
    """)
    w = Dashboard(
        status_json=Path(args.status_json),
        log_dir=Path(args.log_dir),
        flow_metrics_csv=flow,
        refresh_ms=args.refresh_ms,
        timeout_sec=args.timeout_sec,
        tail_lines=args.tail_lines,
    )
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
