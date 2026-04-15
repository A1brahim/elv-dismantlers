import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).resolve().parents[1]))


# --------------------------------------------------
# STANDARDISED COLOUR PALETTE
# --------------------------------------------------

PRIMARY_COLOR = "#5A6F89"
NEUTRAL_COLOR = "#9AA3AF"

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(layout="wide")

st.title("Balance Sheet Structural Analysis")
st.caption(
    "Capital structure, liquidity positioning and structural risk mapping "
    "based on overlap-year financial means."
)

# --------------------------------------------------
# PATH CONFIG
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_PATH = PROJECT_ROOT / "dashboard"

YEARLY_PATH = DASHBOARD_PATH / "balance_sheet_yearly.csv"

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data():
    return pd.read_csv(YEARLY_PATH)

yearly_df = load_data()

# --------------------------------------------------
# COMPANY-LEVEL MEANS (OVERLAP YEARS)
# --------------------------------------------------

mean_metrics = (
    yearly_df
    .groupby("company")
    .agg({
        "equity_ratio": "mean",
        "debt_ratio": "mean",
        "cash_liquidity": "mean",
        "current_assets": "mean",
        "current_liabilities": "mean",
        "equity": "mean",
        "total_assets": "mean"
    })
    .reset_index()
)

# Liquidity Ratio
mean_metrics["liquidity_ratio"] = (
    mean_metrics["current_assets"] /
    mean_metrics["current_liabilities"]
)

# Debt-to-Equity Ratio
mean_metrics["debt_to_equity"] = (
    (mean_metrics["debt_ratio"] / 100) /
    (mean_metrics["equity_ratio"] / 100)
)

# Convert to percentages
mean_metrics["equity_ratio"] *= 100
mean_metrics["debt_ratio"] *= 100

# --------------------------------------------------
# SECTION 1 — CAPITAL STRUCTURE POSITIONING
# --------------------------------------------------

st.header("Capital Structure Positioning")

view_option = st.radio(
    "Select Leverage Metric",
    ["Debt Ratio (%)", "Debt-to-Equity Ratio"],
    horizontal=True
)

if view_option == "Debt Ratio (%)":
    x_metric = "debt_ratio"
    x_label = "Debt Ratio (%)"
    industry_mean = mean_metrics["debt_ratio"].mean()
else:
    x_metric = "debt_to_equity"
    x_label = "Debt-to-Equity Ratio"
    industry_mean = mean_metrics["debt_to_equity"].mean()

# Conditional colouring: Above / Below Industry Mean (Leverage)
mean_metrics["Leverage Position"] = mean_metrics[x_metric].apply(
    lambda x: (
        f"Above Industry Mean<br>({x_label})"
        if x >= industry_mean
        else f"Below Industry Mean<br>({x_label})"
    )
)

fig1 = px.scatter(
    mean_metrics.round(2),
    x=x_metric,
    y="equity_ratio",
    size="total_assets",
    hover_name="company",
    color="Leverage Position",
    color_discrete_map={
        f"Above Industry Mean<br>({x_label})": "#5A6F89",
        f"Below Industry Mean<br>({x_label})": "#F28B82"
    },
    hover_data={
        "total_assets": ":,.0f",
        "equity_ratio": ":.1f",
        x_metric: ":.1f"
    },
    labels={
        x_metric: x_label,
        "equity_ratio": "Equity Ratio (%)",
        "total_assets": "Total Assets (SEK '000)"
    },
    title="Capital Structure Mapping"
)

# Industry mean lines
fig1.add_shape(
    type="line",
    x0=industry_mean,
    x1=industry_mean,
    y0=mean_metrics["equity_ratio"].min(),
    y1=mean_metrics["equity_ratio"].max(),
    line=dict(color="#9C9EA4", width=2)
)

# Annotation for vertical mean line
fig1.add_annotation(
    x=industry_mean,
    y=mean_metrics["equity_ratio"].max() + 3,
    text=f"Industry Mean<br>({x_label})",
    showarrow=False,
    align="center",
    font=dict(size=12, color="#9C9EA4")
)

