import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from src.metrics.operating_efficiency import (
    compute_operating_margin,
    compute_industry_operating_structure,
    compute_latest_operating_margin_ranking,
    compute_structural_operating_efficiency,
    compute_capital_productivity,
    compute_return_metrics,
    compute_structural_return_metrics
)

st.set_page_config(layout="wide")
st.title("Operating Efficiency")

# -------------------------------------------------
# Load Data
# -------------------------------------------------

@st.cache_data
def load_data():
    return pd.read_csv("dashboard/balance_sheet_yearly.csv")

df = load_data()
df = compute_operating_margin(df)

industry_structure = compute_industry_operating_structure(df)
latest_ranking, latest_year = compute_latest_operating_margin_ranking(df)
structural_df, industry_mean_structural = compute_structural_operating_efficiency(df)

# -------------------------------------------------
# Structural Overview
# -------------------------------------------------

avg_margin = industry_structure["mean_operating_margin"].mean()
latest_mean = industry_structure.loc[
    industry_structure["year"] == latest_year,
    "mean_operating_margin",
].values[0]

drift_direction = (
    "improving"
    if industry_structure["structural_drift"].iloc[-1] > 0
    else "softening"
)

st.markdown(
    f"**Operating Efficiency Overview:** "
    f"Average operating margin (2021–{latest_year}) measured {avg_margin:.2%}. "
    f"In {latest_year}, industry mean margin stood at {latest_mean:.2%}. "
    f"Recent structural drift suggests operating efficiency is {drift_direction}."
)

# -------------------------------------------------
# Latest-Year Ranking
# -------------------------------------------------

st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        Operating Margin Ranking
    </h2>
    <div style="font-size:1.2rem; color:#6B7280; margin-top:0;">
        Latest Year: {latest_year}
    </div>
    """,
    unsafe_allow_html=True
)

latest_ranking["performance_flag"] = latest_ranking["operating_margin"].apply(
    lambda x: "Above Industry Mean"
    if x >= latest_mean
    else "Below Industry Mean"
)

fig_rank = px.bar(
    latest_ranking.sort_values("operating_margin"),
    x="operating_margin",
    y="company",
    orientation="h",
    color="performance_flag",
    color_discrete_map={
        "Above Industry Mean": "#5A6F89",
        "Below Industry Mean": "#F28B82",
    },
)

fig_rank.update_traces(
    hovertemplate="<b>%{y}</b><br>Operating Margin: %{x:.2%}<extra></extra>"
)

fig_rank.add_vline(
    x=latest_mean,
    line_width=2,
    line_color="#9C9EA4",
)

fig_rank.update_layout(
    height=500,
    xaxis=dict(title="Operating Margin"),
    yaxis=dict(title="Company"),
    legend_title_text="Performance vs Industry Mean",
)

st.plotly_chart(fig_rank, use_container_width=True)

st.markdown(
    f"**Operating Margin Ranking ({latest_year}):** "
    f"In {latest_year}, the industry mean operating margin stood at {latest_mean:.2%}. "
    "Firms above this threshold demonstrate stronger operating efficiency, "
    "while those below operate with comparatively thinner margins."
)

# -------------------------------------------------
# Firm-Level Mean ± Volatility
# -------------------------------------------------

st.markdown(
    """
    <h2 style="margin-bottom:0;">
        Operating Margin (Mean ± Volatility)
    </h2>
    <div style="font-size:1.05rem; color:#6B7280;">
        Multi-Year  Performance (2021–Latest)
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------
# Prepare Data
# -------------------------------------------------

# Normalise relative to largest firm
structural_df["relative_asset_size"] = (
    structural_df["mean_total_assets"] /
    structural_df["mean_total_assets"].max()
)

# Colour positioning
structural_df["performance_flag"] = structural_df["mean_operating_margin"].apply(
    lambda x: "Above Industry Mean"
    if x >= industry_mean_structural
    else "Below Industry Mean"
)

# -------------------------------------------------
# Firm-Level Mean ± Volatility
# -------------------------------------------------

