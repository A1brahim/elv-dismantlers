import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add project root to Python path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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


# Compute last 4 months for display
df["month"] = pd.to_datetime(df["date"]).dt.to_period("M")

monthly_avg = (
    df.groupby("month")["price_sek_mwh"]
    .mean()
    .sort_index()
)
last_4 = monthly_avg.tail(4)
values = last_4.values
months = last_4.index
deltas = [
    None,
    values[1] - values[0],
    values[2] - values[1],
    values[3] - values[2]
]


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
st.caption("Source: Nord Pool Spot Prices (via Elprisetjustnu API)")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Current", f"{metrics['latest']:,.0f} SEK/MWh")
col2.metric("7d Avg", f"{metrics['avg_7d']:,.0f} SEK/MWh")
col3.metric("30d Avg", f"{metrics['avg_30d']:,.0f} SEK/MWh")
col4.metric("Volatility", f"{metrics['volatility']:,.0f} SEK/MWh")

st.markdown("#### Recent Monthly Averages")

display_months = months[1:]
display_values = values[1:]
display_deltas = deltas[1:]

col1, col2, col3 = st.columns(3)

for col, month, value, delta in zip(
    [col1, col2, col3],
    display_months,
    display_values,
    display_deltas
):
    col.metric(
        month.strftime("%b %Y"),
        f"{value:,.0f} SEK/MWh",
        delta=f"{delta:+,.0f}" if delta is not None else None,
        delta_color="inverse"
    )

last_delta = display_deltas[-1]
last_date = df["date"].iloc[-1]
last_price = df["price_sek_mwh"].iloc[-1]

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
    hovertemplate="%{x}<br>%{y:,.0f} SEK/MWh<extra></extra>"
))

# --- Trend line (main signal) ---
fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["trend_30d"],
    mode="lines",
    line=dict(color="#5A6F89", width=2),
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
    text="Geopolitical Shock (28 Feb 2026)",
    showarrow=False,
    xshift=70,
    yshift=100,
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

st.markdown(
    "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
    unsafe_allow_html=True
)


# -------------------------------
# Diesel Cost Analysis
# -------------------------------

from src.metrics.market_data import get_diesel_se, compute_diesel_metrics

diesel_df = get_diesel_se()
diesel_metrics, diesel_df = compute_diesel_metrics(diesel_df)

st.markdown("#### Fuel Cost (Diesel)")
st.caption("Data harvested from OKQ8 Energy (Corporate Price Data)")

col_d1, col_d2, col_d3, col_d4 = st.columns(4)

col_d1.metric("Current", f"{diesel_metrics['latest']:.2f} SEK/L")
col_d2.metric("7d Avg", f"{diesel_metrics['avg_7d']:.2f} SEK/L")
col_d3.metric("30d Avg", f"{diesel_metrics['avg_30d']:.2f} SEK/L")
col_d4.metric("Volatility", f"{diesel_metrics['volatility']:.2f} SEK/L")

# Monthly Cards
diesel_df["month"] = pd.to_datetime(diesel_df["date"]).dt.to_period("M")

monthly_avg_diesel = (
    diesel_df.groupby("month")["price_sek_litre"]
    .mean()
    .sort_index()
)

last_4_diesel = monthly_avg_diesel.tail(4)

values_d = last_4_diesel.values
months_d = last_4_diesel.index

deltas_d = [
    None,
    values_d[1] - values_d[0],
    values_d[2] - values_d[1],
    values_d[3] - values_d[2]
]

st.markdown("#### Recent Monthly Averages")

col1, col2, col3 = st.columns(3)

for col, month, value, delta in zip(
    [col1, col2, col3],
    months_d[1:],
    values_d[1:],
    deltas_d[1:]
):
    col.metric(
        month.strftime("%b %Y"),
        f"{value:.2f} SEK/L",
        delta=f"{delta:+.2f}" if delta is not None else None,
        delta_color="inverse"
    )

# Time Series Plot

fig_diesel = go.Figure()

# Volatility band (same as electricity)
fig_diesel.add_trace(go.Scatter(
    x=diesel_df["date"],
    y=diesel_df["upper"],
    line=dict(width=0),
    showlegend=False,
    hoverinfo="skip"
))

fig_diesel.add_trace(go.Scatter(
    x=diesel_df["date"],
    y=diesel_df["lower"],
    fill='tonexty',
    fillcolor='rgba(242, 139, 130, 0.10)',  # ← MATCH electricity
    line=dict(width=0),
    name="Volatility Band",
    hoverinfo="skip"
))

# Raw price
fig_diesel.add_trace(go.Scatter(
    x=diesel_df["date"],
    y=diesel_df["price_sek_litre"],
    mode="lines",
    line=dict(color="#F28B82", width=1),
    opacity=0.5,
    name="Price",
    hovertemplate="%{x}<br>%{y:.2f} SEK/L<extra></extra>"
))

# Trend
fig_diesel.add_trace(go.Scatter(
    x=diesel_df["date"],
    y=diesel_df["trend_30d"],
    mode="lines",
    line=dict(width=2.0, color="#5A6F89"),
    name="30d Trend",
    hovertemplate="%{x}<br>%{y:.2f} SEK/L<extra></extra>"
))