# Compute equity mean before adding hline and annotations
equity_mean = mean_metrics["equity_ratio"].mean()

fig1.add_shape(
    type="line",
    x0=mean_metrics[x_metric].min(),
    x1=mean_metrics[x_metric].max(),
    y0=equity_mean,
    y1=equity_mean,
    line=dict(color="#9C9EA4", width=2)
)

# Annotation for horizontal equity mean line
fig1.add_annotation(
    x=mean_metrics[x_metric].max(),
    y=equity_mean - 4,
    text="Industry Mean<br>(Equity Ratio)",
    showarrow=False,
    align="right",
    xanchor="right",
    font=dict(size=12, color="#9C9EA4")
)


fig1.update_layout(height=600)

st.plotly_chart(fig1, use_container_width=True)
st.markdown(
    "<span style='font-size:12px; color:rgba(0,0,0,0.6);'>"
    "Bubble size represents average Total Assets (scale of company), "
    "calculated as the mean over the four overlapping years of investigation."
    "</span>",
    unsafe_allow_html=True
)

# Structured summary for Capital Structure Positioning
st.markdown(
    f"**Capital Structure Positioning (Overlap-Year Means):** "
    f"The industry average {x_label.lower()} stands at **{industry_mean:.2f}**, "
    f"while the average equity ratio is **{equity_mean:.2f}%**. "
    f"Firms positioned in the upper-left quadrant exhibit lower leverage and stronger capital buffers "
    f"relative to the industry mean."
)


highest = mean_metrics.loc[mean_metrics[x_metric].idxmax()]
lowest = mean_metrics.loc[mean_metrics[x_metric].idxmin()]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label=f"Highest {x_label}",
        value=highest["company"],
        delta=f"{highest[x_metric]:.2f}"
    )

with col2:
    st.metric(
        label=f"Lowest {x_label}",
        value=lowest["company"],
        delta=f"{lowest[x_metric]:.2f}"
    )

with col3:
    st.metric(
        label=f"Industry Average {x_label}",
        value=f"{industry_mean:.2f}"
    )

# --------------------------------------------------
# DEBT RATIO TIME SERIES (COMPANY + INDUSTRY)
# --------------------------------------------------

st.subheader("Debt Ratio Time Series (Company vs Industry)")

# Industry yearly statistics
industry_yearly = (
    yearly_df
    .groupby("year")["debt_ratio"]
    .agg(["mean", "std"])
    .reset_index()
)

industry_yearly["upper"] = industry_yearly["mean"] + industry_yearly["std"]
industry_yearly["lower"] = industry_yearly["mean"] - industry_yearly["std"]

fig_ts = go.Figure()

# Plot each company line
for company in yearly_df["company"].unique():
    company_df = yearly_df[yearly_df["company"] == company]
    fig_ts.add_trace(
        go.Scatter(
            x=company_df["year"],
            y=company_df["debt_ratio"],
            mode="lines+markers",
            line=dict(width=1.5, color=PRIMARY_COLOR),
            opacity=0.35,
            name=company,
            showlegend=False,
            text=[company] * len(company_df),
            hovertemplate="<b>%{text}</b><br>Year: %{x}<br>Debt Ratio: %{y:.2f}%<extra></extra>"
        )
    )

# Industry mean line
fig_ts.add_trace(
    go.Scatter(
        x=industry_yearly["year"],
        y=industry_yearly["mean"],
        mode="lines",
        line=dict(color="#5DADE2", width=2),
        name="Industry Average Debt Ratio",
        hovertemplate="Year: %{x}<br>Industry Avg: %{y:.2f}%<extra></extra>"
    )
)

# Volatility band
fig_ts.add_trace(
    go.Scatter(
        x=list(industry_yearly["year"]) + list(industry_yearly["year"][::-1]),
        y=list(industry_yearly["upper"]) + list(industry_yearly["lower"][::-1]),
        fill="toself",
        fillcolor="rgba(200,200,200,0.3)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip",
        name="Volatility Band (±1σ)"
    )
)

