import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QScrollArea, QFrame, QTabWidget,
                             QGroupBox, QLineEdit, QPushButton, QFormLayout, QSplitter)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont

# Matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
try:
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
except:
    NavigationToolbar = None
from matplotlib.figure import Figure
import matplotlib.dates as mdates

# Project Paths
PROJECT_ROOT = Path("c:/garam/garam")
sys.path.append(str(PROJECT_ROOT))
from scripts.run_weighted_sim import WeightedSimEngine

DATA_ROOT = PROJECT_ROOT / "GARAM_Data/kr/intraday/1m"
PORTFOLIO_PATH = PROJECT_ROOT / "portfolio_state.json"
KOSPI_PATH = PROJECT_ROOT / "GARAM_Data/kr/index/kospi_dashboard.csv"

# --- Sparkline & PositionCard (Existing) ---
class SparklineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 60)
        self.figure = Figure(figsize=(1.2, 0.6), dpi=100)
        self.figure.patch.set_alpha(0)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color:transparent;")
        self.ax = self.figure.add_axes([0, 0, 1, 1])
        self.ax.axis('off')
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def update_data(self, prices):
        self.ax.clear()
        self.ax.axis('off')
        if len(prices) > 1:
            color = 'red' if prices[-1] < prices[0] else 'green'
            self.ax.plot(prices, color=color, linewidth=1.5)
            self.ax.fill_between(range(len(prices)), prices, min(prices), color=color, alpha=0.1)
        self.canvas.draw()

class PositionCard(QFrame):
    def __init__(self, symbol, data, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("QFrame { background-color: #333; border-radius: 5px; margin: 2px; } QLabel { color: white; }")
        self.setFixedHeight(80)
        layout = QHBoxLayout()
        self.lbl_info = QLabel(f"{symbol}")
        self.lbl_info.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        self.lbl_stats = QLabel("Loading...")
        self.lbl_stats.setStyleSheet("font-size: 14px;")
        self.sparkline = SparklineWidget()
        layout.addWidget(self.lbl_info)
        layout.addStretch()
        layout.addWidget(self.lbl_stats)
        layout.addWidget(self.sparkline)
        self.setLayout(layout)
        
    def update_state(self, current_price, avg_price, target_price=0):
        if avg_price > 0:
            pnl_pct = ((current_price - avg_price) / avg_price) * 100
        else:
            pnl_pct = 0.0
        color = "#ff4444" if pnl_pct < 0 else "#00C851"
        target_str = f" / 🎯 {target_price:,.0f}" if target_price > 0 else ""
        self.lbl_stats.setText(f"현재: {current_price:,.0f} ({pnl_pct:+.2f}%)\n평단: {avg_price:,.0f}{target_str}")
        self.lbl_stats.setStyleSheet(f"font-size: 14px; font-family: Consolas; color: {color}; border: none;")

# --- Live Monitor Tab ---
class LiveMonitorTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Chart
        chart_box = QFrame()
        chart_box.setStyleSheet("background-color: #2b2b2b; border-radius: 5px;")
        chart_layout = QVBoxLayout(chart_box)
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.figure.patch.set_facecolor('#2b2b2b')
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#2b2b2b')
        chart_layout.addWidget(QLabel("💰 Equity Curve (Live Session)"))
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_box, stretch=1)
        
        # Positions
        list_label = QLabel("📝 Active Positions")
        list_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(list_label)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll, stretch=2)
        
        self.equity_history = []
        self.timestamps = []
        self.position_widgets = {}

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system)
        self.timer.start(1000)

    def update_system(self):
        try:
            if not PORTFOLIO_PATH.exists(): return
            with open(PORTFOLIO_PATH, 'r', encoding='utf-8') as f:
                state = json.load(f)
            equity = state.get('equity', 0)
            now = datetime.now()
            self.equity_history.append(equity)
            self.timestamps.append(now)
            if len(self.equity_history) > 3600:
                self.equity_history.pop(0)
                self.timestamps.pop(0)
            self._update_chart()
            self._update_list(state.get('positions', {}))
        except Exception as e:
            print(f"Update error: {e}")

    def _update_chart(self):
        self.ax.clear()
        self.ax.plot(self.timestamps, self.equity_history, color='#00C851', linewidth=2)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.grid(True, color='#444', linestyle='--')
        self.ax.tick_params(colors='#888')
        self.canvas.draw()
        
    def _update_list(self, positions):
        for symbol, data in positions.items():
            if symbol not in self.position_widgets:
                card = PositionCard(symbol, data)
                self.scroll_layout.addWidget(card)
                self.position_widgets[symbol] = card
            card = self.position_widgets[symbol]
            current_price = self._get_current_price(symbol, data.get('avg_price', 0))
            card.update_state(current_price, data.get('avg_price', 0), data.get('target_price', 0))
            card.sparkline.update_data(self._get_recent_history(symbol))
            
        # Cleanup
        active = set(positions.keys())
        current = set(self.position_widgets.keys())
        for sym in current - active:
            w = self.position_widgets.pop(sym)
            w.deleteLater()

    def _get_current_price(self, symbol, fallback):
        try:
            csv_path = DATA_ROOT / f"{symbol}_1m.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                if not df.empty: return df['close'].iloc[0] # assuming sorted desc
        except: pass
        return fallback

    def _get_recent_history(self, symbol):
        try:
            csv_path = DATA_ROOT / f"{symbol}_1m.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                head = df.head(60)
                prices = head['close'].tolist()
                prices.reverse()
                return prices
        except: pass
        return []

