import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).resolve().parents[1]))


from src.metrics.market_structure import (
    compute_average_market_share,
    compute_hhi,
    compute_market_share,
    concentration_ratio,
    effective_number_of_firms,
    dominance_gap,
    compute_gini_market_share,
    market_share_mobility
)

st.title("Market Structure Analysis")

@st.cache_data
def load_data():
    return pd.read_csv("data/processed/elv_time_series.csv")

# Load and clean data

df = load_data()

df = df.rename(columns={
    "Company": "company",
    "Year": "year",
    "Net sales": "total_revenue"
})

required_cols = {"company", "year", "total_revenue"}
if not required_cols.issubset(df.columns):
    st.error("Dataset must contain: company, year, total_revenue columns.")
    st.stop()

# -------------------------------------------------
# Market Share Time Series
# -------------------------------------------------

ms_df = compute_market_share(df, "total_revenue")

year_min = int(ms_df["year"].min())
year_max = int(ms_df["year"].max())
st.subheader(f"Market Share Time Series ({year_min}–{year_max}) (Company vs Industry)")

industry_yearly = (
    ms_df.groupby("year")["market_share"]
    .agg(["mean", "std"])
    .reset_index()
)

industry_yearly["upper"] = industry_yearly["mean"] + industry_yearly["std"]
industry_yearly["lower"] = industry_yearly["mean"] - industry_yearly["std"]

fig = go.Figure()

for company in ms_df["company"].unique():
    company_df = ms_df[ms_df["company"] == company]
    fig.add_trace(go.Scatter(
        x=company_df["year"],
        y=company_df["market_share"] * 100,
        mode="lines+markers",
        showlegend=False,
        line=dict(color="rgba(120,120,120,0.35)", width=1),
        marker=dict(size=5),
        text=[company] * len(company_df),
        hovertemplate="<b>%{text}</b><br>Year: %{x}<br>Market Share: %{y:.2f}%<extra></extra>"
    ))

# Industry average (blue continuous)
fig.add_trace(go.Scatter(
    x=industry_yearly["year"],
    y=industry_yearly["mean"] * 100,
    mode="lines+markers",
    line=dict(color="#6FA8DC", width=2.5),
    marker=dict(size=7),
    name="Industry Average",
    hovertemplate="<b>Industry Average</b><br>Year: %{x}<br>Market Share: %{y:.2f}%<extra></extra>"
))

# Volatility band
fig.add_trace(go.Scatter(
    x=list(industry_yearly["year"]) + list(industry_yearly["year"][::-1]),
    y=list(industry_yearly["upper"] * 100) + list(industry_yearly["lower"][::-1] * 100),
    fill="toself",
    fillcolor="rgba(90,111,137,0.08)",
    line=dict(color="rgba(255,255,255,0)"),
    hoverinfo="skip",
    name="Volatility Band (±1σ)"
))

fig.update_layout(
    height=500,
    xaxis=dict(
        title="Year",
        range=[year_min - 1, year_max + 1],
        tickmode="linear",
        dtick=1
    ),
    yaxis_title="Market Share (%)",
    legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
)

st.plotly_chart(fig, use_container_width=True)

# Analytical summary line
avg_trend = industry_yearly["mean"].iloc[-1] - industry_yearly["mean"].iloc[0]
volatility_avg = industry_yearly["std"].mean()

st.markdown(
    f"**Market Structure (Composite View):** "
    f"Industry average market share remained "
    f"{'structurally stable' if abs(avg_trend) < 0.005 else 'directionally shifting'} "
    f"over the observed period ({year_min}–{year_max}). "
    f"Cross-sectional dispersion (±1σ) averaged {volatility_avg*100:.2f}%, "
    f"indicating {'limited competitive redistribution' if volatility_avg < 0.05 else 'moderate competitive dispersion'} "
    f"within the observed sample."
)

# -------------------------------------------------
# Concentration Metrics
# -------------------------------------------------

st.subheader("Industry Concentration Metrics")

years = sorted(df["year"].unique())
selected_year = st.selectbox("Select Year for Concentration Analysis", ["Total"] + years)

if selected_year == "Total":
    df_total = df.groupby("company", as_index=False)["total_revenue"].sum()
    total = df_total["total_revenue"].sum()
    shares = df_total["total_revenue"] / total
    cr3 = shares.sort_values(ascending=False).head(3).sum()
    hhi = (shares ** 2).sum()