fig_ts.update_layout(
    height=500,
    xaxis=dict(
        title="Year",
        tickmode="array",
        tickvals=[2020, 2021, 2022, 2023, 2024, 2025],
        ticktext=["2020", "2021", "2022", "2023", "2024", "2025"],
        range=[2020, 2025]
    ),
    yaxis_title="Debt Ratio (%)"
)


st.plotly_chart(fig_ts, use_container_width=True)

st.markdown(
    "<span style='font-size:12px; color:rgba(0,0,0,0.6);'>"
    "Grey band represents volatility (defined as ±1 standard deviation) "
    "around the industry average Debt Ratio per year."
    "</span>",
    unsafe_allow_html=True
)

# Structured summary for Debt Ratio Time Series
avg_debt_level = industry_yearly["mean"].mean()
avg_debt_vol = industry_yearly["std"].mean()

st.markdown(
    f"**Debt Ratio Dynamics (Company vs Industry):** "
    f"Over the observed period, the industry average debt ratio was "
    f"**{avg_debt_level:.2f}%**, with an average annual volatility of "
    f"**{avg_debt_vol:.2f} percentage points** (±1σ)."
)

# --------------------------------------------------
# Debt Ratio Volatility Ranking (Company-Level)
# --------------------------------------------------

company_volatility = (
    yearly_df
    .groupby("company")["debt_ratio"]
    .std()
    .reset_index(name="debt_ratio_volatility")
)

# Compute industry average volatility
industry_volatility_avg = company_volatility["debt_ratio_volatility"].mean()

# Identify highest and lowest volatility
highest_vol = company_volatility.loc[
    company_volatility["debt_ratio_volatility"].idxmax()
]

lowest_vol = company_volatility.loc[
    company_volatility["debt_ratio_volatility"].idxmin()
]

st.subheader("Debt Ratio Volatility Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Highest Debt Ratio Volatility",
        value=highest_vol["company"],
        delta=f"{highest_vol['debt_ratio_volatility'] * 100:.2f}%"
    )

with col2:
    st.metric(
        label="Lowest Debt Ratio Volatility",
        value=lowest_vol["company"],
        delta=f"{lowest_vol['debt_ratio_volatility'] * 100:.2f}%"
    )

with col3:
    st.metric(
        label="Industry Average Volatility",
        value=f"{industry_volatility_avg * 100:.2f}%"
    )

# --------------------------------------------------
# SECTION 2 — LIQUIDITY VS LEVERAGE MAP
# --------------------------------------------------

st.header("Liquidity vs Leverage Map")

# Conditional colouring: Above / Below Industry Mean (Debt)
debt_mean = mean_metrics["debt_ratio"].mean()
liq_mean = mean_metrics["liquidity_ratio"].mean()
mean_metrics["Liquidity Map Position"] = mean_metrics["debt_ratio"].apply(
    lambda x: (
        "Above Industry Mean<br>(Debt Ratio)"
        if x >= debt_mean
        else "Below Industry Mean<br>(Debt Ratio)"
    )
)

fig2 = px.scatter(
    mean_metrics.round(2),
    x="debt_ratio",
    y="liquidity_ratio",
    size="total_assets",
    hover_name="company",
    color="Liquidity Map Position",
    color_discrete_map={
        "Above Industry Mean<br>(Debt Ratio)": PRIMARY_COLOR,
        "Below Industry Mean<br>(Debt Ratio)": "#F28B82"
    },
    hover_data={
        "total_assets": ":,.0f",
        "debt_ratio": ":.1f",
        "liquidity_ratio": ":.2f"
    },
    labels={
        "debt_ratio": "Debt Ratio (%)",
        "liquidity_ratio": "Liquidity Ratio",
        "total_assets": "Total Assets (SEK '000)"
    },
    title="Liquidity vs Leverage Positioning"
)

fig2.add_shape(
    type="line",
    x0=debt_mean,
    x1=debt_mean,
    y0=mean_metrics["liquidity_ratio"].min(),
    y1=mean_metrics["liquidity_ratio"].max(),
    line=dict(color=NEUTRAL_COLOR, width=2)
)