# Sort by average asset size (decending)
ordered_df = structural_df.sort_values("mean_total_assets", ascending=False)

company_order = ordered_df["company"].tolist()

fig_whisker = px.scatter(
    ordered_df,
    x="company",
    y="mean_operating_margin",
    error_y="margin_volatility",
    color="performance_flag",
    color_discrete_map={
        "Above Industry Mean": "#5A6F89",
        "Below Industry Mean": "#F28B82",
    },
    category_orders={"company": company_order},
)

# ---- Scatter hover (mean ± volatility only)
fig_whisker.update_traces(
    selector=dict(mode="markers"),
    hovertemplate="<b>%{x}</b><br>"
                  "Mean Margin: %{y:.2%} ± %{error_y.array:.2%}"
                  "<extra></extra>"
)

# ---- Asset-size bars (custom hover)
fig_whisker.add_bar(
    x=company_order,
    y=ordered_df["relative_asset_size"] * 0.1,
    marker_color="#F5970C",
    opacity=0.5,
    name="Relative Asset Size (Normalised)",
    hovertemplate="<b>%{x}</b><br>"
                  "Relative Asset Size: %{y:.2f} (scaled)"
                  "<extra></extra>"
)

fig_whisker.add_hline(
    y=industry_mean_structural,
    line_width=2,
    line_color="#9C9EA4",
)

fig_whisker.update_layout(
    height=550,
    xaxis=dict(title="Company"),
    yaxis=dict(title="Operating Margin (Mean ± Volatility)"),
    legend_title_text="Performance vs Industry Mean",
)

st.plotly_chart(fig_whisker, use_container_width=True)

st.markdown(
    "**Firm-Level Operating Efficiency (2021–Latest):** "
    "Each point represents the firm's average operating margin over the analysis period. "
    "Whiskers reflect volatility (standard deviation). Firms are ordered by average asset size, "
    "while the faint lower bar visualises relative asset magnitude, normalised to the largest firm. "
    "Colour indicates positioning versus the industry mean."
)

# -------------------------------------------------
# Industry Structural Dynamics
# -------------------------------------------------

st.markdown(
    """
    <h2 style="margin-bottom:0;">
        Industry Operating Margin Over Time
    </h2>
    <div style="font-size:1.05rem; color:#6B7280;">
        Multi-Year Industry Performance (2021–Latest)
    </div>
    """,
    unsafe_allow_html=True
)

fig_line = go.Figure()

# Industry Mean Line
fig_line.add_trace(
    go.Scatter(
        x=industry_structure["year"],
        y=industry_structure["mean_operating_margin"],
        mode="lines+markers",
        name="Industry Mean",
        line=dict(color="#4C78A8", width=2),
        marker=dict(color="#4C78A8"),
    )
)