else:
    cr3 = concentration_ratio(df, "total_revenue", selected_year)
    hhi = compute_hhi(df, "total_revenue", selected_year)

col1, col2 = st.columns(2)
with col1:
    st.metric("CR3 (Top 3 Concentration Ratio)", f"{cr3 * 100:.2f}%")
with col2:
    st.metric("HHI (Herfindahl-Hirschman Index)", f"{hhi:.2f}")

# Concentration interpretation
if hhi < 0.15:
    concentration_regime = "Fragmented"
elif hhi < 0.25:
    concentration_regime = "Moderately Concentrated"
else:
    concentration_regime = "Highly Concentrated"

st.markdown(
    f"**Industry Concentration:** The market is classified as "
    f"**{concentration_regime}** based on HHI ({hhi:.2f}). "
    f"Top 3 firms control {cr3*100:.1f}% of total market share."
)

# -------------------------------------------------
# Advanced Diagnostics
# -------------------------------------------------

st.markdown("---")
st.subheader("Advanced Structural Diagnostics")

if selected_year == "Total":
    eff_firms = 1 / hhi if hhi != 0 else None
    ranked = df_total.sort_values("total_revenue", ascending=False)
    dom_gap = (ranked.iloc[0]["total_revenue"] - ranked.iloc[1]["total_revenue"]) / total
    gini = compute_gini_market_share(df, "total_revenue", None)
else:
    eff_firms = effective_number_of_firms(df, "total_revenue", selected_year)
    dom_gap = dominance_gap(df, "total_revenue", selected_year)
    gini = compute_gini_market_share(df, "total_revenue", selected_year)


col1, col2 = st.columns(2)
with col1:
    st.metric("Effective Number of Firms", f"{eff_firms:.0f}" if eff_firms else "N/A")
with col2:
    st.metric("Dominance Gap (Leader - #2)", f"{dom_gap * 100:.2f}%" if dom_gap else "N/A")

# Structural diagnostics interpretation
st.markdown(
    f"**Structural Depth:** Effective competition equivalent to "
    f"~{eff_firms:.0f} equally-sized firms. "
    f"Leader dominance gap is {dom_gap*100:.1f}% of total market share."
)

# -------------------------------------------------
# Market Share Gini Scale
# -------------------------------------------------

if gini is not None:
    st.markdown("### Market Share Gini")

    gradient = np.linspace(0, 1, 500)
    gradient = np.vstack((gradient,))

    gini_fig = go.Figure()
    gini_fig.add_trace(go.Heatmap(
        z=gradient,
        x=np.linspace(0, 1, 500),
        y=[0.4, 0.7],  # thinner band
        colorscale=[[0.0, "green"], [0.5, "yellow"], [1.0, "red"]],
        showscale=False
    ))

    gini_fig.add_shape(
        type="line",
        x0=gini,
        x1=gini,
        y0=0.4,
        y1=0.7,
        line=dict(color="black", width=2)
    )

    gini_fig.add_annotation(
        x=gini,
        y=0.80,
        text=f"<b>{gini:.2f}</b>",
        showarrow=False,
        font=dict(size=10, color="black")
    )

    # Directional concentration scale label
    gini_fig.add_annotation(
        x=0.5,
        y=0.2,
        text="Low Concentration  →  High Concentration",
        showarrow=False,
        font=dict(size=11, color="#55585B")
    )

    gini_fig.update_layout(
        height=130,
        margin=dict(l=40, r=40, t=20, b=40),
        xaxis=dict(
            range=[0, 1],
            tickvals=[0, 0.25, 0.5, 0.75, 1]
        ),
        yaxis=dict(
            range=[0, 1],
            showticklabels=False
        ),
        plot_bgcolor="white"
    )


    st.plotly_chart(gini_fig, use_container_width=True)

    # Gini interpretation
    if gini < 0.3:
        gini_regime = "Low concentration (shares relatively evenly distributed)"
    elif gini < 0.6:
        gini_regime = "Moderate concentration"
    else:
        gini_regime = "High concentration (market power concentrated in few firms)"

    st.markdown(
        f"**Market Share Gini:** A Gini coefficient of **{gini:.2f}** indicates "
        f"{gini_regime}. "
    )

# -------------------------------------------------
# Structural Dynamics
# -------------------------------------------------

