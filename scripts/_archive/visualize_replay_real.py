"""
Garam Replay Visualizer (Real Data)
"""
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# 1. Load Simulation Results
try:
    history_df = pd.read_csv("sim_test_result.csv")
    history_df['date'] = pd.to_datetime(history_df['date'])
    history_df.sort_values('date', inplace=True)
    dates = history_df['date'].unique()
    
    # Equity & Regime
    equity_curve = history_df['equity'].values
    regime_labels = history_df['regime'].values
    
    # Load KOSPI (Benchmark)
    kospi_path = "GARAM_Data/kr/index/kospi_dashboard.csv"
    try:
        kdf = pd.read_csv(kospi_path)
        kdf['date'] = pd.to_datetime(kdf['date'])
        kdf = kdf.set_index('date').reindex(history_df['date']).interpolate()
        kospi_price = kdf['close'].values
    except:
        # Fallback if no KOSPI file
        kospi_price = np.ones(len(equity_curve)) * 2500
        
except Exception as e:
    print(f"Error loading data: {e}")
    exit()

# 2. Build Figures
fig = go.Figure()

# Layer 1: KOSPI
# Normalize
norm_kospi = kospi_price / kospi_price[0] * equity_curve[0]
fig.add_trace(go.Scatter(
    x=history_df['date'], y=norm_kospi,
    mode='lines',
    name='KOSPI (Norm)',
    line=dict(color='black', width=2, dash='dot')
))

# Layer 2: Equity
fig.add_trace(go.Scatter(
    x=history_df['date'], y=equity_curve,
    mode='lines',
    name='Garam Equity',
    line=dict(color='blue', width=3)
))

# Layer 3: Regime Background (Turbo Zones)
shapes = []
# Very simple regime logic: Look for strings like "TURBO"
prev_regime = ""
start_idx = 0
for i in range(len(history_df)):
    curr_regime = str(regime_labels[i])
    if "TURBO" in curr_regime:
        is_turbo = True
    else:
        is_turbo = False
        
    date_val = history_df['date'].iloc[i]
    
    # Check change
    # Optimization: Just draw daily bars for now or merge blocks
    if "TURBO" in curr_regime:
         shapes.append(dict(
            type="rect", xref="x", yref="paper",
            x0=date_val, x1=date_val + pd.Timedelta(days=1), y0=0, y1=1,
            fillcolor="rgba(255,0,0,0.1)", layer="below", line_width=0
        ))
    elif "COOLDOWN" in curr_regime:
         shapes.append(dict(
            type="rect", xref="x", yref="paper",
            x0=date_val, x1=date_val + pd.Timedelta(days=1), y0=0, y1=1,
            fillcolor="rgba(0,0,255,0.1)", layer="below", line_width=0
        ))

fig.update_layout(shapes=shapes)

# Layout
fig.update_layout(
    title="Garam Visual Replay (Real Data: 26 Symbols)",
    template="plotly_white",
    hovermode="x unified",
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(step="all", label="All")
            ])
        ),
        rangeslider=dict(visible=True), 
        type="date"
    ),
    yaxis=dict(title="Value (KRW)"),
    updatemenus=[
        dict(
            type="buttons",
            showactive=False,
            x=0.05, y=1.25, 
            buttons=[
                dict(label="▶ Play",
                     method="animate",
                     args=[None, dict(frame=dict(duration=50, redraw=False), fromcurrent=True)]),
                dict(label="⏸ Pause",
                     method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])
            ]
        )
    ]
)

# Frames for Animation
frames = []
dates_list = history_df['date'].tolist()
for i in range(1, len(dates_list), 5):
    frames.append(go.Frame(
        data=[
            go.Scatter(x=dates_list[:i], y=norm_kospi[:i]),
            go.Scatter(x=dates_list[:i], y=equity_curve[:i])
        ],
        name=str(i)
    ))
fig.frames = frames

# Save
output_file = "garam_replay_real.html"
fig.write_html(output_file)
print(f"Real Replay saved to {output_file}")