# Upper bound (mean + dispersion)
fig_line.add_trace(
    go.Scatter(
        x=industry_structure["year"],
        y=industry_structure["mean_operating_margin"] + industry_structure["dispersion"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
    )
)

# Lower bound (mean - dispersion) with fill
fig_line.add_trace(
    go.Scatter(
        x=industry_structure["year"],
        y=industry_structure["mean_operating_margin"] - industry_structure["dispersion"],
        mode="lines",
        fill="tonexty",
        fillcolor="rgba(76,120,168,0.15)",
        line=dict(width=0),
        name="Dispersion (±1σ)",
    )
)

fig_line.update_layout(
    height=500,
    
    # Axis formatting
    xaxis=dict(
        title="Year",
        range=[2020, 2025],
        tickmode="linear",
        dtick=1
    ),
    yaxis=dict(
        title="Operating Margin",
        tickformat=".00%"  # keeps it clean and consistent
    ),

    # Legend on top
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
)

st.plotly_chart(fig_line, use_container_width=True)

st.markdown(
    f"**Industry Trend (2021–{latest_year}):** "
    f"Average operating margin across the industry was {avg_margin:.2%}. "
    "Shaded bands reflect cross-sectional dispersion (±1σ), indicating "
    "the degree of performance divergence between firms over time."
)

# -------------------------------------------------
# Structural Positioning (Level + Drift)
# -------------------------------------------------


st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        Operating Margin Positioning (Level and Directional Drift)
    </h2>
    <div style="font-size:1.2rem; color:#6B7280; margin-top:0;">
        Multi-Year Firm Performance (2021–Latest)
    </div>
    """,
    unsafe_allow_html=True
)

# Performance flag
structural_df["performance_flag"] = structural_df[
    "mean_operating_margin"
].apply(
    lambda x: "Above Operating Margin Industry Mean"
    if x >= industry_mean_structural
    else "Below Operating Margin Industry Mean"
)

fig_struct = px.scatter(
    structural_df,
    x="mean_operating_margin",
    y="structural_drift",
    color="performance_flag",
    color_discrete_map={
        "Above Operating Margin Industry Mean": "#5A6F89",
        "Below Operating Margin Industry Mean": "#F28B82",
    },
    hover_name="company",
    category_orders={
        "performance_flag": [
            "Above Operating Margin Industry Mean",
            "Below Operating Margin Industry Mean",
        ]
    },
)

fig_struct.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>"
                  "Mean Margin: %{x:.2%}<br>"
                  "Structural Drift: %{y:.2%}"
                  "<extra></extra>"
)

# Vertical Industry Mean Line
fig_struct.add_vline(
    x=industry_mean_structural,
    line_width=2,
    line_color="#9C9EA4",
)

fig_struct.add_annotation(
    xref="x",          # stay aligned with industry mean value
    yref="paper",      # reference top of chart
    x=industry_mean_structural,
    y=1,               # top edge of plotting area
    text="Industry Mean Operating Margin",
    showarrow=False,
    xanchor="right",    # text appears to the right of the line
    yanchor="top",     # anchor text to the top
    xshift= -5,          # small horizontal offset
    font=dict(color="#6B7280")
)

# Horizontal Neutral Drift Line
fig_struct.add_hline(
    y=0,
    line_width=2,
    line_color="#9C9EA4",
)

fig_struct.add_annotation(
    xref="paper",     # <-- anchor to plot area (0 to 1)
    yref="y",         # <-- keep y in data coordinates
    x=1,              # <-- far right edge
    y=0,              # <-- zero drift line
    text="Zero Structural Drift",
    showarrow=False,
    xanchor="right",  # <-- align text to right boundary
    yanchor="bottom", # <-- place text above the line
    yshift=5,         # <-- small lift above line
    font=dict(color="#6B7280")
)

# Axis formatting
fig_struct.update_layout(
    height=550,
    xaxis=dict(
        title="Mean Operating Margin (2021–Latest)",
        tickformat=".0%"
    ),
    yaxis=dict(
        title="Structural Drift (Δ Margin Over Period)",
        tickformat=".0%"
    ),
    legend_title_text="Performance vs Industry Mean",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
)

st.plotly_chart(fig_struct, use_container_width=True)

st.markdown(
    """
**Operating Margin Positioning (2021–Latest):** Firms in the upper-right quadrant combine above-industry average margins with positive structural drift, while those below the horizontal line exhibit margin deterioration over the period.
"""
)

# -------------------------------------------------
# Capital Productivity Heat Map
# -------------------------------------------------

st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        Capital Productivity Matrix
    </h2>
    <div style="font-size:1.2rem; color:#6B7280; margin-top:0;">
        Asset Turnover × Operating Margin (Latest Year: {latest_year})
    </div>
    """,
    unsafe_allow_html=True
)

capital_df, cp_industry_mean, cp_year = compute_capital_productivity(df)

mean_turnover = capital_df["asset_turnover"].mean()
mean_margin = capital_df["operating_margin"].mean()

# Bubble size scaling
capital_df["bubble_size"] = (
    capital_df["capital_productivity"].abs()
    / capital_df["capital_productivity"].abs().max()
) * 45