fig2.add_annotation(
    x=debt_mean,
    y=mean_metrics["liquidity_ratio"].max() + 0.2,
    text="Industry Mean<br>(Debt Ratio)",
    showarrow=False,
    align="center",
    font=dict(size=12, color=NEUTRAL_COLOR)
)

fig2.add_shape(
    type="line",
    x0=mean_metrics["debt_ratio"].min(),
    x1=mean_metrics["debt_ratio"].max(),
    y0=liq_mean,
    y1=liq_mean,
    line=dict(color=NEUTRAL_COLOR, width=2)
)

fig2.add_annotation(
    x=mean_metrics["debt_ratio"].max(),
    y=liq_mean - 0.2,
    text="Industry Mean<br>(Liquidity Ratio)",
    showarrow=False,
    align="right",
    xanchor="right",
    font=dict(size=12, color=NEUTRAL_COLOR)
)

# Add legend title for clarity
fig2.update_layout(
    legend_title_text="Leverage Position"
)

fig2.update_layout(height=600)

st.plotly_chart(fig2, use_container_width=True)
st.markdown(
    "<span style='font-size:12px; color:rgba(0,0,0,0.6);'>"
    "Bubble size represents average Total Assets (scale of company), "
    "calculated as the mean over the four overlapping years of investigation."
    "</span>",
    unsafe_allow_html=True
)

# Structured summary for Liquidity vs Leverage Map
st.markdown(
    f"**Liquidity vs Leverage Structure (Overlap-Year Means):** "
    f"The industry average debt ratio is **{debt_mean:.2f}%**, "
    f"with an average liquidity ratio of **{liq_mean:.2f}**. "
    f"Firms positioned in the lower-right quadrant combine elevated leverage with weaker liquidity buffers."
)

# Structural stability summary (based on liquidity ratio for consistency)
highest_liq_risk = mean_metrics.loc[mean_metrics["liquidity_ratio"].idxmax()]
lowest_liq_risk = mean_metrics.loc[mean_metrics["liquidity_ratio"].idxmin()]
industry_liq_avg_risk = mean_metrics["liquidity_ratio"].mean()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Highest Liquidity Ratio",
        value=highest_liq_risk["company"],
        delta=f"{highest_liq_risk['liquidity_ratio']:.2f}"
    )

with col2:
    st.metric(
        label="Lowest Liquidity Ratio",
        value=lowest_liq_risk["company"],
        delta=f"{lowest_liq_risk['liquidity_ratio']:.2f}"
    )

with col3:
    st.metric(
        label="Industry Average Liquidity Ratio",
        value=f"{industry_liq_avg_risk:.2f}"
    )

# --------------------------------------------------
# SECTION 3 — RISK QUADRANT MAPPING
# --------------------------------------------------


st.header("Risk Quadrant Mapping")

st.markdown(
    """
**Risk Model Selection**

Two classification frameworks are available:

• **Relative Risk Model** – Companies are classified relative to the industry mean  
  - Above / below average Debt Ratio  
  - Above / below average Liquidity Ratio  

• **Standard Risk Model** – Companies are classified using absolute structural thresholds  
  - Debt Ratio thresholds  
  - Liquidity Ratio thresholds  

"""
)

risk_model = st.radio(
    "Select Risk Classification Model",
    ["Relative (Industry Mean-Based)", "Standard (Absolute Threshold-Based)"],
    horizontal=True
)


# --------------------------------------------------
# Risk Classification Logic
# --------------------------------------------------

debt_mean = mean_metrics["debt_ratio"].mean()
liq_mean = mean_metrics["liquidity_ratio"].mean()

def classify_relative(row):
    if row["debt_ratio"] > debt_mean:
        if row["liquidity_ratio"] < liq_mean:
            return "Fragile"
        else:
            return "Aggressive"
    else:
        if row["liquidity_ratio"] < liq_mean:
            return "Underleveraged"
        else:
            return "Conservative"