st.markdown("### Structural Dynamics Over Time")


mobility_df = market_share_mobility(df, "total_revenue")

# --- Mobility Regime Classification (Percentile-Based) ---
low_thresh = mobility_df["mobility_index"].quantile(0.33)
high_thresh = mobility_df["mobility_index"].quantile(0.66)

def classify_mobility(val):
    if val <= low_thresh:
        return "Low Mobility"
    elif val <= high_thresh:
        return "Medium Mobility"
    else:
        return "High Mobility"

mobility_df["mobility_regime"] = mobility_df["mobility_index"].apply(classify_mobility)

fig_mob = go.Figure()
fig_mob.add_trace(go.Scatter(
    x=mobility_df["year"],
    y=mobility_df["mobility_index"],
    mode="lines+markers",
    line=dict(color="#5DADE2", width=2),
    name="Structural Mobility Index",
    showlegend=True
))

fig_mob.update_layout(
    height=400,
    xaxis=dict(
        title="Year",
        range=[2021, 2025],
        tickmode="linear",
        dtick=1
    ),
    yaxis_title="Mobility Index",
    legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
)

st.plotly_chart(fig_mob, use_container_width=True)

# Mobility summary
mobility_trend = mobility_df["mobility_index"].iloc[-1] - mobility_df["mobility_index"].iloc[0]
avg_mobility = mobility_df["mobility_index"].mean()

latest_year = mobility_df["year"].iloc[-1]
latest_regime = mobility_df["mobility_regime"].iloc[-1]


sample_start = mobility_df["year"].min()
sample_end = mobility_df["year"].max()
sample_n = mobility_df["year"].nunique()
latest_mob = mobility_df["mobility_index"].iloc[-1]

st.markdown(
    f"**Structural Mobility:** Structural mobility "
    f"{'declined' if mobility_trend < 0 else 'increased'} over the period. "
    f"Average mobility level was {avg_mobility:.3f}. "
    f"The latest year ({latest_year}), at {latest_mob:.3f}, falls in the lower third of observed mobility levels "
    f"and is therefore classified as **{latest_regime}** relative to the historical sample "
    f"({sample_start}–{sample_end}) and within the observed sample (n = {sample_n} years)."
)

# -------------------------------------------------
# Mobility Regime Bar (Visual Scale)
# -------------------------------------------------

st.markdown("#### Mobility Regime Scale")

# Normalise mobility range
mob_min = mobility_df["mobility_index"].min()
mob_max = mobility_df["mobility_index"].max()
latest_mob = mobility_df["mobility_index"].iloc[-1]

# Create gradient scale
mob_gradient = np.linspace(mob_min, mob_max, 500)
mob_gradient = np.vstack((mob_gradient,))

mob_fig = go.Figure()

mob_fig.add_trace(go.Heatmap(
    z=mob_gradient,
    x=np.linspace(mob_min, mob_max, 500),
    y=[0.4, 0.7],  # thinner band
    colorscale=[[0.0, "green"], [0.5, "yellow"], [1.0, "red"]],
    showscale=False
))

# Vertical marker for latest mobility
mob_fig.add_shape(
    type="line",
    x0=latest_mob,
    x1=latest_mob,
    y0=0.4,
    y1=0.7,
    line=dict(color="black", width=2)
)

mob_fig.add_annotation(
    x=latest_mob,
    y=0.80,
    text=f"<b>{latest_mob:.3f}</b>",
    showarrow=False,
    font=dict(size=10, color="black")
)

mob_fig.update_layout(
    height=130,
    margin=dict(l=40, r=40, t=20, b=40),
    xaxis=dict(
        range=[mob_min, mob_max],
        tickvals=np.linspace(mob_min, mob_max, 5)
    ),
    yaxis=dict(
        range=[0, 1],
        showticklabels=False
    ),
    plot_bgcolor="white"
)

mob_fig.add_annotation(
    x=(mob_min + mob_max) / 2,
    y=0.2,
    text="Mobility Index  (Low → High)",
    showarrow=False,
    font=dict(size=11, color="#55585B")
)

st.plotly_chart(mob_fig, use_container_width=True)

# -------------------------------------------------
# YoY HHI Contribution
# -------------------------------------------------

st.markdown("### Year-over-Year Change in Herfindahl–Hirschman Index Contribution (Per Company)")