# --- Strategy Lab Tab ---
class SimThread(QThread):
    finished = pyqtSignal(list, str) # history list, slot_id
    
    def __init__(self, slot_id, wa, wb, wc, wd, ws, ts, turbo, buffer):
        super().__init__()
        self.slot_id = slot_id
        self.wa = wa
        self.wb = wb
        self.wc = wc
        self.wd = wd
        self.ws = ws
        self.ts = ts
        self.turbo = turbo
        self.buffer = buffer

    def run(self):
        eng = WeightedSimEngine(self.wa, self.wb, self.wc, self.wd, self.ws, self.ts, self.turbo, self.buffer)
        start = "2024-01-02"
        # end = datetime.now().strftime("%Y-%m-%d") # Use full data
        end = "2025-12-31" # Force 2-Year range if data exists
        res = eng.run(start, end)
        self.finished.emit(res, self.slot_id)

class SimControlWidget(QGroupBox):
    run_clicked = pyqtSignal(str, float, float, float, float, float, float, float, float) # id, wa, wb, wc, wd, ws, ts, turbo, buffer
    
    def __init__(self, slot_id, title, color):
        super().__init__(title)
        self.slot_id = slot_id
        self.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {color}; border: 1px solid {color}; margin-top: 10px; }} QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; }}")
        
        layout = QFormLayout()
        self.inp_wa = QLineEdit("1.0")
        self.inp_wb = QLineEdit("0.0")
        self.inp_wa = QLineEdit("1.0")
        self.inp_wb = QLineEdit("0.0")
        self.inp_wc = QLineEdit("0.0")
        self.inp_wd = QLineEdit("0.0")
        self.inp_ws = QLineEdit("0.0")
        self.inp_ts = QLineEdit("0.0")
        self.inp_turbo = QLineEdit("1.0")
        self.inp_buffer = QLineEdit("8.0")
        self.btn_run = QPushButton("RUN")
        self.btn_run.setStyleSheet(f"background-color: {color}; color: black; font-weight: bold;")
        self.btn_run.clicked.connect(self.on_run)
        
        layout.addRow("Trend (Wa):", self.inp_wa)
        layout.addRow("Revert (Wb):", self.inp_wb)
        layout.addRow("Fear (Wc):", self.inp_wc)
        layout.addRow("Hero (Wd):", self.inp_wd)
        layout.addRow("Sense (Ws):", self.inp_ws)
        layout.addRow("TurboSense(Ts):", self.inp_ts)
        layout.addRow("Turbo (x):", self.inp_turbo)
        layout.addRow("Hold (Buffer):", self.inp_buffer)
        layout.addWidget(self.btn_run)
        self.setLayout(layout)

    def on_run(self):
        try:
            wa = float(self.inp_wa.text())
            wb = float(self.inp_wb.text())
            wc = float(self.inp_wc.text())
            wd = float(self.inp_wd.text())
            ws = float(self.inp_ws.text())
            ts = float(self.inp_ts.text())
            turbo = float(self.inp_turbo.text())
            buffer = float(self.inp_buffer.text())
            self.run_clicked.emit(self.slot_id, wa, wb, wc, wd, ws, ts, turbo, buffer)
        except:
            print("Invalid Input")

    def trigger_run(self):
        self.on_run()

    def set_busy(self, is_busy):
        if is_busy:
            self.btn_run.setText("⏳ Waiting...")
            self.btn_run.setEnabled(False)
        else:
            self.btn_run.setText("RUN")
            self.btn_run.setEnabled(True)