def classify_standard(row):
    # Absolute structural thresholds (SME industrial convention)
    if row["debt_ratio"] > 70 and row["liquidity_ratio"] < 1.5:
        return "Fragile"
    elif row["debt_ratio"] > 70 and row["liquidity_ratio"] >= 1.5:
        return "Aggressive"
    elif row["debt_ratio"] <= 40 and row["liquidity_ratio"] >= 2.0:
        return "Conservative"
    elif row["debt_ratio"] <= 40 and row["liquidity_ratio"] < 2.0:
        return "Underleveraged"
    else:
        return "Moderate"

if risk_model == "Relative (Industry Mean-Based)":
    mean_metrics["Risk Profile"] = mean_metrics.apply(classify_relative, axis=1)
else:
    mean_metrics["Risk Profile"] = mean_metrics.apply(classify_standard, axis=1)

# --------------------------------------------
# Structural Risk Classification Chart
# --------------------------------------------

# Conditional colouring: Above / Below Industry Mean (Debt)
mean_metrics["Risk Map Position"] = mean_metrics["debt_ratio"].apply(
    lambda x: (
        "Above Industry Mean<br>(Debt Ratio)"
        if x >= debt_mean
        else "Below Industry Mean<br>(Debt Ratio)"
    )
)

fig3 = px.scatter(
    mean_metrics.round(2),
    x="debt_ratio",
    y="liquidity_ratio",
    color="Risk Map Position",
    size="total_assets",
    hover_name="company",
    color_discrete_map={
        "Above Industry Mean<br>(Debt Ratio)": PRIMARY_COLOR,
        "Below Industry Mean<br>(Debt Ratio)": "#F28B82"
    },
    hover_data={
        "total_assets": ":,.0f",
        "debt_ratio": ":.1f",
        "liquidity_ratio": ":.2f"
    },
    labels={
        "debt_ratio": "Debt Ratio (%)",
        "liquidity_ratio": "Liquidity Ratio",
        "total_assets": "Total Assets (SEK '000)"
    },
    title="Structural Risk Classification"
)

# Vertical mean line (Debt)
fig3.add_shape(
    type="line",
    x0=debt_mean,
    x1=debt_mean,
    y0=mean_metrics["liquidity_ratio"].min(),
    y1=mean_metrics["liquidity_ratio"].max(),
    line=dict(color=NEUTRAL_COLOR, width=2)
)

fig3.add_annotation(
    x=debt_mean,
    y=mean_metrics["liquidity_ratio"].max() + 0.2,
    text="Industry Mean<br>(Debt Ratio)",
    showarrow=False,
    align="center",
    font=dict(size=12, color=NEUTRAL_COLOR)
)

# Horizontal mean line (Liquidity)
fig3.add_shape(
    type="line",
    x0=mean_metrics["debt_ratio"].min(),
    x1=mean_metrics["debt_ratio"].max(),
    y0=liq_mean,
    y1=liq_mean,
    line=dict(color=NEUTRAL_COLOR, width=2)
)

fig3.add_annotation(
    x=mean_metrics["debt_ratio"].max(),
    y=liq_mean - 0.2,
    text="Industry Mean<br>(Liquidity Ratio)",
    showarrow=False,
    align="right",
    xanchor="right",
    font=dict(size=12, color=NEUTRAL_COLOR)
)

fig3.update_layout(
    legend_title_text="Leverage Position",
    height=600
)

st.plotly_chart(fig3, use_container_width=True)

st.markdown(
    "<span style='font-size:12px; color:rgba(0,0,0,0.6);'>"
    "Bubble size represents average Total Assets (scale of company), "
    "calculated as the mean over the four overlapping years of investigation."
    "</span>",
    unsafe_allow_html=True
)

# Structured summary for Risk Quadrant Mapping
risk_counts = mean_metrics["Risk Profile"].value_counts()
total_firms = len(mean_metrics)

if risk_model.startswith("Relative"):
    summary_text = (
        "**Structural Risk Classification (Relative Model):** "
        "Based on leverage and liquidity relative to industry averages, "
        "firms are distributed across the full spectrum of structural risk categories."
    )
