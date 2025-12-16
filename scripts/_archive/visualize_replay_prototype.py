"""
Garam Replay Visualizer (Prototype)
Generates dummy data to demonstrate the visual replay capabilities.
"""
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import plotly.io as pio
from datetime import datetime, timedelta

# 1. Create Dummy Data
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", periods=200, freq='D')
n_days = len(dates)

# KOSPI (Benchmark)
kospi_base = 2500
kospi_ret = np.random.normal(0.0002, 0.01, n_days)
kospi_price = kospi_base * np.cumprod(1 + kospi_ret)

# GARAM Equity (Performance)
equity_base = 100_000_000
# Simulation: Sometimes beats, sometimes fails
garam_ret = kospi_ret + np.random.normal(0.0005, 0.005, n_days) 
equity_curve = equity_base * np.cumprod(1 + garam_ret)

# Turbo State (Background Color)
# 0: Base, 1: Turbo, 2: Cooldown
regime_state = np.zeros(n_days)
regime_state[50:100] = 1 # Turbo Run
regime_state[120:130] = 2 # Cooldown directly after?
regime_state[150:180] = 1

# Trade Events (Buy/Sell Markers)
trades = []
# Randomly generate some trades
for i in range(10, n_days-10):
    if np.random.random() < 0.05: # Buy
        trades.append({
            'date': dates[i],
            'type': 'BUY',
            'price': float(equity_curve[i]),
            'desc': f"BUY Signal<br>Momentum: {np.random.randint(80,99)}<br>Vol: Low"
        })
    elif np.random.random() < 0.03: # Sell
        trades.append({
            'date': dates[i],
            'type': 'SELL',
            'price': float(equity_curve[i]),
            'desc': f"SELL Signal<br>Trailing Stop: -3%<br>Profit: +{np.random.randint(5,20)}%"
        })

# 400 Random Stocks (Background Noise)
background_traces = []
for _ in range(50): # 400 is too heavy for simple html prototype, use 50 for demo
    stock_ret = kospi_ret + np.random.normal(0, 0.02, n_days)
    stock_price = 100 * np.cumprod(1 + stock_ret)
    background_traces.append(stock_price)

# 2. Build Plotly Figure
fig = go.Figure()

# Layer 1: Background Stocks (Light Grey)
x_axis = dates
for trace in background_traces:
    # Normalize to start at Equity Base for visual comparison
    norm_trace = trace / trace[0] * equity_base
    fig.add_trace(go.Scatter(
        x=x_axis, y=norm_trace,
        mode='lines',
        line=dict(color='rgba(150,150,150,0.3)', width=1), # Increased Opacity (0.1 -> 0.3)
        hoverinfo='skip',
        showlegend=False
    ))

# Layer 1.5: Active Holding Paths (Highlight "The Horse We Rode")
# Simulate connection between Buy and Sell
for t_buy, t_sell in zip([t for t in trades if t['type']=='BUY'], [t for t in trades if t['type']=='SELL']):
    # Find indices
    try:
        idx_buy = np.where(dates == t_buy['date'])[0][0]
        idx_sell = np.where(dates == t_sell['date'])[0][0]
        
        # We need a stock trace to highlight. 
        # In this dummy demo, we'll just highlight the Equity Curve itself or a random stock trace?
        # User wants to see "The stock we bought". 
        # Let's pick a random background trace to pretend it was the one we bought.
        stock_idx = np.random.randint(0, len(background_traces))
        selected_trace = background_traces[stock_idx]
        norm_trace = selected_trace / selected_trace[0] * equity_base
        
        fig.add_trace(go.Scatter(
            x=x_axis[idx_buy:idx_sell+1], y=norm_trace[idx_buy:idx_sell+1],
            mode='lines+markers',
            line=dict(color='orange', width=3),
            marker=dict(size=0), # Line only
            name='Active Trade',
            hoverinfo='text',
            hovertext=f"Held {t_buy['date'].strftime('%Y-%m-%d')} ~ {t_sell['date'].strftime('%Y-%m-%d')}"
        ))
    except:
        pass

# Layer 2: KOSPI (Benchmark)
# Normalize KOSPI to Equity Base
norm_kospi = kospi_price / kospi_price[0] * equity_base
fig.add_trace(go.Scatter(
    x=x_axis, y=norm_kospi,
    mode='lines',
    name='KOSPI (Norm)',
    line=dict(color='black', width=2, dash='dot')
))

# Layer 3: Equity Curve
fig.add_trace(go.Scatter(
    x=x_axis, y=equity_curve,
    mode='lines',
    name='Garam Equity',
    line=dict(color='blue', width=3)
))

