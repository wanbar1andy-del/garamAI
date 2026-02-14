
import sys
import json
import time
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

# Config
CONFIG_PATH = Path("c:/garam/garam/config/active_strategy_params.json")

class AdaptiveDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GARAM OSS: Active Adaptation Monitor")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("background-color: #1e1e1e; color: #00ff00;")
        
        layout = QVBoxLayout()
        
        self.title_label = QLabel("SYSTEM STATUS: WAITING")
        self.title_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        self.param_label = QLabel("Waiting for OSS update...")
        self.param_label.setFont(QFont("Consolas", 12))
        self.param_label.setStyleSheet("color: #cccccc;")
        layout.addWidget(self.param_label)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # Check timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_config)
        self.timer.start(1000) # Check every 1s
        
        self.last_ts = ""

    def check_config(self):
        if not CONFIG_PATH.exists():
            return
            
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
                
            ts = data.get("timestamp", "")
            if ts != self.last_ts:
                self.last_ts = ts
                self.update_ui(data)
        except:
            pass
            
    def update_ui(self, data):
        params = data.get("parameters", {})
        perf = data.get("performance_expectation", {})
        
        self.title_label.setText("🔥 ACTIVE PARAMETERS UPDATED 🔥")
        self.title_label.setStyleSheet("color: #ff0055;") # Flash color
        QTimer.singleShot(500, lambda: self.title_label.setStyleSheet("color: #00ff00;"))
        
        text = f"""
        [Adaptation Timestamp]
        {data.get('timestamp')}
        
        [Target Volatility]
        {params.get('target_vol', 0):.4f} (Sensitivity)
        
        [Max Multiplier]
        {params.get('max_mult', 0):.2f}x (Aggression)
        
        [Moving Averages]
        {params.get('fast_ma')} / {params.get('slow_ma')}
        
        [Expected Performance]
        Return: {perf.get('return', 0):.2f}%
        Max Drawdown: {perf.get('mdd', 0):.2f}%
        """
        self.param_label.setText(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdaptiveDashboard()
    window.show()
    sys.exit(app.exec_())
