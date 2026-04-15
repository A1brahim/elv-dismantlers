import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.title("Firm Financial Performance")

@st.cache_data
def load_data():
    return pd.read_csv("data/processed/elv_full_metrics.csv")

df = load_data()

# Standardise column names for internal consistency
df = df.rename(columns={
    "Company": "company",
    "Year": "year",
    "Net sales": "total_revenue",
    "EBITDA": "ebitda",
    "YoY Revenue Growth": "revenue_yoy",
    "Operating Margin": "operating_margin",
    "Net Margin": "net_margin",
    "Market Share": "market_share",
    "Profit Share": "profit_share"
})

# -------------------------------------------------
# Revenue Growth Dynamics
# -------------------------------------------------

st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        Revenue Growth Dynamics
    <div style="font-size:1.2rem; color:#6B7280; margin-top:0;">
        Multi-Year Firm Performance (2021–Latest)
    </div>
    """,
    unsafe_allow_html=True
)

df_growth = df.copy()

industry_growth = (
    df_growth.groupby("year")["revenue_yoy"]
    .mean()
    .reset_index()
)

industry_vol = (
    df_growth.groupby("year")["revenue_yoy"]
    .std()
    .reset_index()
)

industry_growth["upper"] = industry_growth["revenue_yoy"] + industry_vol["revenue_yoy"]
industry_growth["lower"] = industry_growth["revenue_yoy"] - industry_vol["revenue_yoy"]

fig_growth = go.Figure()

for company in df_growth["company"].unique():
    company_df = df_growth[df_growth["company"] == company]
    fig_growth.add_trace(go.Scatter(
        x=company_df["year"],
        y=company_df["revenue_yoy"] * 100,
        mode="lines+markers",
        line=dict(color="silver"),
        showlegend=False,
        hovertemplate="<b>%{text}</b><br>Year: %{x}<br>YoY Growth: %{y:.2f}%<extra></extra>",
        text=[company]*len(company_df)
    ))

fig_growth.add_trace(go.Scatter(
    x=industry_growth["year"],
    y=industry_growth["upper"] * 100,
    mode="lines",
    line=dict(width=0),
    showlegend=False
))

fig_growth.add_trace(go.Scatter(
    x=industry_growth["year"],
    y=industry_growth["lower"] * 100,
    mode="lines",
    fill="tonexty",
    fillcolor="rgba(93,173,226,0.15)",
    line=dict(width=0),
    name="Industry Volatility (±1σ)"
))

# Industry average
fig_growth.add_trace(go.Scatter(
    x=industry_growth["year"],
    y=industry_growth["revenue_yoy"] * 100,
    mode="lines",
    line=dict(color="#5DADE2", width=2),
    name="Industry Average"
))

all_years = sorted(df_growth["year"].unique().tolist() + [2025])

fig_growth.update_layout(
    height=450,
    xaxis=dict(
        title="Year",
        tickmode="array",
        tickvals=all_years,
        range=[min(all_years) - 0.1, max(all_years) + 0.1]
    ),
    yaxis_title="Revenue YoY Growth (%)",
    legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
)


st.plotly_chart(fig_growth, use_container_width=True)

# Summary insight for Revenue Growth Dynamics
avg_growth = industry_growth["revenue_yoy"].mean() * 100
latest_year = industry_growth["year"].max()
latest_growth = industry_growth.loc[
    industry_growth["year"] == latest_year, "revenue_yoy"
].values[0] * 100
volatility_avg = industry_vol["revenue_yoy"].mean() * 100

st.markdown(
    f"**Revenue Growth:** Over the observed period, the industry experienced an average year-on-year "
    f"revenue growth of **{avg_growth:.1f}%**. The shaded band (±1σ) reflects typical volatility around the industry "
    f"trend, with an average dispersion of approximately **{volatility_avg:.1f} percentage points**."
)
# -------------------------------------------------
# CAGR Growth Dynamics
# -------------------------------------------------

st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        Revenue Compound Annual Growth Rate (CAGR)
    <div style="font-size:1.2rem; color:#6B7280; margin-top:0;">
         Firm Performance (2021–Latest)
    </div>
    """,
    unsafe_allow_html=True
)

cagr_df = (
    df.groupby("company")["CAGR_21_24"]
    .first()
    .reset_index()
)

# Sort companies by CAGR descending (match Executive Summary)
cagr_df = cagr_df.sort_values("CAGR_21_24", ascending=False)

# Split positive and negative performers
positive_df = cagr_df[cagr_df["CAGR_21_24"] >= 0]
negative_df = cagr_df[cagr_df["CAGR_21_24"] < 0]

industry_avg_cagr = cagr_df["CAGR_21_24"].mean()
industry_std_cagr = cagr_df["CAGR_21_24"].std()

fig_cagr = go.Figure()

# Positive bars
fig_cagr.add_trace(go.Bar(
    x=positive_df["company"],
    y=positive_df["CAGR_21_24"] * 100,
    marker_color="#5A6F89",
    name="Positive Performance"
))

# Negative bars
fig_cagr.add_trace(go.Bar(
    x=negative_df["company"],
    y=negative_df["CAGR_21_24"] * 100,
    marker_color="#F28B82",
    name="Negative Performance"
))

# Industry average with whiskers
fig_cagr.add_trace(go.Bar(
    x=["Industry Average"],
    y=[industry_avg_cagr * 100],
    marker_color="#AEB6BF",
    error_y=dict(
        type="data",
        array=[industry_std_cagr * 100],
        visible=True
    ),
    name="Industry Average (±1σ)"
))