# Layer 4: Trade Markers
buy_x = [t['date'] for t in trades if t['type'] == 'BUY']
buy_y = [t['price'] for t in trades if t['type'] == 'BUY']
buy_txt = [t['desc'] for t in trades if t['type'] == 'BUY']

sell_x = [t['date'] for t in trades if t['type'] == 'SELL']
sell_y = [t['price'] for t in trades if t['type'] == 'SELL']
sell_txt = [t['desc'] for t in trades if t['type'] == 'SELL']

fig.add_trace(go.Scatter(
    x=buy_x, y=buy_y,
    mode='markers',
    name='BUY',
    marker=dict(symbol='triangle-up', size=12, color='green'),
    text=buy_txt,
    hoverinfo='text+x'
))

fig.add_trace(go.Scatter(
    x=sell_x, y=sell_y,
    mode='markers',
    name='SELL',
    marker=dict(symbol='triangle-down', size=12, color='red'),
    text=sell_txt,
    hoverinfo='text+x'
))

# 3. Animation Frames (Replay Logic)
frames = []
for i in range(1, n_days, 2): # Step 2 for speed in demo
    frames.append(go.Frame(
        data=[
            # We don't animate background lines to save performance, only the main lines
            # Update KOSPI
            go.Scatter(x=x_axis[:i], y=norm_kospi[:i]), 
            # Update Equity
            go.Scatter(x=x_axis[:i], y=equity_curve[:i]) 
        ],
        name=str(i)
    ))

# Button List Construction
dropdown_buttons = [
    dict(label="None (Clear)",
         method="restyle",
         args=["line.color", ['rgba(150,150,150,0.3)']*len(background_traces) + ['black', 'blue', 'green', 'red', 'orange'], 
               list(range(len(background_traces))) 
         ])
]

for k in range(len(background_traces)):
    # Create color array: K-th is Red, others Grey
    colors = ['rgba(150,150,150,0.1)'] * len(background_traces)
    colors[k] = 'red'
    widths = [1] * len(background_traces)
    widths[k] = 3
    
    dropdown_buttons.append(
        dict(label=f"Highlight Stock {k}",
             method="restyle",
             args=[{"line.color": colors, "line.width": widths}, 
                   list(range(len(background_traces)))]
        )
    )

# 4. Layout & Controls
fig.update_layout(
    title="Garam Visual Replay (Prototype)",

    template="plotly_white",
    hovermode="x unified",
    xaxis=dict(
        range=[dates[0], dates[-1]],
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(count=2, label="2y", step="year", stepmode="backward"),
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
        ),
        dict(
            type="dropdown",
            direction="down",
            x=0.3, y=1.25,
            showactive=True,
            active=0,
            buttons=dropdown_buttons
        )
    ],
    sliders=[{
        "active": 0,
        "yanchor": "top",
        "xanchor": "left",
        "currentvalue": {"font": {"size": 20}, "prefix": "Day:", "visible": True, "xanchor": "right"},
        "transition": {"duration": 300, "easing": "cubic-in-out"},
        "pad": {"b": 10, "t": 50},
        "len": 0.9,
        "x": 0.1,
        "y": 0,
        "steps": [{"args": [[str(k)], {"frame": {"duration": 300, "redraw": False}, "mode": "immediate", "transition": {"duration": 300}}], "label": str(k), "method": "animate"} for k in range(1, n_days, 5)]
    }]
)

# Speed Control Hint (Plotly doesn't support native Speed Slider easily via Python, 
# so usually we implement fixed speeds in buttons or use Dash. 
# For this HTML prototype, we preset 'duration=50'' which is fast.)
fig.add_annotation(
    x=0.5, y=1.1, xref="paper", yref="paper",
    text="Prototype Note: Speed Volume is fixed at 20fps for this demo.",
    showarrow=False, font=dict(color="gray")
)

# Highlighting Turbo Zones (Shapes)
shapes = []
for i in range(n_days-1):
    if regime_state[i] == 1:
        shapes.append(dict(
            type="rect", xref="x", yref="paper",
            x0=dates[i], x1=dates[i+1], y0=0, y1=1,
            fillcolor="rgba(255,0,0,0.1)", layer="below", line_width=0
        ))
    elif regime_state[i] == 2:
        shapes.append(dict(
            type="rect", xref="x", yref="paper",
            x0=dates[i], x1=dates[i+1], y0=0, y1=1,
            fillcolor="rgba(0,0,255,0.1)", layer="below", line_width=0
        ))
fig.update_layout(shapes=shapes)

# Save
output_file = "garam_replay_prototype_v4.html"
fig.write_html(output_file)
print(f"Prototype saved to {output_file}")