fig_diesel.update_layout(
    height=420,
    plot_bgcolor="white",
    margin=dict(l=20, r=20, t=20, b=20),
    yaxis_title="SEK/L",
    xaxis_title="Date",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

fig_diesel.update_xaxes(
    tickformat="%b %Y",   # Jan 2026
    dtick="M1",          # monthly ticks
    gridcolor="rgba(0,0,0,0.05)"
)

# --- Regime Marker (IRAN Shock) ---
fig_diesel.add_vline(
    x="2026-02-28",
    line_dash="dot",
    line_color="rgba(0,0,0,0.7)",
    line_width=2
)

fig_diesel.add_annotation(
    x="2026-02-28",
    y=diesel_df["price_sek_litre"].quantile(0.9),
    text="Geopolitical Shock (28 Feb 2026)",
    showarrow=False,
    xshift=70,
    yshift=105,
    font=dict(size=10, color="rgba(0,0,0,0.9)")
)

st.plotly_chart(fig_diesel, use_container_width=True, config={"displayModeBar": False})

st.markdown("""
Diesel costs have structurally increased since 28 February, tightening margins for operators reliant on long-distance transport, particularly those outside urban areas.""")


st.markdown(
    "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
    unsafe_allow_html=True
)


# -------------------------------
# Scrap Metal Prices (Revenue)
# -------------------------------

from src.metrics.market_data import get_metal_prices, compute_metal_metrics

metal_df = get_metal_prices()
metal_metrics, metal_df = compute_metal_metrics(metal_df)

st.markdown("#### Scrap Metal Prices Copper (COMEX Futures, SEK)")
st.caption("Source: Yahoo Finance (COMEX Copper Futures 'HG=F', converted to SEK via USD/SEK)")


col_m1, col_m2, col_m3, col_m4 = st.columns(4)

col_m1.metric("Current", f"{metal_metrics['latest']:,.2f} SEK")
col_m2.metric("7d Avg", f"{metal_metrics['avg_7d']:,.2f} SEK")
col_m3.metric("30d Avg", f"{metal_metrics['avg_30d']:,.2f} SEK")
col_m4.metric("Volatility", f"{metal_metrics['volatility']:,.2f}")

# Monthly cards
metal_df["month"] = pd.to_datetime(metal_df["date"]).dt.to_period("M")

monthly_avg_metal = (
    metal_df.groupby("month")["copper_sek"]
    .mean()
    .sort_index()
)

last_4_metal = monthly_avg_metal.tail(4)

values_m = last_4_metal.values
months_m = last_4_metal.index

deltas_m = [
    None,
    values_m[1] - values_m[0],
    values_m[2] - values_m[1],
    values_m[3] - values_m[2]
]

st.markdown("#### Recent Monthly Averages")

col1, col2, col3 = st.columns(3)

for col, month, value, delta in zip(
    [col1, col2, col3],
    months_m[1:],
    values_m[1:],
    deltas_m[1:]
):
    col.metric(
        month.strftime("%b %Y"),
        f"{value:.2f}",
        delta=f"{delta:+.2f}" if delta is not None else None,
        delta_color="inverse"
    )

# Plot
fig_metal = go.Figure()

# Volatility band
fig_metal.add_trace(go.Scatter(
    x=metal_df["date"],
    y=metal_df["upper"],
    line=dict(width=0),
    showlegend=False,
    hoverinfo="skip"
))

fig_metal.add_trace(go.Scatter(
    x=metal_df["date"],
    y=metal_df["lower"],
    fill='tonexty',
    fillcolor='rgba(242, 139, 130, 0.10)',
    line=dict(width=0),
    name="Volatility Band",
    hoverinfo="skip"
))

# Raw price
fig_metal.add_trace(go.Scatter(
    x=metal_df["date"],
    y=metal_df["copper_sek"],
    mode="lines",
    line=dict(color="#F28B82", width=1),
    opacity=0.5,
    name="Price",
    hovertemplate="%{x}<br>%{y:.2f}<extra></extra>"
))

# Trend
fig_metal.add_trace(go.Scatter(
    x=metal_df["date"],
    y=metal_df["trend_30d"],
    mode="lines",
    line=dict(width=2.0, color="#5A6F89"),
    name="30d Trend",
    hovertemplate="%{x}<br>%{y:.2f}<extra></extra>"
))

fig_metal.update_layout(
    height=420,
    plot_bgcolor="white",
    margin=dict(l=20, r=20, t=20, b=20),
    yaxis_title="SEK",
    xaxis_title="Date",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

fig_metal.update_xaxes(
    tickformat="%b %Y",
    dtick="M1",
    gridcolor="rgba(0,0,0,0.05)"
)

# Regime marker
fig_metal.add_vline(
    x="2026-02-28",
    line_dash="dot",
    line_color="rgba(0,0,0,0.7)",
    line_width=2
)

fig_metal.add_annotation(
    x="2026-02-28",
    y=metal_df["copper_sek"].quantile(0.9),
    text="Geopolitical Shock (28 Feb 2026)",
    showarrow=False,
    xshift=70,
    yshift=105,
    font=dict(size=10, color="rgba(0,0,0,0.9)")
)

st.plotly_chart(fig_metal, use_container_width=True, config={"displayModeBar": False})

st.markdown("""
Copper prices show moderate upward momentum with relatively contained volatility, suggesting stable revenue conditions compared to the more volatile cost environment.
""")

st.markdown(
    "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
    unsafe_allow_html=True
)

st.markdown("#### Scrap Metal Prices – Aluminium (SEK/tonne, LME Futures)")
st.caption("Source: Yahoo Finance (ALI=F), converted using USD/SEK FX")

if "aluminium_sek" not in metal_df.columns:
    st.warning("Aluminium data currently unavailable (data source issue).")

else:
    series_al = metal_df["aluminium_sek"]

    # --- Metrics ---
    col_a1, col_a2, col_a3, col_a4 = st.columns(4)

    col_a1.metric("Current", f"{series_al.iloc[-1]:,.0f} SEK")
    col_a2.metric("7d Avg", f"{series_al.tail(7).mean():,.0f} SEK")
    col_a3.metric("30d Avg", f"{series_al.tail(30).mean():,.0f} SEK")
    col_a4.metric("Volatility", f"{series_al.tail(30).std():,.0f}")

    # --- Monthly ---
    metal_df["month"] = pd.to_datetime(metal_df["date"]).dt.to_period("M")

    monthly_avg_al = (
        metal_df.groupby("month")["aluminium_sek"]
        .mean()
        .sort_index()
    )

    last_4_al = monthly_avg_al.tail(4)

    values_al = last_4_al.values
    months_al = last_4_al.index

    deltas_al = [
        None,
        values_al[1] - values_al[0],
        values_al[2] - values_al[1],
        values_al[3] - values_al[2]
    ]

    st.markdown("#### Recent Monthly Averages")

    col1, col2, col3 = st.columns(3)

    for col, month, value, delta in zip(
        [col1, col2, col3],
        months_al[1:],
        values_al[1:],
        deltas_al[1:]
    ):
        col.metric(
            month.strftime("%b %Y"),
            f"{value:,.0f}",
            delta=f"{delta:+,.0f}" if delta is not None else None,
            delta_color="inverse"
        )

    # --- Rolling ---
    trend_al = series_al.rolling(30, min_periods=10).mean()
    vol_al = series_al.rolling(30, min_periods=10).std()

    upper_al = trend_al + vol_al
    lower_al = trend_al - vol_al

    # --- Plot ---
    fig_al = go.Figure()

    fig_al.add_trace(go.Scatter(
        x=metal_df["date"], y=upper_al, line=dict(width=0), showlegend=False
    ))

    fig_al.add_trace(go.Scatter(
        x=metal_df["date"],
        y=series_al,
        mode="lines",
        line=dict(color="#F28B82", width=1),
        opacity=0.5,
        name="Price",
        hovertemplate="%{x}<br>%{y:,.0f} SEK<extra></extra>"
        ))

    fig_al.add_trace(go.Scatter(
        x=metal_df["date"],
        y=upper_al,
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip"
    ))
    
    fig_al.add_trace(go.Scatter(
        x=metal_df["date"],
        y=lower_al,
        fill='tonexty',
        fillcolor='rgba(242, 139, 130, 0.10)',
        line=dict(width=0),
        name="Volatility Band",
        hoverinfo="skip"
    ))

    # 30d trend
    fig_al.add_trace(go.Scatter(
        x=metal_df["date"],
        y=trend_al,
        mode="lines",
        line=dict(color="#5A6F89", width=2),
        name="30d Trend",
        hovertemplate="%{x}<br>%{y:,.0f} SEK<extra></extra>"
        ))

# --- Layout ---
fig_al.update_layout(
    height=420,
    plot_bgcolor="white",
    margin=dict(l=20, r=20, t=20, b=20),
    yaxis_title="SEK/tonne",
    xaxis_title="Date",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

fig_al.update_xaxes(
    tickformat="%b %Y",
    dtick="M1",
    gridcolor="rgba(0,0,0,0.05)"
)

fig_al.update_yaxes(
    gridcolor="rgba(0,0,0,0.05)"
)

# --- Regime Marker ---
fig_al.add_vline(
    x="2026-02-28",
    line_dash="dot",
    line_color="rgba(0,0,0,0.7)",
    line_width=2
)

fig_al.add_annotation(
    x="2026-02-28",
    y=series_al.quantile(0.9),
    text="Geopolitical Shock (28 Feb 2026)",
    showarrow=False,
    xshift=70,
    yshift=105,
    font=dict(size=10, color="rgba(0,0,0,0.9)")
)

st.plotly_chart(fig_al, use_container_width=True, config={"displayModeBar": False})

st.markdown("""
Aluminium prices show more gradual and stable movements compared to copper, reflecting their role as a lower-margin, volume-driven revenue component. This provides some revenue stability, though with less upside sensitivity.
""")