fig_cp = px.scatter(
    capital_df,
    x="asset_turnover",
    y="operating_margin",
    size="bubble_size",
    color="capital_productivity",
    color_continuous_scale="RdBu",
    color_continuous_midpoint=cp_industry_mean,
    hover_name="company",
)

fig_cp.update_traces(
    hovertemplate="<b>%{hovertext}</b>"
    "<br>Asset Turnover: %{x:.2f}"
    "<br>Operating Margin: %{y:.2%}"
    "<br>Capital Productivity: %{marker.color:.3f}"
    "<extra></extra>"
)

# Quadrant reference lines (structural, not classificatory)
fig_cp.add_vline(x=mean_turnover, line_width=2, line_color="#9C9EA4")
fig_cp.add_hline(y=mean_margin, line_width=2, line_color="#9C9EA4")

# --- Vertical line label (Asset Turnover Mean) ---
fig_cp.add_annotation(
    x=mean_turnover,
    y=capital_df["operating_margin"].max(),
    text="Industry Avg Turnover",
    showarrow=False,
    xanchor="right",
    xshift=-5,
    yshift=10,
    font=dict(color="#6B7280", size=11),
    align="left"
)

# --- Horizontal line label (Operating Margin Mean) ---
fig_cp.add_annotation(
    x=capital_df["asset_turnover"].min(),
    y=mean_margin,
    text="Industry Avg Margin",
    showarrow=False,
    xshift=10,
    yshift=10,
    font=dict(color="#6B7280", size=11),
    align="left"
)


fig_cp.update_layout(
    height=550,
    xaxis=dict(title="Asset Turnover"),
    yaxis=dict(title="Operating Margin"),
    coloraxis_colorbar=dict(title="Capital Productivity"),
    plot_bgcolor="white"
)

st.plotly_chart(fig_cp, use_container_width=True)

st.markdown(
    f"**Capital Productivity ({latest_year}):** "
    "Color intensity reflects capital efficiency (Turnover × Margin), "
    "while bubble size represents magnitude. "
    "Reference lines indicate industry structural averages."
)

# -------------------------------------------------
# Return Metrics (ROA & EBITDA Margin)
# -------------------------------------------------

st.markdown("---")

st.markdown(
    f"""
    <h2 style="margin-bottom:0;">
        Return Metrics
    </h2>
    <div style="font-size:1.2rem; color:#6B7280; margin-top:0;">
        Firm Performance (Latest Year: {latest_year})
    </div>
    """,
    unsafe_allow_html=True
)

returns_df, industry_roa_mean, industry_ebitda_mean, return_year = compute_return_metrics(df)

# -------------------------------------------------
# ROA Ranking
# -------------------------------------------------

st.markdown("**Return on Assets (ROA)**")

returns_df["roa_flag"] = returns_df["roa"].apply(
    lambda x: "Above ROA Industry Mean"
    if x >= industry_roa_mean
    else "Below ROA Industry Mean"
)


roa_sorted = returns_df.sort_values("roa", ascending=True)

fig_roa = px.bar(
    roa_sorted,
    x="roa",
    y="company",
    orientation="h",
    color="roa_flag",
    color_discrete_map={
        "Above ROA Industry Mean": "#5A6F89",
        "Below ROA Industry Mean": "#F28B82",
    },
    category_orders={
        "company": roa_sorted["company"].tolist(),
        "roa_flag": [
            "Above ROA Industry Mean",
            "Below ROA Industry Mean",
        ],
    },
)

fig_roa.update_traces(
    hovertemplate="<b>%{y}</b><br>"
                  "ROA: %{x:.2%}<extra></extra>"
)

fig_roa.add_vline(
    x=industry_roa_mean,
    line_width=2,
    line_color="#9C9EA4",
)

fig_roa.add_annotation(
    xref="x",
    yref="paper",
    x=industry_roa_mean,
    y=1,
    text="Industry ROA Mean",
    showarrow=False,
    xanchor="left",
    yanchor="top",
    xshift=5,
    font=dict(color="#6B7280")
)

