import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add project root to Python path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))


# Add project root to Python path (consistent with other dashboard pages)
from src.metrics.market_data import get_electricity_se3, compute_electricity_metrics

def get_electricity_se3_metrics(force_refresh=False):
    df = get_electricity_se3(force_refresh)
    metrics = compute_electricity_metrics(df)
    return df, metrics

df = get_electricity_se3()
metrics, df = compute_electricity_metrics(df)

if metrics is None or len(metrics) == 0:
    st.warning("Electricity data not available.")
    st.stop()


# --------------------------------------------------
# Page Setup
# --------------------------------------------------


st.set_page_config(layout="wide")
st.title("Market Environment & Cost Structure")


st.markdown(
    "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
    unsafe_allow_html=True
)


# --------------------------------------------------
# Electricity Cost Analysis
# --------------------------------------------------

st.subheader("Electricity Cost (Southern Sweden - SE3)")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Current", f"{metrics['latest']:.0f} SEK/MWh")
col2.metric("7d Avg", f"{metrics['avg_7d']:.0f} SEK/MWh")
col3.metric("30d Avg", f"{metrics['avg_30d']:.0f} SEK/MWh")
col4.metric("Volatility", f"{metrics['volatility']:.0f} SEK/MWh")


fig = go.Figure()

# --- Volatility band (draw first so it's behind) ---
fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["upper"],
    line=dict(width=0),
    showlegend=False,
    hoverinfo="skip"
))

fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["lower"],
    fill='tonexty',
    fillcolor='rgba(242, 139, 130, 0.10)',
    line=dict(width=0),
    name="Volatility Band",
    hoverinfo="skip"
))

# --- Raw price (light) ---
fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["price_sek_mwh"],
    mode="lines",
    line=dict(color="#F28B82", width=1),
    opacity=0.5,
    name="Price",
    hovertemplate="%{x}<br>%{y:.0f} SEK/MWh<extra></extra>"
))

# --- Trend line (main signal) ---
fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["trend_30d"],
    mode="lines",
    line=dict(color="#5A6F89", width=3),
    name="30d Trend",
    hovertemplate="%{x}<br>%{y:.0f} SEK/MWh<extra></extra>"
))

# --- Layout ---
fig.update_layout(
    height=420,
    plot_bgcolor="white",
    margin=dict(l=20, r=20, t=20, b=20),
    yaxis_title="SEK/MWh",
    xaxis_title="Date",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)
# --- Regime Markers ---
# Iran shock
fig.add_vline(
    x="2026-02-28",
    line_dash="dot",
    line_color="rgba(0,0,0,0.7)",
    line_width=2
)

fig.add_annotation(
    x="2026-02-28",
    y=df["price_sek_mwh"].quantile(0.9),  # better than max
    text="Geopolitical Shock (Feb 2026)",
    showarrow=False,
    yshift=115,
    font=dict(size=10, color="rgba(0,0,0,0.9)")
)

# --- Y-axis: clean 250 bands ---
max_y = df["price_sek_mwh"].max()
upper_bound = df["price_sek_mwh"].quantile(0.98)
upper_bound = int(np.ceil(upper_bound / 250) * 250)

fig.update_yaxes(
    range=[0, upper_bound],
    dtick=250,
    gridcolor="rgba(0,0,0,0.05)"
)

# --- X-axis clean ---
fig.update_xaxes(
    gridcolor="rgba(0,0,0,0.05)"
)



st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.markdown("""
Electricity prices exhibit sustained volatility over the past year, with repeated spikes and wide deviations from the underlying trend. 
This is expected to directly impacts processing and operating margins, particularly for smaller operators. Smaller operators are more exposed to these swings due to limited cost absorption capacity.
""")