class StrategyLabTab(QWidget):
    def __init__(self):
        super().__init__()
        # Main Layout: Horizontal (Graph Left | Slots Right)
        main_layout = QHBoxLayout(self)
        
        # --- LEFT PANEL: Graph & Zoom ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0,0,0,0)
        
        # 1. Zoom Controls
        zoom_layout = QHBoxLayout()
        for label, days in [("2Y", 730), ("1Y", 365), ("6M", 180), ("3M", 90), ("1M", 30), ("1W", 7)]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, d=days: self.set_zoom(d))
            zoom_layout.addWidget(btn)
        
        # Run All Button
        btn_all = QPushButton("🚀 RUN ALL")
        btn_all.setStyleSheet("background-color: #FF9800; color: black; font-weight: bold; padding: 5px;")
        btn_all.clicked.connect(self.run_all_sims)
        zoom_layout.addWidget(btn_all)
        
        left_layout.addLayout(zoom_layout)

        # 2. Main Graph
        self.figure = Figure(figsize=(8, 5))
        self.figure.patch.set_facecolor('#1e1e1e')
        # Tighter layout for "Full" look
        self.figure.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1e1e1e')
        
        if NavigationToolbar:
            left_layout.addWidget(NavigationToolbar(self.canvas, self))
        left_layout.addWidget(self.canvas)
        
        main_layout.addWidget(left_panel, stretch=4) # Graph takes 4/5 width
        
        # --- RIGHT PANEL: Slots ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0,0,0,0)
        
        right_header = QLabel("⚙️ Strategy Slots")
        right_header.setAlignment(Qt.AlignCenter)
        right_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #AAA; margin-bottom: 5px;")
        right_layout.addWidget(right_header)
        
        self.slots = {}
        colors = {'A': '#FF5555', 'B': '#55FF55', 'C': '#5555FF'}
        
        for pid in ['A', 'B', 'C']:
            w = SimControlWidget(pid, f"Slot {pid}", colors[pid])
            # Set Diamond Ratio Defaults
            # Slot A: Conservative Turbo (Ts=2.0)
            if pid == 'A':
                w.inp_wa.setText("2.2")
                w.inp_wb.setText("1.8")
                w.inp_wc.setText("2.7")
                w.inp_wd.setText("3.5") 
                w.inp_ts.setText("2.0") 
                w.inp_turbo.setText("1.0") 
                w.inp_buffer.setText("8.0")
            # Slot B: Base Benchmark (Turbo=0)
            elif pid == 'B': 
                w.inp_wa.setText("2.0")
                w.inp_wb.setText("1.5")
                w.inp_wc.setText("1.7") 
                w.inp_wd.setText("3.0") 
                w.inp_ts.setText("0.0") 
                w.inp_turbo.setText("0.0") # Base 1.0 Only
                w.inp_buffer.setText("8.0") 
            # Slot C: Aggressive Turbo (Ts=-2.0)
            elif pid == 'C': 
                w.inp_wa.setText("2.2")
                w.inp_wb.setText("1.8")
                w.inp_wc.setText("2.7")
                w.inp_wd.setText("3.5")
                w.inp_ts.setText("-2.0") 
                w.inp_turbo.setText("1.0")
                w.inp_buffer.setText("6.0")
            
            w.run_clicked.connect(self.start_sim)
            right_layout.addWidget(w)
            self.slots[pid] = {'active': False, 'data': [], 'color': colors[pid], 'widget': w}
            
        right_layout.addStretch() # Push slots to top
        main_layout.addWidget(right_panel, stretch=1) # Slots take 1/5 width
        
        # Load KOSPI
        self.kospi_data = []
        self.load_kospi()
        
        # Initial Plot
        self.draw_graph()
        
        # Load KOSPI
        self.kospi_data = []
        self.load_kospi()
        
        # Initial Plot
        self.draw_graph()

    def load_kospi(self):
        if KOSPI_PATH.exists():
            df = pd.read_csv(KOSPI_PATH)
            df['date'] = pd.to_datetime(df['date'])
            # Normalize to 100m start roughly? Or just plot raw on twinx?
            # Let's Normalize to 100,000,000 for apple-to-apple comparison if possible.
            # Assuming sim starts at 100M.
            if not df.empty:
                start_val = df['close'].iloc[0]
                df['equity'] = (df['close'] / start_val) * 100_000_000
                self.kospi_data = df.to_dict('records')

    def start_sim(self, slot_id, wa, wb, wc, wd, ws, ts, turbo, buffer):
        print(f"Starting Sim {slot_id}: {wa}, {wb}, {wc}, {wd}, {ws}, {ts}, {turbo}, {buffer}")
        if 'widget' in self.slots[slot_id]:
            self.slots[slot_id]['widget'].set_busy(True)
            
        thread = SimThread(slot_id, wa, wb, wc, wd, ws, ts, turbo, buffer)
        thread.finished.connect(self.on_sim_finished)
        # Keep reference to avoid GC
        self.slots[slot_id]['thread'] = thread 
        thread.start()

    def on_sim_finished(self, history, slot_id):
        print(f"Sim {slot_id} Finished: {len(history)} days")
        if 'widget' in self.slots[slot_id]:
            self.slots[slot_id]['widget'].set_busy(False)

        self.slots[slot_id]['data'] = history
        self.draw_graph()

    def draw_graph(self, days=None):
        self.ax.clear()
        self.ax.grid(True, color='#333', linestyle='--')
        
        # KOSPI (Benchmark)
        if self.kospi_data:
            dates = [d['date'] for d in self.kospi_data]
            vals = [d['equity'] for d in self.kospi_data]
            self.ax.plot(dates, vals, color='#666666', linestyle='--', label='KOSPI', linewidth=1)
            
        # Slots
        for pid, info in self.slots.items():
            if info['data']:
                df = pd.DataFrame(info['data'])
                df['date'] = pd.to_datetime(df['date'])
                self.ax.plot(df['date'], df['equity'], color=info['color'], label=f"Slot {pid}", linewidth=2)
                
        self.ax.legend()
        self.ax.tick_params(colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        
        if days:
            end = datetime.now()
            start = end - timedelta(days=days)
            self.ax.set_xlim(pd.Timestamp(start), pd.Timestamp(end))
            
        self.canvas.draw()

    def set_zoom(self, days):
        self.draw_graph(days)

    def run_all_sims(self):
        for pid, info in self.slots.items():
            if 'widget' in info:
                info['widget'].trigger_run()

# --- Main Window ---
class MonitorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Garam Interactive Dashboard")
        self.setGeometry(100, 100, 1200, 900)
        self.setStyleSheet("QMainWindow { background-color: #1e1e1e; } QLabel { color: white; } QLineEdit { background: #333; color: white; }")
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #333; color: #AAA; padding: 10px; }
            QTabBar::tab:selected { background: #555; color: white; }
        """)
        
        self.tab_live = LiveMonitorTab()
        self.tab_lab = StrategyLabTab()
        
        self.tabs.addTab(self.tab_live, "Live Monitor")
        self.tabs.addTab(self.tab_lab, "연구소")
        
        self.setCentralWidget(self.tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MonitorWindow()
    window.show()
    sys.exit(app.exec_())
