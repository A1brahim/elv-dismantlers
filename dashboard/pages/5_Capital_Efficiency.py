import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import sys
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

import numpy as np
from scipy.stats import pearsonr

from src.metrics.capital_efficiency import (
    compute_asset_turnover,
    compute_industry_capital_structure,
    compute_latest_year_ranking,
    compute_scale_efficiency_map,
    compute_structural_capital_efficiency,
)

st.set_page_config(layout="wide")

st.title("Capital Efficiency (Asset Turnover)")

# -------------------------------------------------
# Load Data
# -------------------------------------------------

@st.cache_data
def load_data():
    return pd.read_csv("dashboard/balance_sheet_yearly.csv")

df = load_data()

# -------------------------------------------------
# Compute Capital Efficiency Metrics
# -------------------------------------------------

df = compute_asset_turnover(df)
industry_structure = compute_industry_capital_structure(df)
latest_ranking, latest_year = compute_latest_year_ranking(df)
scale_eff_df = compute_scale_efficiency_map(df)

# Structural Capital Efficiency (Mean + Drift)
structural_df, industry_mean_structural = compute_structural_capital_efficiency(df)

# -------------------------------------------------
# Structural Overview Summary
# -------------------------------------------------

avg_turnover = industry_structure["mean_asset_turnover"].mean()
latest_mean = industry_structure.loc[
    industry_structure["year"] == latest_year, "mean_asset_turnover"
].values[0]

drift_direction = (
    "improving"
    if industry_structure["structural_drift"].iloc[-1] > 0
    else "softening"
)

st.markdown(
    f"**Capital Efficiency Overview:** "
    f"Average asset turnover (2021–{latest_year}) measured {avg_turnover:.2f}. "
    f"In {latest_year}, industry mean turnover stood at {latest_mean:.2f}. "
    f"Recent structural drift suggests capital productivity is {drift_direction}."
)

# -------------------------------------------------
# Latest-Year Ranking
# -------------------------------------------------

st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        Capital Efficiency Ranking 
    <div style="font-size:1.2rem; color:#6B7280; margin-top:0;">
        Latest: {latest_year}
    </div>
    """,
    unsafe_allow_html=True
)

latest_ranking["performance_flag"] = latest_ranking["asset_turnover"].apply(
    lambda x: "Above Industry Mean" if x >= latest_mean else "Below Industry Mean"
)

color_map = {
    "Above Industry Mean": "#5A6F89",
    "Below Industry Mean": "#F28B82",
}

fig_rank = px.bar(
    latest_ranking,
    x="asset_turnover",
    y="company",
    orientation="h",
    color="performance_flag",
    color_discrete_map=color_map,
    hover_data={
        "asset_turnover": ":.2f",
        "performance_flag": False,
    },
)

fig_rank.update_traces(
    hovertemplate="<b>%{y}</b><br>Capital Efficiency (Asset Turnover): %{x:.2f}<extra></extra>"
)

fig_rank.add_vline(
    x=latest_mean,
    line_width=2,
    line_color="#9C9EA4",
    annotation_text="Industry Mean",
    annotation_position="top"
)

fig_rank.update_layout(
    yaxis=dict(categoryorder="total ascending", title="Company"),
    xaxis=dict(title="Capital Efficiency (Asset Turnover)"),
    height=500,
    legend_title_text="Performance vs Industry Mean"
)

st.plotly_chart(fig_rank, use_container_width=True)

# Summary under ranking
st.markdown(
    f"**Capital Efficiency Ranking ({latest_year}):** "
    f"In {latest_year}, the industry mean asset turnover was {latest_mean:.2f}. "
    f"Firms above this level demonstrate stronger capital efficiency, "
    f"while those below operate with weaker asset utilisation."
)


# -------------------------------------------------
# Firm-Level Structural Efficiency (Mean ± Volatility)
# -------------------------------------------------

st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        Capital Efficiency (Mean ± Volatility)
    <div style="font-size:1.2rem; color:#6B7280; margin-top:0;">
        Multi-Year Profile (2021–Latest)
    </div>
    """,
    unsafe_allow_html=True
)

firm_stats = (
    df.groupby("company")
    .agg(
        mean_asset_turnover=("asset_turnover", "mean"),
        turnover_volatility=("asset_turnover", "std"),
        mean_total_assets=("total_assets", "mean"),
    )
    .reset_index()
)

# Sort firms by total asset size (descending)
firm_stats = firm_stats.sort_values("mean_total_assets", ascending=False)

# Performance flag relative to structural industry mean
firm_stats["performance_flag"] = firm_stats["mean_asset_turnover"].apply(
    lambda x: "Above Industry Mean"
    if x >= industry_mean_structural
    else "Below Industry Mean"
)

color_map = {
    "Above Industry Mean": "#5A6F89",
    "Below Industry Mean": "#F28B82",
}