fig_roa.update_layout(
    height=450,
    xaxis=dict(
        title="Return on Assets",
        tickformat=".0%"
    ),
    yaxis=dict(title=""),
    legend_title_text="Performance vs Industry Mean",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
)

st.plotly_chart(fig_roa, use_container_width=True)

st.markdown(
    """
**Return on Assets (2024):** Firms to the right of the vertical reference line generate above-industry asset returns, while those to the left operate with weaker capital profitability.
"""
)

# -------------------------------------------------
# EBITDA Margin Ranking
# -------------------------------------------------

st.markdown("**EBITDA Margin**")

returns_df["ebitda_flag"] = returns_df["ebitda_margin"].apply(
    lambda x: "Above EBITDA Industry Mean"
    if x >= industry_ebitda_mean
    else "Below EBITDA Industry Mean"
)

ebitda_sorted = returns_df.sort_values("ebitda_margin", ascending=True)

fig_ebitda = px.bar(
    ebitda_sorted,
    x="ebitda_margin",
    y="company",
    orientation="h",
    color="ebitda_flag",
    color_discrete_map={
        "Above EBITDA Industry Mean": "#5A6F89",
        "Below EBITDA Industry Mean": "#F28B82",
    },
    category_orders={
        "company": ebitda_sorted["company"].tolist(),
        "ebitda_flag": [
            "Above EBITDA Industry Mean",
            "Below EBITDA Industry Mean",
        ],
    },
)

fig_ebitda.update_traces(
    hovertemplate="<b>%{y}</b><br>"
                  "EBITDA Margin: %{x:.2%}<extra></extra>"
)

fig_ebitda.add_vline(
    x=industry_ebitda_mean,
    line_width=2,
    line_color="#9C9EA4",
)

fig_ebitda.add_annotation(
    xref="x",
    yref="paper",
    x=industry_ebitda_mean,
    y=1,
    text="Industry EBITDA Margin Mean",
    showarrow=False,
    xanchor="left",
    yanchor="top",
    xshift=5,
    font=dict(color="#6B7280")
)

fig_ebitda.update_layout(
    height=450,
    xaxis=dict(
        title="EBITDA Margin",
        tickformat=".0%"
    ),
    yaxis=dict(title=""),
    legend_title_text="Performance vs Industry Mean",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
)

st.plotly_chart(fig_ebitda, use_container_width=True)

st.markdown(
    """
**EBITDA Margin (2024):** Firms above the industry benchmark demonstrate stronger operating cash-flow margins, whereas those below reflect weaker cost efficiency.
"""
)

# -------------------------------------------------
# Structural Return Metrics (Multi-Year View)
# -------------------------------------------------

st.markdown("---")
st.subheader("Structural Return Quality (Mean ± Volatility)")

structural_returns, industry_mean_roa, industry_mean_ebitda = compute_structural_return_metrics(df)

# --------------------------
# ROA Structural View
# --------------------------

st.markdown("**Structural ROA (Mean ± Volatility)**")

# -------------------------------------------------
# Merge structural mean asset size (over period)
# -------------------------------------------------

structural_roa = structural_returns.copy()

# -------------------------------------------------
# Normalise asset size (structural)
# -------------------------------------------------

structural_roa["relative_asset_size"] = (
    structural_roa["mean_total_assets"]
    / structural_roa["mean_total_assets"].max()
)

# -------------------------------------------------
# Flag performance vs industry mean
# -------------------------------------------------

structural_roa["roa_flag"] = structural_roa["mean_roa"].apply(
    lambda x: "Above Industry Mean"
    if x >= industry_mean_roa
    else "Below Industry Mean"
)

# -------------------------------------------------
# Rank by mean asset size (ascending)
# -------------------------------------------------

structural_roa = structural_roa.sort_values(
    "mean_total_assets",
    ascending=True
)

company_order = structural_roa["company"].tolist()

# -------------------------------------------------
# Scatter (Mean ± Volatility)
# -------------------------------------------------

