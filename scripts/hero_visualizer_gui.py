"""
히어로 스캔 결과 시각화 GUI

기능:
- 히어로 스캔 CSV 로드
- 400개 종목 차트 (코스피 비교선 포함)
- 히어로 구간 색상 강조
- 수익 그래프 별도 표시
"""
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QComboBox, QListWidget,
    QSplitter, QGroupBox, QScrollArea, QMessageBox, QDateEdit, QCheckBox
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates


class HeroVisualizerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("가람 히어로 시각화 도구")
        self.setGeometry(100, 100, 1400, 900)
        
        # Data
        self.trade_df = None
        self.minute_data_dir = Path("GARAM_Data/history/minute")
        self.current_symbol = None
        
        self.init_ui()
        
    def load_trade_log(self):
        """매매 일지(체결 내역) 로드"""
        # Default path check
        default_dir = "GARAM_Data/orders"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "매매 일지 선택 (chejan_fills.csv 등)", default_dir, "CSV Files (*.csv)"
        )
        if not file_path:
            return
            
        try:
            self.trade_df = pd.read_csv(file_path)
            # Normalize Columns: Need 'code', 'type' (buy/sell), 'date', 'price', 'qty'
            # Assuming standard Garam format or Kiwoom format
            # Let's try to standardize
            
            # Convert code to 6 digit string
            if "code" in self.trade_df.columns:
                self.trade_df["code"] = self.trade_df["code"].astype(str).str.zfill(6)
            elif "종목코드" in self.trade_df.columns:
                self.trade_df["code"] = self.trade_df["code"].astype(str).str.replace("A", "").str.zfill(6)
                
            # Date/Time
            # If 'time' column exists (HHMMSS) and file has date context? Or 'date' column?
            # Ideally trade log has full datetime.
            
            # Refresh list to show icons
            self.populate_symbol_list()
            
            self.lbl_status.setText(f"매매 일지 로드 완료: {len(self.trade_df)} 건")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"매매 일지 로드 실패: {e}")
        
    def init_ui(self):
        """UI 초기화"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # === Top Control Panel ===
        control_panel = QGroupBox("제어 패널")
        control_layout = QHBoxLayout()
        
        btn_load_scan = QPushButton("📂 히어로 스캔 결과 열기")
        btn_load_scan.clicked.connect(self.load_hero_scan)
        btn_load_scan.setStyleSheet("font-size: 14px; padding: 8px;")
        
        btn_load_kospi = QPushButton("📈 코스피 데이터 열기")
        btn_load_kospi.clicked.connect(self.load_kospi_data)
        btn_load_kospi.setStyleSheet("font-size: 14px; padding: 8px;")
        
        self.lbl_status = QLabel("준비")
        self.lbl_status.setStyleSheet("font-size: 14px; color: green; font-weight: bold;")
        
        
        btn_load_trades = QPushButton("📝 매매 일지 열기")
        btn_load_trades.clicked.connect(self.load_trade_log)
        btn_load_trades.setStyleSheet("font-size: 14px; padding: 8px;")
        control_layout.addWidget(btn_load_trades)
        
        control_layout.addWidget(btn_load_scan)
        control_layout.addWidget(btn_load_kospi)
        control_layout.addStretch()
        control_layout.addWidget(QLabel("상태:"))
        control_layout.addWidget(self.lbl_status)
        control_panel.setLayout(control_layout)
        main_layout.addWidget(control_panel)
        
        # === Main Splitter (List | Charts) ===
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel: Symbol List
        left_panel = QGroupBox("종목 목록")
        left_layout = QVBoxLayout()
        
        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("필터:"))
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["전체", "히어로만", "비히어로만", "매매종목만", "놓친 히어로"])
        self.combo_filter.currentIndexChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.combo_filter)
        left_layout.addLayout(filter_layout)
        
        # Date Range Filter
        date_filter_box = QGroupBox("날짜 구간 검색")
        date_layout = QHBoxLayout()
        
        date_layout.addWidget(QLabel("시작:"))
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addDays(-5)) # Default: 5 days ago
        self.date_start.dateChanged.connect(self.refresh_chart)
        date_layout.addWidget(self.date_start)
        
        date_layout.addWidget(QLabel("종료:"))
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.dateChanged.connect(self.refresh_chart)
        date_layout.addWidget(self.date_end)
        
        btn_today = QPushButton("오늘 (실시간)")
        btn_today.clicked.connect(self.set_today_range)
        date_layout.addWidget(btn_today)
        
        date_filter_box.setLayout(date_layout)
        left_layout.addWidget(date_filter_box)
        
        # Real-time Auto Refresh Checkbox
        self.chk_auto_refresh = QCheckBox("실시간 자동 갱신 (3초)")
        self.chk_auto_refresh.stateChanged.connect(self.toggle_auto_refresh)
        left_layout.addWidget(self.chk_auto_refresh)
        
        # Symbol List
        self.list_symbols = QListWidget()
        self.list_symbols.itemClicked.connect(self.on_symbol_selected)
        self.list_symbols.setStyleSheet("font-size: 12px;")
        left_layout.addWidget(self.list_symbols)
        
        # Stats
        self.lbl_stats = QLabel("히어로: 0 / 전체: 0")
        self.lbl_stats.setStyleSheet("font-size: 12px; color: blue;")
        left_layout.addWidget(self.lbl_stats)
        
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(300)
        splitter.addWidget(left_panel)
        
        # Right Panel: Charts
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Symbol Info
        self.lbl_symbol_info = QLabel("종목을 선택하세요")
        self.lbl_symbol_info.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(self.lbl_symbol_info)
        
        # Price Chart
        chart_box = QGroupBox("가격 차트 (코스피 비교)")
        chart_layout = QVBoxLayout()
        self.figure_price = Figure(figsize=(10, 4))
        self.canvas_price = FigureCanvas(self.figure_price)
        self.ax_price = self.figure_price.add_subplot(111)
        chart_layout.addWidget(self.canvas_price)
        chart_box.setLayout(chart_layout)
        right_layout.addWidget(chart_box)
        
        # Return Chart
        return_box = QGroupBox("수익률 그래프")
        return_layout = QVBoxLayout()
        self.figure_return = Figure(figsize=(10, 3))
        self.canvas_return = FigureCanvas(self.figure_return)
        self.ax_return = self.figure_return.add_subplot(111)
        return_layout.addWidget(self.canvas_return)
        return_box.setLayout(return_layout)
        right_layout.addWidget(return_box)
        
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([300, 1100])
        main_layout.addWidget(splitter)
        
    def load_hero_scan(self):
        """히어로 스캔 결과 CSV 로드"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "히어로 스캔 결과 선택", "results", "CSV Files (*.csv)"
        )
        if not file_path:
            return
        
        try:
            self.hero_df = pd.read_csv(file_path)
            
            # Validate columns
            required = ["symbol", "is_hero"]
            if not all(c in self.hero_df.columns for c in required):
                QMessageBox.warning(self, "오류", f"필수 컬럼 누락: {required}")
                return
            
            self.hero_df["symbol"] = self.hero_df["symbol"].astype(str).str.zfill(6)
            
            # Populate list
            self.populate_symbol_list()
            
            heroes = (self.hero_df["is_hero"] == 1).sum()
            total = len(self.hero_df)
            self.lbl_status.setText(f"스캔 결과 로드 완료: {Path(file_path).name}")
            self.lbl_stats.setText(f"히어로: {heroes} / 전체: {total}")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"파일 로드 실패:\n{e}")
    
    def load_kospi_data(self):
        """코스피 일봉 데이터 로드"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "코스피 데이터 선택", "GARAM_Data", "CSV Files (*.csv)"
        )
        if not file_path:
            return
        
        try:
            self.kospi_df = pd.read_csv(file_path)
            
            # Normalize columns
            if "timestamp" in self.kospi_df.columns:
                self.kospi_df["date"] = self.kospi_df["timestamp"]
            
            self.kospi_df["date"] = pd.to_datetime(self.kospi_df["date"])
            
            # Normalize to 100 base
            if "close" in self.kospi_df.columns:
                start_val = self.kospi_df["close"].iloc[0]
                self.kospi_df["normalized"] = (self.kospi_df["close"] / start_val) * 100
            
            self.lbl_status.setText(f"코스피 데이터 로드 완료: {len(self.kospi_df)} 행")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"코스피 로드 실패:\n{e}")
    
    def populate_symbol_list(self):
        """종목 리스트 채우기"""
        self.list_symbols.clear()
        
        if self.hero_df is None:
            return
        
        for _, row in self.hero_df.iterrows():
            symbol = row["symbol"]
            is_hero = row.get("is_hero", 0)
            score = row.get("score", 0.0)
            is_traded = symbol in traded_symbols
            
            # Display Icon
            if is_traded:
                icon = "💰" # Traded
            elif is_hero == 1:
                icon = "💔" # Missed Hero
            else:
                icon = "  "
            
            prefix = "⭐" if is_hero == 1 else ""
            display = f"{icon}{prefix} {symbol} | Score: {score:.2f}"
            
            self.list_symbols.addItem(display)
    
    def apply_filter(self):
        """필터 적용"""
        if self.hero_df is None:
            return
        
        filter_type = self.combo_filter.currentText()
        traded_symbols = set()
        if self.trade_df is not None:
             traded_symbols = set(self.trade_df["code"].astype(str).str.zfill(6).unique())

        self.list_symbols.clear()
        
        for _, row in self.hero_df.iterrows():
            symbol = row["symbol"]
            is_hero = row.get("is_hero", 0)
            score = row.get("score", 0.0)
            is_traded = symbol in traded_symbols
            
            # Categories
            # 1. Traded Hero (💰)
            # 2. Missed Hero (💔) - Hero but not traded
            # 3. Traded Normal (💸) - Not hero but traded (maybe manual?)
            # 4. Normal ( )
            
            # Filter Logic
            if filter_type == "히어로만" and is_hero != 1:
                continue
            if filter_type == "매매종목만" and not is_traded:
                continue
            if filter_type == "놓친 히어로" and not (is_hero == 1 and not is_traded):
                continue
                
            # Display Icon
            if is_traded:
                icon = "💰" # Traded
            elif is_hero == 1:
                icon = "💔" # Missed Hero
            else:
                icon = "  "
            
            # Hero Star
            star = "⭐" if is_hero == 1 else ""
            
            display = f"{icon}{star} {symbol} | Score: {score:.2f}"
            self.list_symbols.addItem(display)
    
    def on_symbol_selected(self, item):
        """종목 선택 시"""
        text = item.text()
        # Extract symbol (6 digits)
        # Format: "💰⭐ 005930 | Score..."
        # Split by "|" first
        left_part = text.split("|")[0]
        # Remove known icons
        for icon in ["💰", "💔", "⭐", "💸"]:
            left_part = left_part.replace(icon, "")
        symbol = left_part.strip()
        
        self.current_symbol = symbol
        self.plot_symbol_chart(symbol)
    
    def set_today_range(self):
        """오늘 날짜로 설정 (장중 모니터링용)"""
        today = QDate.currentDate()
        self.date_start.setDate(today)
        self.date_end.setDate(today)
        self.refresh_chart()

    def toggle_auto_refresh(self, state):
        """실시간 자동 갱신 토글"""
        if state == Qt.Checked:
            self.refresh_timer = QTimer(self)
            self.refresh_timer.timeout.connect(self.refresh_chart)
            self.refresh_timer.start(3000) # 3 seconds
        else:
            if hasattr(self, 'refresh_timer'):
                self.refresh_timer.stop()
                
    def refresh_chart(self):
        """현재 선택된 종목 차트 갱신"""
        if self.current_symbol:
            self.plot_symbol_chart(self.current_symbol)
            
    def plot_symbol_chart(self, symbol):
        """종목 차트 그리기"""
        # Get hero info
        hero_row = self.hero_df[self.hero_df["symbol"] == symbol]
        if hero_row.empty:
            return
        
        is_hero = hero_row.iloc[0].get("is_hero", 0)
        score = hero_row.iloc[0].get("score", 0.0)
        rsi = hero_row.iloc[0].get("rsi", 0.0)
        
        self.lbl_symbol_info.setText(
            f"종목: {symbol} | 히어로: {'✓' if is_hero else '✗'} | "
            f"Score: {score:.2f} | RSI: {rsi:.1f}"
        )
        
        # Load minute data
        minute_path = self.minute_data_dir / f"{symbol}.csv"
        
        if not minute_path.exists():
            self.ax_price.clear()
            self.ax_price.text(
                0.5, 0.5, f"데이터 없음: {symbol}",
                ha="center", va="center", fontsize=14
            )
            self.canvas_price.draw()
            return
        
        try:
            df = pd.read_csv(minute_path)
            df = df.rename(columns={"체결시간": "date", "현재가": "close"})
            df["date"] = pd.to_datetime(df["date"], format="%Y%m%d%H%M%S", errors="coerce")
            df = df.dropna(subset=["date"])
            df = df.sort_values("date")
            
            # Filter by Date Range
            q_start = self.date_start.date().toPyDate()
            q_end = self.date_end.date().toPyDate()
            
            # Convert to datetime for comparison (start of day / end of day)
            dt_start = pd.Timestamp(q_start)
            dt_end = pd.Timestamp(q_end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            
            df = df[
                (df["date"] >= dt_start) & 
                (df["date"] <= dt_end)
            ]
            
            if df.empty:
                self.ax_price.clear()
                self.ax_price.text(0.5, 0.5, f"선택 구간 데이터 없음 ({q_start} ~ {q_end})", ha="center")
                self.canvas_price.draw()
                return

            # Normalize to 100
            df["normalized"] = (df["close"] / df["close"].iloc[0]) * 100
            
            # Plot Price Chart
            self.ax_price.clear()
            
            # 1. Base Line (Ghost Tail / Market Context) - Dotted Gray
            self.ax_price.plot(df["date"], df["normalized"], 
                              label=f"{symbol} (Ghost)", color="gray", linestyle=":", linewidth=1.5, alpha=0.6)
            
            # 2. Holding Periods (Active Strategy) - Solid Blue
            # Logic: Masking based on trades
            # Just plot segments where we had position?
            # Complex to reconstruct perfectly from simple CSV without active simulation.
            # Simplified approach: If we have trades, try to connect B to S.
            
            trade_segments = []
            active_ranges = []
            
            if self.trade_df is not None:
                sym_trades = self.trade_df[self.trade_df["code"] == symbol].copy()
                if not sym_trades.empty and "date" in sym_trades.columns:
                     sym_trades["dt"] = pd.to_datetime(sym_trades["date"].astype(str), format="%Y%m%d%H%M%S", errors='coerce')
                     sym_trades = sym_trades.sort_values("dt")
                     
                     # Simple FIFO/Netting simulation for coloring
                     current_pos = 0
                     seg_start = None
                     
                     for _, t in sym_trades.iterrows():
                         row_dt = t["dt"]
                         t_type = str(t.get("type", "")).lower()
                         # Heuristic quantity (if missing, assume 1)
                         qty = float(t.get("qty", 1))
                         
                         is_buy = "매수" in t_type or "buy" in t_type or t_type == "2"
                         is_sell = "매도" in t_type or "sell" in t_type or t_type == "1"
                         
                         if is_buy:
                             if current_pos == 0:
                                 seg_start = row_dt
                             current_pos += qty
                         elif is_sell:
                             current_pos -= qty
                             if current_pos <= 0:
                                 current_pos = 0 # reset
                                 if seg_start:
                                     active_ranges.append((seg_start, row_dt))
                                     seg_start = None
                     
                     # If still holding at end
                     if current_pos > 0 and seg_start:
                         active_ranges.append((seg_start, df["date"].max()))

            if active_ranges:
                for start, end in active_ranges:
                    mask = (df["date"] >= start) & (df["date"] <= end)
                    if mask.any():
                        self.ax_price.plot(df.loc[mask, "date"], df.loc[mask, "normalized"],
                                          color="blue", linewidth=2.5, alpha=1.0)
                # Label hack for legend
                self.ax_price.plot([], [], color="blue", linewidth=2.5, label="보유 구간")
            else:
                # If no trades found (or just watching), plotting whole line as solid if 'Hero' else Base
                # But requirement says "Ghost Tail" implies we show full history. 
                # If no trades, maybe just show Ghost? Or Solid if it's a Hero we missed?
                if is_hero == 1:
                     # Missed Hero -> Show as Orange dashed?
                     self.ax_price.plot(df["date"], df["normalized"], color="orange", linestyle="--", linewidth=1.5, alpha=0.8, label="놓친 히어로")
            
            
            # KOSPI overlay (Alpha Benchmark) - Gray Shading (Area)
            if self.kospi_df is not None:
                kospi_subset = self.kospi_df[
                    (self.kospi_df["date"] >= df["date"].min()) &
                    (self.kospi_df["date"] <= df["date"].max())
                ]
                if not kospi_subset.empty:
                    # Re-normalize Kospi to match start of this period
                    k_start = kospi_subset["close"].iloc[0]
                    kospi_norm = (kospi_subset["close"] / k_start) * 100
                    
                    # Fill Between for "Shadow" effect
                    self.ax_price.fill_between(
                        kospi_subset["date"], kospi_norm, 0,
                        color="gray", alpha=0.15, label="KOSPI (Benchmark)"
                    )
                    # Line on top
                    self.ax_price.plot(
                        kospi_subset["date"], kospi_norm,
                        color="gray", linestyle="-", linewidth=1.0, alpha=0.5
                    )
                    
                    # Set Y-lim to focus on price action, ignore 0 base of fill_between if needed
                    # Actually fill_between goes to 0 by default, which messes up scale if stock is at 100.
                    # Be smart: fill between min of chart? Or just fill under line?
                    # Let's fill between min(displayed price)*0.9
                    y_min, y_max = self.ax_price.get_ylim()
                    # We can't know ylim yet easily without rendering first.
                    # Improved trick: fill_between(..., y1=kospi_norm, y2=min_val)
                    # Just filling relative to its own min might look weird.
                    # Best visual: Fill between curve and bottom of chart.
                    
                    # Instead of 0, let's use a dynamic low. 
                    low_base = min(df["normalized"].min(), kospi_norm.min()) * 0.95
                    self.ax_price.collections.clear() # Clear previous fills if any
                    # Re-plot fill with base
                    self.ax_price.fill_between(
                        kospi_subset["date"], kospi_norm, low_base,
                        color="gray", alpha=0.15, label="KOSPI (Area)"
                    )

            # Hero period highlight
            if is_hero == 1:
                cutoff_idx = int(len(df) * 0.8)
                hero_period = df.iloc[cutoff_idx:]
                self.ax_price.axvspan(
                    hero_period["date"].min(), hero_period["date"].max(),
                    alpha=0.1, color="yellow", label="히어로 구간"
                )
            
            self.ax_price.set_title(f"{symbol} Tactical View (Ghost Tail)", fontsize=14, weight="bold")
            self.ax_price.set_xlabel("Time")
            self.ax_price.set_ylabel("Norm. Price (Start=100)")
            self.ax_price.legend(loc='upper left')
            self.ax_price.grid(True, alpha=0.3)
            self.ax_price.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H"))
            
            # --- Plot Trades (Buy/Sell Markers - SWAPPED COLORS) ---
            # User Instruction: Buy(B) - Blue, Sell(S) - Red
            if self.trade_df is not None:
                sym_trades = self.trade_df[self.trade_df["code"] == symbol].copy()
                if not sym_trades.empty:
                    if "date" in sym_trades.columns:
                         sym_trades["dt"] = pd.to_datetime(sym_trades["date"].astype(str), format="%Y%m%d%H%M%S", errors='coerce')
                    
                    if "dt" in sym_trades.columns:
                        chart_start = df["date"].min()
                        chart_end = df["date"].max()
                        sym_trades = sym_trades[(sym_trades["dt"] >= chart_start) & (sym_trades["dt"] <= chart_end)]
                        
                        for _, t in sym_trades.iterrows():
                            # Type determination
                            t_type = str(t.get("type", "")).lower()
                            t_price = t.get("price", 0)
                            if t_price == 0: continue
                                
                            start_close = df["close"].iloc[0]
                            t_norm = (t_price / start_close) * 100
                            
                            t_dt = t["dt"]
                            
                            if "매수" in t_type or "buy" in t_type or t_type == "2":
                                # Buy Marker: BLUE (User Request)
                                self.ax_price.scatter(t_dt, t_norm, marker='^', c='blue', s=120, edgecolors='black', zorder=10)
                                self.ax_price.text(t_dt, t_norm, "B", color='blue', fontweight='bold', fontsize=12, ha='center', va='bottom')
                            elif "매도" in t_type or "sell" in t_type or t_type == "1":
                                # Sell Marker: RED (User Request)
                                self.ax_price.scatter(t_dt, t_norm, marker='v', c='red', s=120, edgecolors='black', zorder=10)
                                self.ax_price.text(t_dt, t_norm, "S", color='red', fontweight='bold', fontsize=12, ha='center', va='top')
                                
                                # Ghost Tail Line (120 mins after sell)
                                # Dotted Line
                                end_dt_ghost = t_dt + pd.Timedelta(minutes=120)
                                ghost_mask = (df["date"] >= t_dt) & (df["date"] <= end_dt_ghost)
                                if ghost_mask.any():
                                     self.ax_price.plot(df.loc[ghost_mask, "date"], df.loc[ghost_mask, "normalized"], 
                                                       color="black", linestyle=":", linewidth=2.0, alpha=0.6, label="_nolegend_")

            self.canvas_price.draw()
            
            # Plot Return Chart
            self.ax_return.clear()
            
            # Calculate Alpha (Excess Return) for coloring
            df["return"] = df["close"].pct_change() * 100
            df["cum_return"] = (1 + df["return"]/100).cumprod() - 1
            df["cum_return"] = df["cum_return"] * 100 # %
            
            # Color logic: Green if positive, Red if negative
            self.ax_return.plot(df["date"], df["cum_return"].fillna(0), 
                               color="purple", linewidth=2, label="Garam")
            self.ax_return.axhline(0, color="black", linestyle="--", linewidth=1)
            
            # Hero period highlight
            if is_hero == 1:
                self.ax_return.axvspan(
                    hero_period["date"].min(), hero_period["date"].max(),
                    alpha=0.2, color="yellow"
                )
            
            final_return = df["cum_return"].iloc[-1]
            self.ax_return.set_title(
                f"누적 수익률: {final_return:.2f}%", 
                fontsize=14, weight="bold", 
                color="green" if final_return > 0 else "red"
            )
            self.ax_return.set_xlabel("시간")
            self.ax_return.set_ylabel("누적 수익률 (%)")
            self.ax_return.grid(True, alpha=0.3)
            self.ax_return.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
            self.canvas_return.draw()
            
        except Exception as e:
            self.ax_price.clear()
            self.ax_price.text(
                0.5, 0.5, f"차트 로드 실패:\n{e}",
                ha="center", va="center", fontsize=12, color="red"
            )
            self.canvas_price.draw()


def main():
    app = QApplication(sys.argv)
    
    # Set style
    app.setStyle("Fusion")
    
    window = HeroVisualizerGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