fig_whisker = px.scatter(
    firm_stats,
    x="company",
    y="mean_asset_turnover",
    error_y="turnover_volatility",
    color="performance_flag",
    color_discrete_map=color_map,
)

# Customise hover tooltip to show only Company Name and Mean ± Volatility (2 d.p.)
fig_whisker.update_traces(
    hovertemplate="<b>%{x}</b><br>"
                  "Mean: %{y:.2f} ± %{error_y.array:.2f}"
                  "<extra></extra>"
)

# -------------------------------------------------
# Visual Asset Size Bar (indicating sorting from large to small)
# -------------------------------------------------

# Normalize asset size for visual scaling
max_assets = firm_stats["mean_total_assets"].max()
firm_stats["asset_size_scaled"] = (
    firm_stats["mean_total_assets"] / max_assets
)

# Create subtle bar at bottom of chart to indicate asset magnitude
fig_whisker.add_bar(
    x=firm_stats["company"],
    y=firm_stats["asset_size_scaled"],  # full 0–1 normalised scale
    base=0.00,
    marker=dict(color="#F5970C"),
    opacity=0.25,
    name="Relative Asset Size (Normalised to Largest Firm)",
    legendgroup="asset_size",
    showlegend=True,
    hoverinfo="skip",
)

# Horizontal industry mean line
fig_whisker.add_hline(
    y=industry_mean_structural,
    line_width=2,
    line_color="#9C9EA4",
    annotation_text="Industry Mean",
    annotation_position="top right"
)

fig_whisker.update_layout(
    height=500,
    xaxis=dict(title="Company"),
    yaxis=dict(
        title="Capital Efficiency (Mean ± Volatility)",
        range=[0.0, max(3.5, structural_df["mean_asset_turnover"].max() + 1)],
        tickmode="linear",
        dtick=0.5
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    legend_title_text="Performance vs Industry Mean"
)

st.plotly_chart(fig_whisker, use_container_width=True)

st.markdown(
    "**Firm-Level Capital Efficiency (2021–Latest):** "
    "Each point represents the firm's average capital efficiency over 2021–Latest. "
    "Whiskers reflect volatility (standard deviation) across the period. "
        "Firms are ordered by average total asset size over the period of analysis (2021–Latest). "
    "The faint lower bar visualises relative asset magnitude, normalised to the largest firm in the sample. "
    "Colour indicates positioning versus the industry mean."
)


# -------------------------------------------------
# Industry Structural Dynamics
# -------------------------------------------------

st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        Industry Capital Efficiency Over Time
    <div style="font-size:1.2rem; color:#6B7280; margin-top:0;">
        Multi-Year Industry Performance (2021–Latest)
    </div>
    """,
    unsafe_allow_html=True
)

fig_line = go.Figure()

# Mean line
fig_line.add_trace(
    go.Scatter(
        x=industry_structure["year"],
        y=industry_structure["mean_asset_turnover"],
        mode="lines+markers",
        name="Industry Mean",
        line=dict(color="#4C78A8", width=3),
    )
)

# Dispersion band (±1 std)
fig_line.add_trace(
    go.Scatter(
        x=industry_structure["year"],
        y=industry_structure["mean_asset_turnover"] + industry_structure["dispersion"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
    )
)

fig_line.add_trace(
    go.Scatter(
        x=industry_structure["year"],
        y=industry_structure["mean_asset_turnover"] - industry_structure["dispersion"],
        mode="lines",
        fill="tonexty",
        fillcolor="rgba(76,120,168,0.15)",
        line=dict(width=0),
        name="Dispersion (±1σ)",
    )
)

fig_line.update_layout(
    height=400,
    xaxis=dict(
        title="Year",
        tickmode="array",
        tickvals=[2020, 2021, 2022, 2023, 2024, 2025],
        range=[2020, 2025]
    ),
    yaxis=dict(
        title="Capital Efficiency (Asset Turnover)",
        range=[0.5, 3],
        tickmode="array",
        tickvals=[0.5, 1, 1.5, 2, 2.5, 3]
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
)

st.plotly_chart(fig_line, use_container_width=True)

# Summary under time series
avg_dispersion = industry_structure["dispersion"].mean()

st.markdown(
    f"**Industry Trend (2021–{latest_year}):** "
    f"Average asset turnover across the industry was {avg_turnover:.2f}. "
    f"Average cross-sectional dispersion measured {avg_dispersion:.2f}, "
    f"indicating the degree of efficiency divergence between firms."
)

# -------------------------------------------------
# Scale vs Efficiency Map
# -------------------------------------------------

st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        Firm Size vs Capital Efficiency
    <div style="font-size:1.2rem; color:#6B7280; margin-top:0;">
        Latest Year ({latest_year})
    </div>
    """,
    unsafe_allow_html=True
)


