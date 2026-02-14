"""
400 Symbol Hero Scan Visualization
- All 400 symbols in grid layout
- Color coding: Heroes (green), Non-heroes (gray)
- Latest data snapshot
"""
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

def visualize_400_symbols(scan_csv_path: Path, output_path: Path = None):
    """Create comprehensive 400-symbol visualization"""
    
    # Load scan results
    df = pd.read_csv(scan_csv_path)
    
    # Sort by score descending
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    
    # Stats
    total = len(df)
    heroes = (df["is_hero"] == 1).sum()
    avg_rsi = df["rsi"].mean()
    
    print(f"Total Symbols: {total}")
    print(f"Heroes: {heroes}")
    print(f"Avg RSI: {avg_rsi:.2f}")
    
    # Create figure
    fig = plt.figure(figsize=(24, 16))
    fig.suptitle(f"400 Symbol Hero Scan Results (Latest Data)\nHeroes: {heroes} | Avg RSI: {avg_rsi:.1f}", 
                 fontsize=20, weight="bold")
    
    # Grid: 20 rows x 20 cols = 400
    rows, cols = 20, 20
    
    for idx, row in df.iterrows():
        if idx >= 400:
            break
        
        symbol = row["symbol"]
        is_hero = row.get("is_hero", 0)
        score = row.get("score", 0.0)
        rsi = row.get("rsi", 50.0)
        close_price = row.get("close", 0.0)
        
        # Position in grid
        r = idx // cols
        c = idx % cols
        
        # Create subplot
        ax = plt.subplot2grid((rows, cols), (r, c))
        
        # Color based on hero status
        if is_hero == 1:
            color = "green"
            edge_color = "darkgreen"
            linewidth = 2
        else:
            color = "gray"
            edge_color = "lightgray"
            linewidth = 0.5
        
        # Bar representing RSI (0-100)
        ax.barh(0, rsi, color=color, edgecolor=edge_color, linewidth=linewidth)
        ax.set_xlim(0, 100)
        ax.set_ylim(-0.5, 0.5)
        
        # Symbol label
        ax.text(50, 0, symbol, ha="center", va="center", 
                fontsize=6, weight="bold", color="white")
        
        # Turn off axes
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(False)
    
    # Legend
    hero_patch = mpatches.Patch(color="green", label="Heroes")
    normal_patch = mpatches.Patch(color="gray", label="Non-Heroes")
    fig.legend(handles=[hero_patch, normal_patch], loc="upper right", fontsize=12)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {output_path}")
    
    plt.show()


def create_summary_charts(scan_csv_path: Path):
    """Create detailed summary charts"""
    
    df = pd.read_csv(scan_csv_path)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("Hero Scan Analysis (400 Symbols)", fontsize=16, weight="bold")
    
    # 1. RSI Distribution
    ax1 = axes[0, 0]
    ax1.hist(df["rsi"], bins=30, color="steelblue", edgecolor="black")
    ax1.axvline(30, color="red", linestyle="--", label="Hero Threshold (RSI < 30)")
    ax1.set_xlabel("RSI")
    ax1.set_ylabel("Count")
    ax1.set_title("RSI Distribution")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Score Distribution
    ax2 = axes[0, 1]
    heroes = df[df["is_hero"] == 1]
    non_heroes = df[df["is_hero"] != 1]
    
    if not heroes.empty:
        ax2.hist(heroes["score"], bins=20, color="green", alpha=0.7, label="Heroes")
    if not non_heroes.empty:
        ax2.hist(non_heroes["score"], bins=20, color="gray", alpha=0.5, label="Non-Heroes")
    
    ax2.set_xlabel("Score")
    ax2.set_ylabel("Count")
    ax2.set_title("Score Distribution")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Top 20 Symbols
    ax3 = axes[1, 0]
    top20 = df.nlargest(20, "score")
    colors = ["green" if h == 1 else "gray" for h in top20["is_hero"]]
    
    ax3.barh(range(len(top20)), top20["score"], color=colors)
    ax3.set_yticks(range(len(top20)))
    ax3.set_yticklabels(top20["symbol"])
    ax3.set_xlabel("Score")
    ax3.set_title("Top 20 Symbols by Score")
    ax3.invert_yaxis()
    ax3.grid(True, axis="x", alpha=0.3)
    
    # 4. Hero Summary Table
    ax4 = axes[1, 1]
    ax4.axis("off")
    
    total = len(df)
    heroes_count = (df["is_hero"] == 1).sum()
    avg_rsi = df["rsi"].mean()
    min_rsi = df["rsi"].min()
    max_rsi = df["rsi"].max()
    
    summary_text = f"""
    SCAN SUMMARY
    ════════════════════════════
    Total Symbols:     {total}
    Heroes Found:      {heroes_count}
    Hero Rate:         {heroes_count/total*100:.2f}%
    
    RSI Statistics:
    ────────────────────────────
    Average:           {avg_rsi:.2f}
    Min:               {min_rsi:.2f}
    Max:               {max_rsi:.2f}
    
    Probe:             MR_RSI_30
    Threshold:         RSI < 30
    Window:            14
    """
    
    ax4.text(0.1, 0.5, summary_text, fontsize=12, family="monospace",
             verticalalignment="center")
    
    plt.tight_layout()
    
    output_path = Path("results/hero_scan_analysis_400.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {output_path}")
    
    plt.show()


if __name__ == "__main__":
    import argparse
    
    p = argparse.ArgumentParser()
    p.add_argument("--scan_csv", required=True, help="Path to hero scan CSV")
    p.add_argument("--output", default="results/hero_scan_400_grid.png")
    args = p.parse_args()
    
    scan_path = Path(args.scan_csv)
    
    if not scan_path.exists():
        print(f"Error: {scan_path} not found")
        sys.exit(1)
    
    print("Creating visualizations...")
    
    # Grid view (all 400)
    visualize_400_symbols(scan_path, Path(args.output))
    
    # Summary charts
    create_summary_charts(scan_path)
    
    print("Done!")
