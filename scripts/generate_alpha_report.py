
"""
Simple PDF Alpha Report Generator
---------------------------------
Generates a PDF summary of Alpha Performance using Matplotlib.
Includes:
- KOSPI Excess Return
- Optimal Exit Accuracy (Ghost Tail)
- Key Risk Metrics
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf
from pathlib import Path
from datetime import datetime

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "GARAM_Data"
REPORT_DIR = PROJECT_ROOT / "reports"

def generate_alpha_report():
    today_str = datetime.now().strftime("%Y-%m-%d")
    pdf_path = REPORT_DIR / f"Alpha_Report_{today_str}.pdf"
    
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Data
    ghost_tail_path = LOG_DIR / "ghost_tail.csv"
    
    # KOSPI Data (Mock or Load)
    # Ideally we load KOSPI CSV. If missing, we skip specific chart.
    
    # 2. Create PDF
    pdf = matplotlib.backends.backend_pdf.PdfPages(pdf_path)
    
    # --- Page 1: Dashboard ---
    fig = plt.figure(figsize=(11.69, 8.27)) # A4 Landscape
    fig.suptitle(f"Garam Tactical Alpha Report ({today_str})", fontsize=20, weight='bold')
    
    # Grid Layout
    grid = plt.GridSpec(2, 2, wspace=0.3, hspace=0.3)
    
    # A. Exit Accuracy (Pie Chart)
    ax1 = fig.add_subplot(grid[0, 0])
    
    if ghost_tail_path.exists():
        df = pd.read_csv(ghost_tail_path)
        if not df.empty:
            # Verdicts
            # PERFECT_EXIT (Diff < -0.5%)
            # TOO_EARLY (Diff > 0.5%)
            # NEUTRAL
            
            # Re-calculate or use existing if column exists
            if 'verdict' not in df.columns:
                 # simple logic
                 df['verdict'] = df.apply(lambda r: "PERFECT" if r['diff_120m'] < -0.5 else ("EARLY" if r['diff_120m'] > 0.5 else "NEUTRAL"), axis=1)
            
            v_counts = df['verdict'].value_counts()
            colors = {'PERFECT': '#4CAF50', 'EARLY': '#F44336', 'NEUTRAL': '#9E9E9E', 'PERFECT_EXIT': '#4CAF50', 'TOO_EARLY': '#F44336'}
            ax1.pie(v_counts, labels=v_counts.index, autopct='%1.1f%%', 
                   colors=[colors.get(x, 'gray') for x in v_counts.index],
                   startangle=90)
            ax1.set_title("Optimal Exit Accuracy (120m Post-Sell)")
            
            # Opportunity Cost Stat
            opp_loss_avg = df[df['diff_120m'] > 0]['diff_120m'].mean()
            ax1.text(0, -1.2, f"Avg Opp. Loss: {opp_loss_avg:.2f}%", ha='center', fontsize=12, color='red')
            
        else:
            ax1.text(0.5, 0.5, "No Trades", ha='center')
    else:
        ax1.text(0.5, 0.5, "No Data", ha='center')
        
    # B. Performance Placeholder (Alpha Curve)
    ax2 = fig.add_subplot(grid[0, 1])
    ax2.text(0.5, 0.5, "Alpha Curve (Simulation Pending)", ha='center')
    ax2.set_title("Cumulative Extcess Return (Alpha)")
    
    # C. Strategy Text Summary
    ax3 = fig.add_subplot(grid[1, :])
    ax3.axis('off')
    
    summary_text = f"""
    [Execution Summary]
    - Report Generated: {datetime.now().strftime("%H:%M:%S")}
    - System Status: OSS Active (Level 3)
    
    [Tactical Insights]
    - 'Ghost Tail' tracking is active for all SELL orders.
    - System is monitoring for 'Early Exit' bias.
    - If Early Exit ratio > 60%, Trailing Stop buffer will automatically expand.
    """
    ax3.text(0.1, 0.8, summary_text, fontsize=12, family='monospace')
    
    pdf.savefig(fig)
    pdf.close()
    
    print(f"[PDF] Report Generated: {pdf_path}")

if __name__ == "__main__":
    generate_alpha_report()