ms_df = compute_market_share(df, "total_revenue")
ms_df["hhi_contribution"] = ms_df["market_share"] ** 2
ms_df = ms_df.sort_values(["company", "year"])
ms_df["yoy_hhi_contribution"] = ms_df.groupby("company")["hhi_contribution"].diff()

industry_yoy = (
    ms_df.groupby("year")["yoy_hhi_contribution"]
    .agg(["mean", "std"])
    .reset_index()
)
industry_yoy["upper"] = industry_yoy["mean"] + industry_yoy["std"]
industry_yoy["lower"] = industry_yoy["mean"] - industry_yoy["std"]

all_companies = sorted(ms_df["company"].unique())
selected_companies = st.multiselect(
    "Select Company (or leave empty to show all)",
    options=all_companies,
    default=all_companies
)

fig_yoy = go.Figure()

for company in selected_companies:
    company_df = ms_df[ms_df["company"] == company]
    fig_yoy.add_trace(go.Scatter(
        x=company_df["year"],
        y=company_df["yoy_hhi_contribution"],
        mode="lines+markers",
        line=dict(color="rgba(120,120,120,0.5)", width=1),
        marker=dict(size=6),
        customdata=[company] * len(company_df),
        hovertemplate="<b>%{customdata}</b><br>Year: %{x}<br>Year-over-Year Herfindahl–Hirschman Index Contribution: %{y:.4f}<extra></extra>",
        showlegend=False
    ))

# Volatility band (±1σ cross-sectional dispersion)
fig_yoy.add_trace(go.Scatter(
    x=list(industry_yoy["year"]) + list(industry_yoy["year"][::-1]),
    y=list(industry_yoy["upper"]) + list(industry_yoy["lower"][::-1]),
    fill="toself",
    fillcolor="rgba(93,173,226,0.15)",
    line=dict(color="rgba(255,255,255,0)"),
    hoverinfo="skip",
    name="Cross-Sectional Dispersion (±1σ)"
))

# Industry average (structural drift)
fig_yoy.add_trace(go.Scatter(
    x=industry_yoy["year"],
    y=industry_yoy["mean"],
    mode="lines",
    line=dict(color="#5DADE2", width=3),
    name="Industry Average",
    hovertemplate="<b>Industry Average</b><br>Year: %{x}<br>Year-over-Year Herfindahl–Hirschman Index Contribution: %{y:.4f}<extra></extra>",
    showlegend=True
))

fig_yoy.update_layout(
    height=450,
    xaxis=dict(
        title="Year",
        tickmode="linear",
        dtick=1
    ),
    yaxis_title="Year-over-Year Change in Herfindahl–Hirschman Index Contribution",
    legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
)




st.plotly_chart(fig_yoy, use_container_width=True)

# --- Year-over-Year Structural Drift Summary ---
latest_yoy_year = industry_yoy["year"].iloc[-1]
latest_drift = industry_yoy["mean"].iloc[-1]
avg_dispersion = industry_yoy["std"].mean()

st.markdown(
    f"**Year-over-Year Structural Drift ({latest_yoy_year}):** "
    f"Net concentration drift = {latest_drift:+.4f}. "
    f"Average cross-sectional dispersion (σ) = {avg_dispersion:.4f}, "
    f"indicating "
    f"{'contained redistribution across firms.' if avg_dispersion < 0.01 else 'active competitive redistribution across firms.'}"
)

# --- Full Structural Diagnostics (Time Comparison) ---

# Compute turbulence per year (mean absolute firm-level change)
turbulence_by_year = (
    ms_df.groupby("year")["yoy_hhi_contribution"]
    .apply(lambda x: x.abs().mean())
    .reset_index(name="turbulence")
)

# Merge with industry drift (mean)
diagnostics_df = industry_yoy.merge(turbulence_by_year, on="year")

# Regime classification

def classify_regime(row):
    if row["turbulence"] < 0.0005:
        return "Stable Structure"
    elif row["turbulence"] < 0.0015:
        return "Mild Competitive Shifts"
    elif row["mean"] > 0 and row["turbulence"] >= 0.0015:
        return "Consolidation Phase"
    else:
        return "Competitive Rebalancing"


diagnostics_df["regime"] = diagnostics_df.apply(classify_regime, axis=1)

# Display compact diagnostics table
st.markdown("#### Structural Regime Overview (All Years)")