latest_scatter = scale_eff_df[scale_eff_df["year"] == latest_year]

# Compute correlation between firm size and asset turnover (latest year)
# Using log-transformed total assets to account for scale differences
valid_data = latest_scatter.dropna(subset=["total_assets", "asset_turnover"])

if len(valid_data) > 1:
    log_assets = np.log(valid_data["total_assets"])
    size_turnover_corr, size_turnover_pval = pearsonr(
        log_assets, valid_data["asset_turnover"]
    )
else:
    size_turnover_corr, size_turnover_pval = np.nan, np.nan

latest_scatter["performance_flag"] = latest_scatter["asset_turnover"].apply(
    lambda x: "Above Industry Turnover Mean" if x >= latest_mean else "Below Industry Turnover Mean"
)

color_map = {
    "Above Industry Turnover Mean": "#5A6F89",
    "Below Industry Turnover Mean": "#F28B82",
}

fig_scatter = px.scatter(
    latest_scatter,
    x="total_assets",
    y="asset_turnover",
    size="total_assets",
    hover_name="company",
    hover_data=None,
    color="performance_flag",
    color_discrete_map=color_map,
)

fig_scatter.update_traces(
    hovertemplate="<b>%{hovertext}</b><extra></extra>"
)

fig_scatter.add_hline(
    y=latest_mean,
    line_width=2,
    line_color="#9C9EA4",
    annotation_text="Industry Turnover Mean",
    annotation_position="top right"
)

mean_assets = latest_scatter["total_assets"].mean()

fig_scatter.add_vline(
    x=mean_assets,
    line_width=2,
    line_color="#9C9EA4",
    annotation_text="Industry Assets Mean",
    annotation_position="top right"
)

fig_scatter.update_layout(
    height=450,
    xaxis=dict(title="Total Assets (Capital Base)"),
    yaxis=dict(
        title="Capital Efficiency (Asset Turnover)",
        range=[0.5, 3],
        tickmode="array",
        tickvals=[0.5, 1, 1.5, 2, 2.5, 3]
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    legend_title_text="Performance vs Industry Mean"
)

st.plotly_chart(fig_scatter, use_container_width=True)

# Summary under scatter
st.markdown(
    f"**Total Assets vs Capital Efficiency ({latest_year}):** "
    f"Firms in the upper-right quadrant combine scale and strong capital productivity, "
    f"while those below the horizontal mean line operate with weaker asset utilisation. "
    f"With a limited cross-sectional sample (n = {len(valid_data)}), "
    f"no statistically meaningful inference can be drawn regarding the structural "
    f"relationship between scale and capital productivity."
)

# -------------------------------------------------
# Structural Capital Efficiency (Mean + Drift)
# -------------------------------------------------

st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        Capital Efficiency Positioning (Level and Directional Drift)
    <div style="font-size:1.2rem; color:#6B7280; margin-top:0;">
        Multi-Year Firm Performance (2021–Latest)
    </div>
    """,
    unsafe_allow_html=True
)


structural_df["performance_flag"] = structural_df["mean_asset_turnover"].apply(
    lambda x: "Above Industry Mean Turnover"
    if x >= industry_mean_structural
    else "Below Industry Mean Turnover"
)

fig_struct = px.scatter(
    structural_df,
    x="mean_asset_turnover",
    y="structural_drift",
    color="performance_flag",
    color_discrete_map={
        "Above Industry Mean Turnover": "#5A6F89",
        "Below Industry Mean Turnover": "#F28B82",
    },
    hover_name="company",
)

fig_struct.update_traces(
    hovertemplate="<b>%{hovertext}</b><extra></extra>"
)

fig_struct.add_vline(
    x=industry_mean_structural,
    line_width=2,
    line_color="#9C9EA4",
    annotation_text="Industry Mean Turnover",
    annotation_position="top right"
)

fig_struct.add_hline(
    y=0,
    line_width=2,
    line_color="#9C9EA4",
    annotation_text="Neutral Drift (0)",
    annotation_position="bottom right"
)

fig_struct.update_layout(
    height=500,
    xaxis=dict(title="Mean Asset Turnover (2021–Latest)"),
    yaxis=dict(title="Structural Drift (Slope per Year)"),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    legend_title_text="Performance vs Industry Turnover Mean"
)

st.plotly_chart(fig_struct, use_container_width=True)

st.markdown(
    "**Capital Efficiency Performance Trend (2021–Latest):** "
    "Structural drift is calculated as the linear regression slope "
    "of asset turnover against time (2021–Latest), capturing the "
    "annual directional change in capital efficiency. "
    "Upper-right quadrant firms combine high average capital productivity "
    "with improving structural drift. Lower-left positioning reflects "
    "persistent structural weakness."
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