fig_struct_roa = px.scatter(
    structural_roa,
    x="company",
    y="mean_roa",
    error_y="roa_volatility",
    color="roa_flag",
    color_discrete_map={
        "Above Industry Mean": "#5A6F89",
        "Below Industry Mean": "#F28B82",
    },
    category_orders={
        "company": company_order,
        "roa_flag": [
            "Above Industry Mean",
            "Below Industry Mean",
        ]
    },
)

fig_struct_roa.update_traces(
    hovertemplate="<b>%{x}</b><br>"
                  "Mean ROA: %{y:.2%} ± %{error_y.array:.2%}<br>"
                  "Mean Assets (2021–Latest): %{customdata[0]:,.0f}"
                  "<extra></extra>",
    customdata=structural_roa[["mean_total_assets"]]
)

# -------------------------------------------------
# Add faint structural asset bar
# -------------------------------------------------

fig_struct_roa.add_bar(
    x=company_order,
    y=structural_roa["relative_asset_size"] * 0.1,
    marker_color="#F5970C",
    opacity=0.35,
    name="Relative Mean Asset Size (2021–Latest)",
    hovertemplate="<b>%{x}</b><br>"
                  "Relative Mean Asset Size: %{y:.2f} (scaled)"
                  "<extra></extra>"
)

# -------------------------------------------------
# Industry mean line
# -------------------------------------------------

fig_struct_roa.add_hline(
    y=industry_mean_roa,
    line_width=2,
    line_color="#9C9EA4",
)

fig_struct_roa.add_annotation(
    x=company_order[-1],
    y=industry_mean_roa,
    text="Industry Mean ROA",
    showarrow=False,
    xshift=10,
    yshift=-10,
    font=dict(color="#6B7280")
)

# -------------------------------------------------
# Layout polish
# -------------------------------------------------

fig_struct_roa.update_layout(
    xaxis_title="Company (Ranked by Mean Asset Size)",
    yaxis_title="Mean ROA (± Volatility)",
    legend_title_text="Performance vs Industry Mean",
)

fig_struct_roa.update_yaxes(range=[-0.20, 0.4])

st.plotly_chart(fig_struct_roa, use_container_width=True)

# -------------------------------------------------
# Short Summary
# -------------------------------------------------

st.markdown(
"""
**Structural ROA:** Firms are ranked by average asset scale (2021–Latest). Points reflect mean return on assets, with whiskers indicating volatility. Firms above the reference line exhibit structurally stronger capital profitability. 
"""
)



# --------------------------
# EBITDA Structural View
# --------------------------

st.markdown("**Structural EBITDA Margin (Mean ± Volatility)**")

# Work directly from structural_returns (already enriched)
structural_ebitda = structural_returns.copy()

# -------------------------------------------------
# Flag vs industry mean
# -------------------------------------------------

structural_ebitda["ebitda_flag"] = structural_ebitda[
    "mean_ebitda_margin"
].apply(
    lambda x: "Above Industry Mean"
    if x >= industry_mean_ebitda
    else "Below Industry Mean"
)

# -------------------------------------------------
# Rank by mean revenue (NOT assets)
# -------------------------------------------------

structural_ebitda = structural_ebitda.sort_values(
    "mean_turnover",
    ascending=True
)

company_order = structural_ebitda["company"].tolist()

# -------------------------------------------------
# Scatter (Mean ± Volatility)
# -------------------------------------------------

fig_struct_ebitda = px.scatter(
    structural_ebitda,
    x="company",
    y="mean_ebitda_margin",
    error_y="ebitda_volatility",
    color="ebitda_flag",
    color_discrete_map={
        "Above Industry Mean": "#5A6F89",
        "Below Industry Mean": "#F28B82",
    },
    category_orders={
        "company": company_order,
        "ebitda_flag": [
            "Above Industry Mean",
            "Below Industry Mean",
        ]
    },
)

fig_struct_ebitda.update_traces(
    hovertemplate="<b>%{x}</b><br>"
                  "Mean EBITDA Margin: %{y:.2%} ± %{error_y.array:.2%}<br>"
                  "Mean Revenue (2021–Latest): %{customdata[0]:,.0f}"
                  "<extra></extra>",
    customdata=structural_ebitda[["mean_turnover"]]
)