st.dataframe(
    diagnostics_df[["year", "mean", "std", "turbulence", "regime"]]
    .rename(columns={
        "mean": "Net HHI Drift",
        "std": "Cross-Sectional Dispersion (σ)",
        "turbulence": "Structural Turbulence",
        "regime": "Structural Regime"
    }),
    use_container_width=True
)

# Table summary
latest_year = diagnostics_df["year"].max()
latest_row = diagnostics_df[diagnostics_df["year"] == latest_year].iloc[0]

st.markdown(
    f"**Latest Structural Snapshot ({latest_year}):** "
    f"Net concentration drift = {latest_row['mean']:+.4f}, "
    f"Dispersion (σ) = {latest_row['std']:.4f}, "
    f"Turbulence = {latest_row['turbulence']:.4f}. "
    f"Current regime classified as **{latest_row['regime']}**."
)

# Visualise turbulence trend
fig_turb = go.Figure()
fig_turb.add_trace(go.Scatter(
    x=diagnostics_df["year"],
    y=diagnostics_df["turbulence"],
    mode="lines+markers",
    line=dict(color="#5DADE2", width=3),
    name="Structural Turbulence"
))

fig_turb.update_layout(
    height=350,
    xaxis=dict(title="Year", tickmode="linear", dtick=1),
    yaxis_title="Structural Turbulence (Mean |Δ Contribution|)",
    legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
)


st.plotly_chart(fig_turb, use_container_width=True)

# Turbulence trend summary
avg_turbulence = diagnostics_df["turbulence"].mean()
peak_year = diagnostics_df.loc[diagnostics_df["turbulence"].idxmax(), "year"]

st.markdown(
    f"**Structural Turbulence (Competitive Intensity):** "
    f"Average annual turbulence measured {avg_turbulence:.4f}. "
    f"Redistribution peaked in {peak_year}. "
    f"Observed turbulence "
    f"{'moderated toward the end of the sample.' if diagnostics_df['turbulence'].iloc[-1] < diagnostics_df['turbulence'].iloc[0] else 'intensified toward the end of the sample.'}"
    f" This indicates "
    f"{'a gradual stabilization of market structure.' if diagnostics_df['turbulence'].iloc[-1] < diagnostics_df['turbulence'].iloc[0] else 'increasing structural reshuffling across firms.'}"
)

# -------------------------------------------------
# Δ Market Share vs Δ HHI Contribution Analysis
# -------------------------------------------------


# Compute YoY market share change
ms_df["yoy_market_share"] = ms_df.groupby("company")["market_share"].diff()

# Remove first-year NaNs
delta_df = ms_df.dropna(subset=["yoy_market_share", "yoy_hhi_contribution"])

# -------------------------------------------------
# Scatter Plot (Structural Sensitivity)
# -------------------------------------------------

st.markdown("#### Scatter: Change in Market Share vs Change in Herfindahl–Hirschman Index Contribution")

# Create sign classification
delta_df["sign"] = delta_df["yoy_hhi_contribution"].apply(
    lambda x: "Increase (≥ 0)" if x >= 0 else "Decrease (< 0)"
)

color_map = {
    "Increase (≥ 0)": "#5A6F89",
    "Decrease (< 0)": "#F28B82"
}

fig_scatter = go.Figure()

for label, group in delta_df.groupby("sign"):
    fig_scatter.add_trace(go.Scatter(
        x=group["yoy_market_share"],
        y=group["yoy_hhi_contribution"],
        mode="markers",
        marker=dict(
            size=10,
            color=color_map[label]
        ),
        name=label,
        text=group["company"],
        hovertemplate="<b>%{text}</b><br>Change in Market Share: %{x:.4f}<br>Change in Herfindahl–Hirschman Index Contribution: %{y:.4f}<extra></extra>"
    ))

# --- Linear regression (ΔHHI = α + β ΔShare) ---
beta, alpha = np.polyfit(
    delta_df["yoy_market_share"],
    delta_df["yoy_hhi_contribution"],
    1
)

x_vals = np.linspace(
    delta_df["yoy_market_share"].min(),
    delta_df["yoy_market_share"].max(),
    100
)
y_vals = alpha + beta * x_vals

fig_scatter.add_trace(go.Scatter(
    x=x_vals,
    y=y_vals,
    mode="lines",
    line=dict(color="#55585B", width=1.5),
    name="Regression Line"
))