else:
    summary_text = (
        "**Structural Risk Classification (Standard Model):** "
        "Using predefined absolute leverage and liquidity thresholds, "
        "firms are distributed across the full spectrum of structural risk categories."
    )

st.markdown(summary_text)

# --------------------------------------------------
# Risk Map Performance Summary (Stability Score)
# --------------------------------------------------

# Recompute stability score locally for ranking display
mean_metrics["stability_score_temp"] = (
    mean_metrics["equity_ratio"]
    - mean_metrics["debt_ratio"]
    + (mean_metrics["liquidity_ratio"] * 10)
)

highest_stability = mean_metrics.loc[
    mean_metrics["stability_score_temp"].idxmax()
]

lowest_stability = mean_metrics.loc[
    mean_metrics["stability_score_temp"].idxmin()
]

industry_stability_avg = mean_metrics["stability_score_temp"].mean()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Highest Structural Stability",
        value=highest_stability["company"],
        delta=f"{highest_stability['stability_score_temp']:.2f}"
    )

with col2:
    st.metric(
        label="Lowest Structural Stability",
        value=lowest_stability["company"],
        delta=f"{lowest_stability['stability_score_temp']:.2f}"
    )

with col3:
    st.metric(
        label="Industry Average Stability Score",
        value=f"{industry_stability_avg:.2f}"
    )

# Clean up temporary column
mean_metrics.drop(columns=["stability_score_temp"], inplace=True)

# --------------------------------------------------
# SECTION 4 — STRUCTURAL STABILITY INDEX
# --------------------------------------------------

st.header("Structural Stability Ranking")

mean_metrics["stability_score"] = (
    mean_metrics["equity_ratio"]
    - mean_metrics["debt_ratio"]
    + (mean_metrics["liquidity_ratio"] * 10)
)


ranking = mean_metrics.sort_values("stability_score", ascending=False)

display_cols = [
    "company",
    "equity_ratio",
    "debt_ratio",
    "liquidity_ratio",
    "Risk Profile",
    "stability_score"
]

# Identify top and bottom firms
top_row = ranking.iloc[0]
bottom_row = ranking.iloc[-1]

comparison_df = pd.DataFrame({
    "Metric": ["Equity Ratio (%)", "Debt Ratio (%)", "Liquidity Ratio", "Stability Score"],
    top_row["company"]: [
        top_row["equity_ratio"],
        top_row["debt_ratio"],
        top_row["liquidity_ratio"],
        top_row["stability_score"]
    ],
    bottom_row["company"]: [
        bottom_row["equity_ratio"],
        bottom_row["debt_ratio"],
        bottom_row["liquidity_ratio"],
        bottom_row["stability_score"]
    ]
})

fig_compare = go.Figure()

fig_compare.add_trace(
    go.Bar(
        x=comparison_df["Metric"],
        y=comparison_df[top_row["company"]],
        name=top_row["company"],
        marker_color=PRIMARY_COLOR,
        hovertemplate="<b>%{x}</b><br>%{y:.2f}<extra></extra>"
    )
)

fig_compare.add_trace(
    go.Bar(
        x=comparison_df["Metric"],
        y=comparison_df[bottom_row["company"]],
        name=bottom_row["company"],
        marker_color="#F28B82",
        hovertemplate="<b>%{x}</b><br>%{y:.2f}<extra></extra>"
    )
)

fig_compare.update_layout(
    barmode="group",
    height=500,
    yaxis_title="Value",
    xaxis_title="Metric"
)

st.plotly_chart(fig_compare, use_container_width=True)

st.markdown(
    "**Structural Stability Index (Composite Framework):** "
    "Comparison of the strongest and weakest balance sheet profiles "
    "across core structural metrics. Blue denotes the strongest profile; "
    "orange denotes the weakest within the observed sample. "
    "The firms displayed above represent the strongest and weakest balance sheet "
    "profiles within the observed sample. Full ranking diagnostics are reserved "
    "for the detailed analytical report."
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