# -------------------------------------------------
# Add faint revenue bar (not asset bar)
# -------------------------------------------------

fig_struct_ebitda.add_bar(
    x=company_order,
    y=structural_ebitda["relative_revenue_size"] * 0.1,
    marker_color="#F5970C",
    opacity=0.35,
    name="Relative Mean Revenue (2021–Latest)",
    hovertemplate="<b>%{x}</b><br>"
                  "Relative Mean Revenue: %{y:.2f} (scaled)"
                  "<extra></extra>"
)

# -------------------------------------------------
# Industry mean line
# -------------------------------------------------

fig_struct_ebitda.add_hline(
    y=industry_mean_ebitda,
    line_width=2,
    line_color="#9C9EA4",
)

fig_struct_ebitda.add_annotation(
    x=company_order[-1],
    y=industry_mean_ebitda,
    text="Industry Mean EBITDA",
    showarrow=False,
    xshift=10,
    yshift=-10,
    font=dict(color="#6B7280")
)

# -------------------------------------------------
# Layout
# -------------------------------------------------

fig_struct_ebitda.update_layout(
    xaxis_title="Company (Ranked by Mean Revenue)",
    yaxis_title="Mean EBITDA Margin (± Volatility)",
    legend_title_text="Performance vs Industry Mean",
)

fig_struct_ebitda.update_yaxes(range=[-0.20, 0.4])

st.plotly_chart(fig_struct_ebitda, use_container_width=True)

# -------------------------------------------------
# Summary
# -------------------------------------------------

st.markdown(
"""
**Structural EBITDA Margin:** Firms are ranked by average revenue scale (2021–Latest). Points reflect mean operating margins, with whiskers indicating volatility. Firms above the benchmark demonstrate structurally stronger operating profitability.
"""
)


# --------------------------
# Structural Drift View
# --------------------------

st.subheader("Return Positioning (Level & Drift)")

structural_returns["roa_flag"] = structural_returns["mean_roa"].apply(
    lambda x: "Above Industry Mean"
    if x >= industry_mean_roa
    else "Below Industry Mean"
)

fig_drift = px.scatter(
    structural_returns,
    x="mean_roa",
    y="roa_structural_drift",
    color="roa_flag",
    hover_name="company",
    color_discrete_map={
        "Above Industry Mean": "#5A6F89",
        "Below Industry Mean": "#F28B82",
    },
    category_orders={
        "roa_flag": [
            "Above Industry Mean",
            "Below Industry Mean",
        ]
    },
)

fig_drift.add_vline(
    x=industry_mean_roa,
    line_width=2,
    line_color="#9C9EA4",
)

fig_drift.add_hline(
    y=0,
    line_width=2,
    line_color="#9C9EA4",
)

fig_drift.add_annotation(
    x=structural_returns["mean_roa"].max(),
    y=0,
    text="Zero Structural Drift",
    showarrow=False,
    xshift=10,
    yshift=-10,
    font=dict(color="#6B7280")
)

fig_drift.add_annotation(
    xref="x",
    yref="paper",
    x=industry_mean_roa,
    y=1,                 # top edge of plot area
    text="Industry Mean ROA",
    showarrow=False,
    xanchor="right",     # text sits to right of line
    yanchor="bottom",    # anchor bottom of text to y
    xshift=-5,
    yshift=5,
    font=dict(color="#6B7280")
)

fig_drift.update_layout(
    xaxis_title="Mean ROA (2021–Latest)",
    yaxis_title="Structural Drift (Δ ROA Over Period)"
)

fig_drift.update_yaxes(range=[-0.10, 0.10])

st.plotly_chart(fig_drift, use_container_width=True)

st.markdown(
"""
**Return Positioning:** Firms in the upper-right quadrant combine above-industry return levels with improving structural drift, while those below the horizontal axis reflect declining profitability momentum. Given the limited sample (n = 10), no statistically meaningful inference can be drawn regarding structural return persistence.
"""
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