fig_scatter.update_layout(
    height=450,
    xaxis_title="Change in Market Share",
    yaxis_title="Change in Herfindahl–Hirschman Index Contribution",
    legend=dict(
        orientation="h",
        y=1.15,
        x=0.5,
        xanchor="center"
    ),
    margin=dict(t=80)
)

st.plotly_chart(fig_scatter, use_container_width=True)

# --- Analytical summary ---
corr = delta_df["yoy_market_share"].corr(delta_df["yoy_hhi_contribution"])
r_squared = corr ** 2

st.markdown(
    f"**Change in Share–Concentration Sensitivity:** "
    f"Correlation (ρ) = {corr:+.3f} | R² = {r_squared:.3f}. "
    f"Approximately {r_squared*100:.1f}% of variation in change in Herfindahl–Hirschman Index contribution "
    f"is explained by change in market share movements, indicating "
    f"{'strong structural amplification effects.' if r_squared >= 0.5 else 'moderate structural linkage between share shifts and concentration dynamics.'}"
)

# -------------------------------------------------
# Dual Bar Chart (Per Company Comparison)
# -------------------------------------------------

available_years = sorted(delta_df["year"].unique())

# Default selected year
default_year = available_years[-1]

st.subheader(
    f"Dual Bar: Change in Market Share vs Change in Herfindahl–Hirschman Index Contribution ({default_year})"
)

# Dropdown placed UNDER the title
selected_bar_year = st.selectbox(
    "Select Year for Change Comparison",
    options=available_years,
    index=len(available_years) - 1
)

latest_df = delta_df[delta_df["year"] == selected_bar_year]

# Reorder: positives (≥0) on the left in descending order,
# negatives (<0) on the right in ascending order
pos_df = latest_df[latest_df["yoy_market_share"] >= 0] \
    .sort_values("yoy_market_share", ascending=False)

neg_df = latest_df[latest_df["yoy_market_share"] < 0] \
    .sort_values("yoy_market_share", ascending=True)

latest_df = pd.concat([pos_df, neg_df])

fig_bar = go.Figure()

fig_bar.add_trace(go.Bar(
    x=latest_df["company"],
    y=latest_df["yoy_market_share"],
    name="Change in Market Share",
    marker=dict(
        color=[
            "#5A6F89" if val >= 0 else "#F28B82"
            for val in latest_df["yoy_market_share"]
        ]
    )
))


fig_bar.add_trace(go.Bar(
    x=latest_df["company"],
    y=latest_df["yoy_hhi_contribution"],
    name="Change in Herfindahl–Hirschman Index Contribution",
    marker=dict(
        color=[
            "#A7BDD2" if val >= 0 else "#E9C1BE"
            for val in latest_df["yoy_hhi_contribution"]
        ]
    )
))

# --- Legend explanation for color coding ---
fig_bar.add_trace(go.Scatter(
    x=[None],
    y=[None],
    mode="markers",
    marker=dict(size=10, color="#5A6F89"),
    name="Increase (≥ 0)",
    showlegend=True
))

fig_bar.add_trace(go.Scatter(
    x=[None],
    y=[None],
    mode="markers",
    marker=dict(size=10, color="#F28B82"),
    name="Decrease (< 0)",
    showlegend=True
))

fig_bar.update_layout(
    barmode="group",
    height=520,
    xaxis_title="Company",
    yaxis_title="Change",
    margin=dict(t=80),
    legend=dict(
        orientation="h",
        y=1.15,
        x=0.5,
        xanchor="center"
    )
)

st.plotly_chart(fig_bar, use_container_width=True)

# Summary insight
net_share_change = latest_df["yoy_market_share"].sum()
net_hhi_change = latest_df["yoy_hhi_contribution"].sum()

st.markdown(
    f"**Change in Structural Redistribution ({selected_bar_year}):** "
    f"Net HHI change = {net_hhi_change:+.4f}. "
    f"Market share redistribution "
    f"{'increased' if net_hhi_change > 0 else 'reduced' if net_hhi_change < 0 else 'did not materially alter'} "
    f"overall concentration. "
    f"Share shifts were "
    f"{'directionally biased toward larger firms.' if net_hhi_change > 0 else 'directionally biased toward smaller firms.' if net_hhi_change < 0 else 'structurally neutral across firm sizes.'}"
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