fig_cagr.update_layout(
    height=500,
    xaxis_title="Company",
    yaxis_title="Revenue CAGR (%)",
    legend=dict(
        orientation="v",
        y=1,
        x=1.02
    ),
    plot_bgcolor="white"
)

st.plotly_chart(fig_cagr, use_container_width=True)

# Summary insight for Revenue CAGR
avg_cagr_pct = industry_avg_cagr * 100

st.markdown(
    f"**Revenue Growth:** Over the 2021–2024 period, the industry recorded an average revenue CAGR of "
    f"**{avg_cagr_pct:.1f}%**. The dispersion around the industry average (shown by the ±1σ error bar) "
    "highlights significant variation in firm-level growth trajectories across the market."
)

# -------------------------------------------------
# Structural Net Margin (Mean ± Volatility)
# -------------------------------------------------

st.markdown("---")

st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        Structural Net Margin
    <div style="font-size:1.2rem; color:#6B7280; margin-top:0;">
        Multi-Year Firm Performance (2021–Latest)
    </div>
    """,
    unsafe_allow_html=True
)

df_net = df.copy()

# Remove missing safely
df_net = df_net[df_net["net_margin"].notna()]

# Industry structural mean per year
industry_net = (
    df_net.groupby("year")["net_margin"]
    .mean()
    .reset_index()
)

# Industry volatility per year
industry_net_vol = (
    df_net.groupby("year")["net_margin"]
    .std()
    .reset_index()
)

industry_net["upper"] = industry_net["net_margin"] + industry_net_vol["net_margin"]
industry_net["lower"] = industry_net["net_margin"] - industry_net_vol["net_margin"]

fig_net_struct = go.Figure()

# Individual firm traces (light silver)
for company in df_net["company"].unique():
    company_df = df_net[df_net["company"] == company]
    fig_net_struct.add_trace(go.Scatter(
        x=company_df["year"],
        y=company_df["net_margin"] * 100,
        mode="lines+markers",
        line=dict(color="silver"),
        showlegend=False,
        hovertemplate="<b>%{text}</b><br>Year: %{x}<br>Net Margin: %{y:.2f}%<extra></extra>",
        text=[company]*len(company_df)
    ))

# Upper volatility bound
fig_net_struct.add_trace(go.Scatter(
    x=industry_net["year"],
    y=industry_net["upper"] * 100,
    mode="lines",
    line=dict(width=0),
    showlegend=False
))

# Lower volatility bound + fill
fig_net_struct.add_trace(go.Scatter(
    x=industry_net["year"],
    y=industry_net["lower"] * 100,
    mode="lines",
    fill="tonexty",
    fillcolor="rgba(93,173,226,0.15)",
    line=dict(width=0),
    name="Industry Volatility (±1σ)"
))

# Industry mean line
fig_net_struct.add_trace(go.Scatter(
    x=industry_net["year"],
    y=industry_net["net_margin"] * 100,
    mode="lines",
    line=dict(color="#5DADE2", width=2),
    name="Industry Average"
))

fig_net_struct.update_layout(
    height=450,
    xaxis=dict(
        title="Year",
        tickmode="array",
        tickvals=sorted(df_net["year"].unique())
    ),
    yaxis_title="Net Margin (%)",
    legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center"),
    plot_bgcolor="white"
)

st.plotly_chart(fig_net_struct, use_container_width=True)

# Summary insight
avg_net_margin = industry_net["net_margin"].mean() * 100
net_volatility = industry_net_vol["net_margin"].mean() * 100

st.markdown(
    f"**Structural Net Margin:** Across the observed period, the industry "
    f"maintained an average net margin of **{avg_net_margin:.1f}%**, "
    f"with an average dispersion of approximately **{net_volatility:.1f} percentage points** "
    f"around the structural mean."
)

# -------------------------------------------------
# Net Profit Margin (Latest Year)
# -------------------------------------------------

st.markdown("---")

latest_net_year = df["year"].max()
st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        Net Profit Margin
    <div style="font-size:1.2rem; color:#6B7280; margin-top:0;">
        Firm Performance (Latest Year: {latest_net_year})
    </div>
    """,
    unsafe_allow_html=True
)

net_df = df[df["year"] == latest_net_year].copy()

# Remove missing values safely
net_df = net_df[net_df["net_margin"].notna()]

# Industry benchmark
industry_net_margin = net_df["net_margin"].mean()

# Flag performance vs industry
net_df["performance_flag"] = net_df["net_margin"].apply(
    lambda x: "Above Industry Mean"
    if x >= industry_net_margin
    else "Below Industry Mean"
)

# Sort ascending for visual clarity
net_df = net_df.sort_values("net_margin", ascending=False)

fig_net = go.Figure()

# Above Industry
fig_net.add_trace(go.Bar(
    x=net_df[net_df["performance_flag"] == "Above Industry Mean"]["company"],
    y=net_df[net_df["performance_flag"] == "Above Industry Mean"]["net_margin"] * 100,
    marker_color="#5A6F89",
    name="Above Industry Mean"
))

# Below Industry
fig_net.add_trace(go.Bar(
    x=net_df[net_df["performance_flag"] == "Below Industry Mean"]["company"],
    y=net_df[net_df["performance_flag"] == "Below Industry Mean"]["net_margin"] * 100,
    marker_color="#F28B82",
    name="Below Industry Mean"
))

# Industry average line
fig_net.add_shape(
    type="line",
    x0=-0.5,
    x1=len(net_df["company"]) - 0.5,
    y0=industry_net_margin * 100,
    y1=industry_net_margin * 100,
    line=dict(color="#9C9EA4", width=2)
)

# Legend entry for benchmark
fig_net.add_trace(go.Scatter(
    x=[None], y=[None],
    mode="lines",
    line=dict(color="#9C9EA4", width=2),
    name="Industry Mean"
))

fig_net.update_layout(
    height=500,
    xaxis_title="Company",
    yaxis=dict(
        title="Net Margin (%)",
        range=[-10, 30],
        dtick=5   # ← force axis to 30%
    ),
    legend=dict(
        orientation="v",
        y=1,
        x=1.02
    ),
    plot_bgcolor="white"
)

st.plotly_chart(fig_net, use_container_width=True)

# Insight summary
st.markdown(
    f"**Net Profitability ({latest_net_year}):** "
    f"The industry recorded an average net margin of "
    f"**{industry_net_margin * 100:.1f}%**. Firms above this benchmark "
    "demonstrate stronger bottom-line conversion after financing and tax effects."
)

# -------------------------------------------------
# Profitability & Margin Structure
# -------------------------------------------------

st.markdown("---")

st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        Profitability & Margin Structure
    <div style="font-size:1.2rem; color:#6B7280; margin-top:0;">
        Multi-Year Firm Performance (2021–Latest)
    </div>
    """,
    unsafe_allow_html=True
)


df_margin = df.copy()

industry_margin = (
    df_margin.groupby("year")["operating_margin"]
    .mean()
    .reset_index()
)

industry_vol_margin = (
    df_margin.groupby("year")["operating_margin"]
    .std()
    .reset_index()
)

industry_margin["upper"] = industry_margin["operating_margin"] + industry_vol_margin["operating_margin"]
industry_margin["lower"] = industry_margin["operating_margin"] - industry_vol_margin["operating_margin"]

fig_margin = go.Figure()

for company in df_margin["company"].unique():
    company_df = df_margin[df_margin["company"] == company]
    fig_margin.add_trace(go.Scatter(
        x=company_df["year"],
        y=company_df["operating_margin"] * 100,
        mode="lines+markers",
        line=dict(color="silver"),
        showlegend=False,
        hovertemplate="<b>%{text}</b><br>Year: %{x}<br>Operating Margin: %{y:.2f}%<extra></extra>",
        text=[company]*len(company_df)
    ))

fig_margin.add_trace(go.Scatter(
    x=industry_margin["year"],
    y=industry_margin["upper"] * 100,
    mode="lines",
    line=dict(width=0),
    showlegend=False
))

fig_margin.add_trace(go.Scatter(
    x=industry_margin["year"],
    y=industry_margin["lower"] * 100,
    mode="lines",
    fill="tonexty",
    fillcolor="rgba(93,173,226,0.15)",
    line=dict(width=0),
    name="Industry Volatility (±1σ)"
))

fig_margin.add_trace(go.Scatter(
    x=industry_margin["year"],
    y=industry_margin["operating_margin"] * 100,
    mode="lines",
    line=dict(color="#5DADE2", width=2),
    name="Industry Average"
))

fig_margin.update_layout(
    height=450,
    xaxis=dict(
        title="Year",
        tickmode="array",
        tickvals=sorted(df_margin["year"].unique())
    ),
    yaxis_title="Operating Margin (%)",
    legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
)


st.plotly_chart(fig_margin, use_container_width=True)

# Summary insight for Profitability & Margin Structure
avg_margin = industry_margin["operating_margin"].mean() * 100
latest_margin_year = industry_margin["year"].max()
latest_margin = industry_margin.loc[
    industry_margin["year"] == latest_margin_year, "operating_margin"
].values[0] * 100
margin_volatility = industry_vol_margin["operating_margin"].mean() * 100

st.markdown(
    f"**Profitability:** Over the observed period, the industry maintained an average operating margin of "
    f"**{avg_margin:.1f}%**. The shaded band (±1σ) represents typical variability in firm-level profitability, "
    f"with an average dispersion of approximately **{margin_volatility:.1f} percentage points**."
)


# -------------------------------------------------
# Profit Pool Distribution
# -------------------------------------------------

st.markdown("---")
st.subheader("Profit Pool Distribution")

df_profit = df.copy()

selected_year = st.selectbox(
    "Select Year for Profit Pool Analysis",
    sorted(df_profit["year"].unique())
)

year_df = df_profit[df_profit["year"] == selected_year]

fig_pool = go.Figure()

# Industry average profit share (mean across firms for selected year)
industry_avg_profit = year_df["profit_share"].mean()


# Split above and below industry average
above_df = year_df[year_df["profit_share"] >= industry_avg_profit]
below_df = year_df[year_df["profit_share"] < industry_avg_profit]

# Above industry average
fig_pool.add_trace(go.Bar(
    x=above_df["company"],
    y=above_df["profit_share"] * 100,
    name="Above Industry Average",
    marker_color="#5A6F89"
))

# Below industry average
fig_pool.add_trace(go.Bar(
    x=below_df["company"],
    y=below_df["profit_share"] * 100,
    name="Below Industry Average",
    marker_color="#F28B82"
))


fig_pool.add_trace(go.Scatter(
    x=year_df["company"],
    y=[industry_avg_profit * 100] * len(year_df),
    mode="lines",
    line=dict(color="#9C9EA4", width=2),
    name="Industry Average"
))

fig_pool.update_layout(
    height=450,
    xaxis_title="Company",
    yaxis_title="Profit Share (%)",
    legend=dict(
        orientation="v",
        y=1,
        x=1.02
    ),
    plot_bgcolor="white"
)



st.plotly_chart(fig_pool, use_container_width=True)

# Summary insight for Profit Pool Distribution
# Identify top firm and concentration metrics for the selected year
top_idx = year_df["profit_share"].idxmax()
top_company = year_df.loc[top_idx, "company"]
top_share_pct = year_df.loc[top_idx, "profit_share"] * 100

# Number of firms above industry average
num_above_avg = above_df.shape[0]
total_firms = year_df.shape[0]

# Concentration: cumulative share of top 3 firms
top3_share_pct = (
    year_df.sort_values("profit_share", ascending=False)
    .head(3)["profit_share"]
    .sum() * 100
)

st.markdown(
    f"**Profit Pool ({int(selected_year)}):** The industry’s average profit share stood at "
    f"**{industry_avg_profit * 100:.1f}%**, with **{num_above_avg} out of {total_firms} firms** capturing a "
    f"disproportionate share of profits."
)

# -------------------------------------------------
# Cumulative Profit Pool (2021–2024)
# -------------------------------------------------

st.markdown("---")
st.subheader("Cumulative Profit Pool (2021–2024)")

df_cum = df.copy()

# Aggregate metrics across 4 years
cum_df = (
    df_cum.groupby("company")
    .agg(
        total_profit=("ebitda", "sum"),
        avg_market_share=("market_share", "mean")
    )
    .reset_index()
)

industry_avg_profit_total = cum_df["total_profit"].mean()
industry_avg_share_total = cum_df["avg_market_share"].mean()

# Color logic based on industry average total profit
cum_df["color"] = cum_df["total_profit"].apply(
    lambda x: "#5A6F89" if x >= industry_avg_profit_total else "#F28B82"
)

fig_bubble = go.Figure()

fig_bubble.add_trace(go.Scatter(
    x=cum_df["avg_market_share"] * 100,
    y=cum_df["total_profit"],
    mode="markers",
    marker=dict(
        size=cum_df["total_profit"] / cum_df["total_profit"].max() * 60,
        color=cum_df["color"],
        sizemode="diameter",
        opacity=0.8,
        line=dict(width=0)
    ),
    text=cum_df["company"],
    hovertemplate="<b>%{text}</b><br>Avg Market Share: %{x:.2f}%<br>Total Profit (4Y): %{y:,.0f} SEK<extra></extra>",
    showlegend=False
))

# Vertical industry average line (market share)
fig_bubble.add_shape(
    type="line",
    x0=industry_avg_share_total * 100,
    x1=industry_avg_share_total * 100,
    y0=cum_df["total_profit"].min(),
    y1=cum_df["total_profit"].max(),
    line=dict(color="#9C9EA4", width=2)
)

# Horizontal industry average line (total profit)
fig_bubble.add_shape(
    type="line",
    x0=(cum_df["avg_market_share"].min() * 100),
    x1=(cum_df["avg_market_share"].max() * 100),
    y0=industry_avg_profit_total,
    y1=industry_avg_profit_total,
    line=dict(color="#9C9EA4", width=2)
)

fig_bubble.add_trace(go.Scatter(
    x=[None], y=[None],
    mode="markers",
    marker=dict(size=12, color="#5A6F89"),
    name="Above Industry Avg Profit"
))

fig_bubble.add_trace(go.Scatter(
    x=[None], y=[None],
    mode="markers",
    marker=dict(size=12, color="#F28B82"),
    name="Below Industry Avg Profit"
))

fig_bubble.update_layout(
    height=500,
    xaxis_title="Average Market Share (2021–2024) (%)",
    yaxis_title="Total Profit Captured (4-Year Sum, SEK)",
    legend=dict(
        orientation="h",
        y=1.08,
        x=0.5,
        xanchor="center"
    ),
    plot_bgcolor="white"
)



st.plotly_chart(fig_bubble, use_container_width=True)

# Summary insight for Cumulative Profit Pool
# Identify the firm capturing the largest cumulative profit
leader_idx = cum_df["total_profit"].idxmax()
leader_company = cum_df.loc[leader_idx, "company"]
leader_profit = cum_df.loc[leader_idx, "total_profit"]
leader_share = cum_df.loc[leader_idx, "avg_market_share"] * 100

# Calculate concentration of the top three firms
top3_profit_share = (
    cum_df.sort_values("total_profit", ascending=False)
    .head(3)["total_profit"]
    .sum() / cum_df["total_profit"].sum() * 100
)

# Count firms above the industry average profit
num_above_profit = (cum_df["total_profit"] >= industry_avg_profit_total).sum()
total_firms = cum_df.shape[0]

st.markdown(
    f"**Cumulative Profit (2021–2024):** Over the full period, profitability was highly concentrated, "
    f"with **{num_above_profit} out of {total_firms} firms** generating profits above the industry average. "
)

# -------------------------------------------------
# Structural Power Matrix
# -------------------------------------------------

st.markdown("---")
st.subheader("Structural Power Matrix (2021–2024)")

df_struct = df.copy()

# Aggregate structural metrics
struct_df = (
    df_struct.groupby("company")
    .agg(
        avg_market_share=("market_share", "mean"),
        avg_operating_margin=("operating_margin", "mean"),
        total_profit=("ebitda", "sum")
    )
    .reset_index()
)

industry_avg_share = struct_df["avg_market_share"].mean()
industry_avg_margin = struct_df["avg_operating_margin"].mean()

fig_struct = go.Figure()

# Color based on structural strength (above both averages = strong position)
struct_df["color"] = struct_df.apply(
    lambda row: "#5A6F89"
    if (row["avg_market_share"] >= industry_avg_share and
        row["avg_operating_margin"] >= industry_avg_margin)
    else "#F28B82",
    axis=1
)


fig_struct.add_trace(go.Scatter(
    x=struct_df["avg_market_share"] * 100,
    y=struct_df["avg_operating_margin"] * 100,
    mode="markers",
    text=struct_df["company"],
    marker=dict(
        size=18,
        color=struct_df["color"],
        opacity=0.9,
        line=dict(width=0)
    ),
    hovertemplate="<b>%{text}</b><br>Avg Market Share: %{x:.2f}%<br>Avg Operating Margin: %{y:.2f}%<br>Total Profit (4Y): %{customdata:,.0f} SEK<extra></extra>",
    customdata=struct_df["total_profit"],
    showlegend=False
))

# Legend traces for structural classification
fig_struct.add_trace(go.Scatter(
    x=[None], y=[None],
    mode="markers",
    marker=dict(size=12, color="#5A6F89"),
    name="Leaders (Above Share & Margin)"
))

fig_struct.add_trace(go.Scatter(
    x=[None], y=[None],
    mode="markers",
    marker=dict(size=12, color="#F28B82"),
    name="Below Structural Threshold"
))


# Vertical industry average line (market share)
fig_struct.add_shape(
    type="line",
    x0=industry_avg_share * 100,
    x1=industry_avg_share * 100,
    y0=struct_df["avg_operating_margin"].min() * 100,
    y1=struct_df["avg_operating_margin"].max() * 100,
    line=dict(color="#9C9EA4", width=2)
)

# Horizontal industry average line (margin)
fig_struct.add_shape(
    type="line",
    x0=struct_df["avg_market_share"].min() * 100,
    x1=struct_df["avg_market_share"].max() * 100,
    y0=industry_avg_margin * 100,
    y1=industry_avg_margin * 100,
    line=dict(color="#9C9EA4", width=2)
)

x_vals = struct_df["avg_market_share"] * 100
y_vals = struct_df["avg_operating_margin"] * 100

x_padding = (x_vals.max() - x_vals.min()) * 0.15
y_padding = (y_vals.max() - y_vals.min()) * 0.20

x_min = x_vals.min() - x_padding
x_max = x_vals.max() + x_padding
y_min = y_vals.min() - y_padding
y_max = y_vals.max() + y_padding

fig_struct.update_layout(
    height=550,
    xaxis=dict(
        title="Average Market Share (2021–2024) (%)",
        range=[x_min, x_max]
    ),
    yaxis=dict(
        title="Average Operating Margin (2021–2024) (%)",
        range=[y_min, y_max]
    ),
    legend=dict(
        orientation="h",
        y=1.08,
        x=0.5,
        xanchor="center"
    ),
    plot_bgcolor="white"
)


st.plotly_chart(fig_struct, use_container_width=True)

# Summary insight for Structural Power Matrix
# Count firms classified as structural leaders (above both industry averages)
num_leaders = (
    (struct_df["avg_market_share"] >= industry_avg_share) &
    (struct_df["avg_operating_margin"] >= industry_avg_margin)
).sum()
total_struct_firms = struct_df.shape[0]

st.markdown(
    f"**Structural Power (2021–2024):** {num_leaders} out of {total_struct_firms} firms "
    f"operate above both the industry average market share and operating margin."
)

# -------------------------------------------------
# Scale Efficiency Analysis (Revenue vs Market Share)
# -------------------------------------------------

st.markdown("---")
st.subheader("Scale Efficiency Analysis (2021–2024)")

# Aggregate firm-level averages across 2021–2024
scale_df = (
    df.groupby("company")
    .agg(
        avg_revenue=("total_revenue", "mean"),
        avg_market_share=("market_share", "mean"),
        avg_operating_margin=("operating_margin", "mean")
    )
    .reset_index()
)

# Convert to percentage for display (margin and share)
scale_df["avg_margin_pct"] = scale_df["avg_operating_margin"] * 100
scale_df["avg_share_pct"] = scale_df["avg_market_share"] * 100

# -----------------------------
# 1️⃣ Margin vs Market Share
# -----------------------------

y_margin = scale_df["avg_margin_pct"].values

# OLS via numpy (degree 1 polynomial fit)
coef_share = np.polyfit(scale_df["avg_share_pct"], scale_df["avg_margin_pct"], 1)
y_pred_share = np.polyval(coef_share, scale_df["avg_share_pct"])

corr_share = np.corrcoef(scale_df["avg_share_pct"], scale_df["avg_margin_pct"])[0, 1]
r2_share = corr_share ** 2

fig_scale_share = go.Figure()

fig_scale_share.add_trace(go.Scatter(
    x=scale_df["avg_share_pct"],
    y=scale_df["avg_margin_pct"],
    mode="markers",
    text=scale_df["company"],
    marker=dict(size=14, color="#5A6F89"),
    hovertemplate="<b>%{text}</b><br>Avg Market Share: %{x:.2f}%<br>Avg Margin: %{y:.2f}%<extra></extra>"
))

fig_scale_share.add_trace(go.Scatter(
    x=scale_df["avg_share_pct"],
    y=y_pred_share,
    mode="lines",
    line=dict(color="#F28B82", width=2),
    name="OLS Trendline"
))

fig_scale_share.update_layout(
    height=450,
    xaxis_title="Average Market Share (%)",
    yaxis_title="Average Operating Margin (%)",
    plot_bgcolor="white",
    showlegend=False
)

st.plotly_chart(fig_scale_share, use_container_width=True)

st.markdown(
    f"**Scale Efficiency (Market Share → Margin, 2021–2024):** "
    f"The relationship between average market share and operating margin shows a "
    f"positive association, with a correlation of **{corr_share:.2f}** "
    f"and an R² of **{r2_share:.2f}**."
)

# -----------------------------
# 2️⃣ Margin vs Revenue
# -----------------------------

# OLS via numpy (degree 1 polynomial fit)
coef_rev = np.polyfit(scale_df["avg_revenue"], scale_df["avg_margin_pct"], 1)
y_pred_rev = np.polyval(coef_rev, scale_df["avg_revenue"])

corr_rev = np.corrcoef(scale_df["avg_revenue"], scale_df["avg_margin_pct"])[0, 1]
r2_rev = corr_rev ** 2

fig_scale_rev = go.Figure()

fig_scale_rev.add_trace(go.Scatter(
    x=scale_df["avg_revenue"],
    y=scale_df["avg_margin_pct"],
    mode="markers",
    text=scale_df["company"],
    marker=dict(size=14, color="#5A6F89"),
    hovertemplate="<b>%{text}</b><br>Avg Revenue: %{x:,.0f} SEK<br>Avg Margin: %{y:.2f}%<extra></extra>"
))

fig_scale_rev.add_trace(go.Scatter(
    x=scale_df["avg_revenue"],
    y=y_pred_rev,
    mode="lines",
    line=dict(color="#F28B82", width=2),
    name="OLS Trendline"
))

fig_scale_rev.update_layout(
    height=450,
    xaxis_title="Average Revenue (SEK)",
    yaxis_title="Average Operating Margin (%)",
    plot_bgcolor="white",
    showlegend=False
)

st.plotly_chart(fig_scale_rev, use_container_width=True)


st.markdown(
    f"**Scale Efficiency (Revenue → Margin, 2021–2024):** "
    f"A positive relationship is also observed between average revenue and operating margin, "
    f"with a correlation of **{corr_rev:.2f}** and an R² of **{r2_rev:.2f}**."
)

# -------------------------------------------------
# Profit Efficiency Ratio (Profit per 1% Market Share)
# -------------------------------------------------

st.markdown("---")
st.subheader("Profit Efficiency Ratio (2021–2024)")

eff_df = (
    df.groupby("company")
    .agg(
        total_profit=("ebitda", "sum"),
        avg_market_share=("market_share", "mean")
    )
    .reset_index()
)

# Avoid division by zero
eff_df = eff_df[eff_df["avg_market_share"] > 0]


eff_df["profit_per_share_unit"] = (
    eff_df["total_profit"] / (eff_df["avg_market_share"] * 100)
)

# -------------------------------------------------
# Profit vs Market Share Scatter (Structural View)
# -------------------------------------------------

fig_eff_scatter = go.Figure()

fig_eff_scatter.add_trace(go.Scatter(
    x=eff_df["avg_market_share"] * 100,
    y=eff_df["total_profit"],
    mode="markers",
    text=eff_df["company"],
    marker=dict(
        size=16,
        color="#5A6F89",
        opacity=0.85
    ),
    hovertemplate="<b>%{text}</b><br>Avg Market Share: %{x:.2f}%<br>Total Profit: %{y:,.0f} SEK<extra></extra>"
))


# Linear structural benchmark
coef_eff = np.polyfit(eff_df["avg_market_share"], eff_df["total_profit"], 1)
# Model fit statistics
corr_eff = np.corrcoef(eff_df["avg_market_share"], eff_df["total_profit"])[0, 1]
r2_eff = corr_eff ** 2

sorted_eff = eff_df.sort_values("avg_market_share")

fig_eff_scatter.add_trace(go.Scatter(
    x=sorted_eff["avg_market_share"] * 100,
    y=np.polyval(coef_eff, sorted_eff["avg_market_share"]),
    mode="lines",
    line=dict(color="#F28B82", width=2),
    name="Structural Benchmark"
))

fig_eff_scatter.update_layout(
    height=450,
    xaxis_title="Average Market Share (2021–2024) (%)",
    yaxis_title="Total Profit (4-Year Sum, SEK)",
    plot_bgcolor="white",
    showlegend=False
)

st.plotly_chart(fig_eff_scatter, use_container_width=True)

st.markdown(
    f"**Profit Efficiency (Market Share → Profit, 2021–2024):** "
    f"The relationship between average market share and total profit "
    f"shows a positive structural association, with a correlation of "
    f"**{corr_eff:.2f}** and an R² of **{r2_eff:.2f}**."
)

eff_df = eff_df.sort_values("profit_per_share_unit", ascending=False)

# Compute industry median benchmark for profit efficiency
industry_median_eff = eff_df["profit_per_share_unit"].median()

# Difference vs industry median
eff_df["diff_vs_median"] = eff_df["profit_per_share_unit"] - industry_median_eff

above_eff = eff_df[eff_df["profit_per_share_unit"] >= industry_median_eff]
below_eff = eff_df[eff_df["profit_per_share_unit"] < industry_median_eff]

fig_eff = go.Figure()

# Above Industry Median
fig_eff.add_trace(go.Bar(
    x=above_eff["company"],
    y=above_eff["profit_per_share_unit"],
    marker_color="#5A6F89",
    name="Above Industry Median",
    text=above_eff["diff_vs_median"],
    texttemplate="+%{text:,.0f}",
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Profit per 1% Share: %{y:,.0f} SEK<br>Vs Median: +%{text:,.0f} SEK<extra></extra>"
))

# Below Industry Median
fig_eff.add_trace(go.Bar(
    x=below_eff["company"],
    y=below_eff["profit_per_share_unit"],
    marker_color="#F28B82",
    name="Below Industry Median",
    text=below_eff["diff_vs_median"],
    texttemplate="%{text:,.0f}",
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Profit per 1% Share: %{y:,.0f} SEK<br>Vs Median: %{text:,.0f} SEK<extra></extra>"
))

# 3️⃣ Horizontal median line (continuous)
fig_eff.add_shape(
    type="line",
    x0=-0.5,
    x1=len(eff_df["company"]) - 0.5,
    y0=industry_median_eff,
    y1=industry_median_eff,
    line=dict(color="#9C9EA4", width=2)
)

# 4️⃣ Legend entry for median line
fig_eff.add_trace(go.Scatter(
    x=[None], y=[None],
    mode="lines",
    line=dict(color="#9C9EA4", width=2),
    name="Industry Median"
))

fig_eff.update_layout(
    height=450,
    xaxis_title="Company",
    yaxis_title="Total Profit per 1% Market Share (SEK)",
    plot_bgcolor="white",
    showlegend=True
)

st.plotly_chart(fig_eff, use_container_width=True)


st.markdown(
    f"**Profit Efficiency Distribution (2021–2024):** "
    f"The industry median profit capture per 1% market share stands at "
    f"**{industry_median_eff:,.0f} SEK**, with "
    f"**{above_eff.shape[0]} out of {eff_df.shape[0]} firms** operating "
    f"above this structural benchmark."
)


# -------------------------------------------------
# Structural Profit Efficiency Model (Regression Benchmark)
# -------------------------------------------------

st.markdown("---")
st.subheader("Structural Profit Efficiency Model (Regression Benchmark)")

# Use same aggregation logic as efficiency section
reg_df = (
    df.groupby("company")
    .agg(
        total_profit=("ebitda", "sum"),
        avg_market_share=("market_share", "mean")
    )
    .reset_index()
)

reg_df = reg_df[reg_df["avg_market_share"] > 0]

# Linear regression: Profit ~ Market Share
coef = np.polyfit(reg_df["avg_market_share"], reg_df["total_profit"], 1)
reg_df["expected_profit"] = np.polyval(coef, reg_df["avg_market_share"])

# Structural alpha (residual)
reg_df["residual"] = reg_df["total_profit"] - reg_df["expected_profit"]

# Model fit
corr_reg = np.corrcoef(reg_df["avg_market_share"], reg_df["total_profit"])[0, 1]
r2_reg = corr_reg ** 2

reg_df = reg_df.sort_values("residual", ascending=False)

# Split outperformers and underperformers
above_reg = reg_df[reg_df["residual"] >= 0]
below_reg = reg_df[reg_df["residual"] < 0]

fig_reg = go.Figure()

# Above expected (structural alpha)
fig_reg.add_trace(go.Bar(
    x=above_reg["company"],
    y=above_reg["residual"],
    marker_color="#5A6F89",
    name="Above Expected (Structural Alpha)",
    text=above_reg["residual"],
    texttemplate="+%{text:,.0f}",
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Residual vs Expected: +%{y:,.0f} SEK<extra></extra>"
))

# Below expected
fig_reg.add_trace(go.Bar(
    x=below_reg["company"],
    y=below_reg["residual"],
    marker_color="#F28B82",
    name="Below Expected",
    text=below_reg["residual"],
    texttemplate="%{text:,.0f}",
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Residual vs Expected: %{y:,.0f} SEK<extra></extra>"
))

# Zero baseline
fig_reg.add_shape(
    type="line",
    x0=-0.5,
    x1=len(reg_df["company"]) - 0.5,
    y0=0,
    y1=0,
    line=dict(color="#9C9EA4", width=2)
)

fig_reg.update_layout(
    height=450,
    xaxis_title="Company",
    yaxis_title="Structural Profit Alpha (SEK)",
    plot_bgcolor="white",
    legend=dict(
        orientation="v",
        y=1,
        x=1.02
    )
)

st.plotly_chart(fig_reg, use_container_width=True)


st.markdown(
    f"**Structural Profit Efficiency (Regression Benchmark, 2021–2024):** "
    f"Expected profit is estimated based on structural market share. "
    f"The model exhibits a correlation of **{corr_reg:.2f}** and an R² of **{r2_reg:.2f}**, "
    f"with positive residuals indicating structural alpha."
)


# -------------------------------------------------
# Scale Elasticity Model (Log–Log Regression)
# -------------------------------------------------

st.markdown("---")
st.subheader("Scale Elasticity Model (Log–Log Regression)")

log_df = (
    df.groupby("company")
    .agg(
        total_profit=("ebitda", "sum"),
        avg_market_share=("market_share", "mean")
    )
    .reset_index()
)

# Remove non-positive values for log transformation
log_df = log_df[(log_df["total_profit"] > 0) & (log_df["avg_market_share"] > 0)]

# Log transformation
log_df["log_profit"] = np.log(log_df["total_profit"])
log_df["log_share"] = np.log(log_df["avg_market_share"])

# Log–log regression
coef_log = np.polyfit(log_df["log_share"], log_df["log_profit"], 1)
beta_elasticity = coef_log[0]

log_df["expected_log_profit"] = np.polyval(coef_log, log_df["log_share"])
log_df["expected_profit"] = np.exp(log_df["expected_log_profit"])

# Structural alpha (elasticity-adjusted residual)
log_df["residual"] = log_df["total_profit"] - log_df["expected_profit"]


corr_log = np.corrcoef(log_df["log_share"], log_df["log_profit"])[0, 1]
r2_log = corr_log ** 2

# -------------------------------------------------
# Log–Log Regression Scatter Plot
# -------------------------------------------------

fig_log_scatter = go.Figure()

# Scatter points
fig_log_scatter.add_trace(go.Scatter(
    x=log_df["log_share"],
    y=log_df["log_profit"],
    mode="markers",
    text=log_df["company"],
    marker=dict(size=14, color="#5A6F89"),
    hovertemplate="<b>%{text}</b><br>log(Market Share): %{x:.3f}<br>log(Profit): %{y:.3f}<extra></extra>"
))

# Regression line (sorted for clean line rendering)
sorted_df = log_df.sort_values("log_share")

fig_log_scatter.add_trace(go.Scatter(
    x=sorted_df["log_share"],
    y=np.polyval(coef_log, sorted_df["log_share"]),
    mode="lines",
    line=dict(color="#F28B82", width=2),
    name="Log–Log Regression Line"
))

fig_log_scatter.update_layout(
    height=450,
    xaxis_title="log(Average Market Share)",
    yaxis_title="log(Total Profit)",
    plot_bgcolor="white",
    showlegend=False
)

st.plotly_chart(fig_log_scatter, use_container_width=True)

log_df = log_df.sort_values("residual", ascending=False)

above_log = log_df[log_df["residual"] >= 0]
below_log = log_df[log_df["residual"] < 0]

fig_log = go.Figure()

# Above expected (elasticity-adjusted alpha)
fig_log.add_trace(go.Bar(
    x=above_log["company"],
    y=above_log["residual"],
    marker_color="#5A6F89",
    name="Above Expected (Elasticity Alpha)",
    text=above_log["residual"],
    texttemplate="+%{text:,.0f}",
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Elasticity Alpha: +%{y:,.0f} SEK<extra></extra>"
))

# Below expected
fig_log.add_trace(go.Bar(
    x=below_log["company"],
    y=below_log["residual"],
    marker_color="#F28B82",
    name="Below Expected",
    text=below_log["residual"],
    texttemplate="%{text:,.0f}",
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Elasticity Alpha: %{y:,.0f} SEK<extra></extra>"
))

# Zero baseline
fig_log.add_shape(
    type="line",
    x0=-0.5,
    x1=len(log_df["company"]) - 0.5,
    y0=0,
    y1=0,
    line=dict(color="#9C9EA4", width=2)
)

fig_log.update_layout(
    height=450,
    xaxis_title="Company",
    yaxis_title="Elasticity-Adjusted Structural Alpha (SEK)",
    plot_bgcolor="white",
    legend=dict(
        orientation="v",
        y=1,
        x=1.02
    )
)

st.plotly_chart(fig_log, use_container_width=True)

st.markdown(
    f"**Scale Elasticity (Log–Log Model, 2021–2024):** "
    f"The estimated elasticity of profit to scale (β) is **{beta_elasticity:.2f}**, "
    f"with a correlation of **{corr_log:.2f}** and an R² of **{r2_log:.2f}**. "
    f"Positive residuals indicate firms outperforming proportional scale expectations."
)


# -------------------------------------------------
# Margin Driver Decomposition (EBITDA vs Revenue Growth)
# -------------------------------------------------

st.markdown("---")
st.subheader("Margin Driver Decomposition (2021–2024)")

driver_df = (
    df.groupby("company")
    .agg(
        revenue_cagr=("CAGR_21_24", "first"),
        ebitda_start=("ebitda", "first"),
        ebitda_end=("ebitda", "last")
    )
    .reset_index()
)


# Robust EBITDA growth calculation
def compute_ebitda_cagr(row):
    start = row["ebitda_start"]
    end = row["ebitda_end"]

    # If both positive → standard CAGR
    if start > 0 and end > 0:
        return (end / start) ** (1/3) - 1

    # If start is zero → fallback to simple average growth proxy
    if start == 0:
        return 0

    # If negative involved → use linear annualised growth proxy
    return (end - start) / abs(start) / 3

driver_df["ebitda_cagr"] = driver_df.apply(compute_ebitda_cagr, axis=1)

driver_df["margin_expansion_proxy"] = (
    driver_df["ebitda_cagr"] - driver_df["revenue_cagr"]
)
# Ensure no company is dropped due to NaN
driver_df["margin_expansion_proxy"] = driver_df["margin_expansion_proxy"].fillna(0)

driver_df = driver_df.sort_values("margin_expansion_proxy", ascending=False)

fig_driver = go.Figure()

# Split positive and negative performers
positive_driver = driver_df[driver_df["margin_expansion_proxy"] >= 0]
negative_driver = driver_df[driver_df["margin_expansion_proxy"] < 0]

# Positive (above 0) – silver blue
fig_driver.add_trace(go.Bar(
    x=positive_driver["company"],
    y=positive_driver["margin_expansion_proxy"] * 100,
    marker_color="#5A6F89",
    name="Margin Expansion",
    hovertemplate="<b>%{x}</b><br>Margin Expansion Proxy: %{y:.2f}%<extra></extra>"
))

# Negative (below 0) – orange
fig_driver.add_trace(go.Bar(
    x=negative_driver["company"],
    y=negative_driver["margin_expansion_proxy"] * 100,
    marker_color="#F28B82",
    name="Margin Compression",
    hovertemplate="<b>%{x}</b><br>Margin Expansion Proxy: %{y:.2f}%<extra></extra>"
))

fig_driver.update_layout(
    height=450,
    xaxis_title="Company",
    yaxis_title="EBITDA CAGR minus Revenue CAGR (%)",
    legend=dict(
        orientation="v",
        y=1,
        x=1.02
    ),
    plot_bgcolor="white"
)

st.plotly_chart(fig_driver, use_container_width=True)

st.markdown(
    f"**Margin Driver Decomposition (2021–2024):** "
    f"This proxy compares EBITDA CAGR to revenue CAGR to assess operational leverage. "
    f"Positive values indicate margin expansion, while negative values suggest margin compression."
)

# -------------------------------------------------
# Public Dashboard Disclaimer
# -------------------------------------------------
st.markdown("---")
st.markdown(
    "**This dashboard presents analytical insights derived from publicly available financial data. "
    "It is intended for informational and exploratory purposes only and does not constitute financial advice.**<br>"
    "**Comprehensive firm-level analytical reports are available upon request.**",
    unsafe_allow_html=True
)