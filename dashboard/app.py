import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(layout="wide")

st.title("Structural Benchmarking of Swedish ELV Dismantlers within 100Km Radius (Years 2021–2024)")
st.caption("Comparative structural financial analysis of selected ELV dismantlers, focusing on growth durability, profitability quality, capital structure discipline, and competitive positioning. Analysis is based on publicly aviailable financial statements.")

# --------------------------------------------------
# LOAD PROCESSED DATA
# --------------------------------------------------

@st.cache_data
def load_data():
    metrics = pd.read_csv("data/processed/elv_metrics.csv")
    ts = pd.read_csv("data/processed/elv_time_series.csv")
    return metrics, ts

df, df_ts = load_data()

# --------------------------------------------------
# SIDEBAR FILTER
# --------------------------------------------------

st.sidebar.header("Filters")

selected_companies = st.sidebar.multiselect(
    "Select Companies",
    options=df["Company"].unique(),
    default=df["Company"].unique()
)

df_filtered = df[df["Company"].isin(selected_companies)]
df_ts_filtered = df_ts[df_ts["Company"].isin(selected_companies)]

# --------------------------------------------------
# INDUSTRY BENCHMARKS
# --------------------------------------------------
industry_avg_cagr = df_filtered["CAGR_21_24"].mean()
industry_avg_margin = df_filtered["Avg Operating Margin"].mean()
industry_avg_market_share = df_filtered["Avg Market Share"].mean()

# --------------------------------------------------
# EXECUTIVE SUMMARY & KEY INSIGHTS
# --------------------------------------------------

st.markdown("### Executive Summary & Key Insights (Yrs 2021–2024)")

if not df_filtered.empty:
    # Top Growth Performer
    top_growth = df_filtered.loc[df_filtered["CAGR_21_24"].idxmax()]

    # Most Operationally Stable Company
    most_stable = df_filtered.loc[df_filtered["Operating Margin Vol"].idxmin()]

    # Market Leader
    market_leader = df_filtered.loc[df_filtered["Avg Market Share"].idxmax()]

    # Correlation Insight
    corr = df_filtered["Avg Market Share"].corr(df_filtered["Avg Operating Margin"])

    col1, col2, col3 = st.columns(3)

   # Top Growth Performer
    with col1:
        st.metric(
            label="Highest Growth Compounder",
            value=top_growth["Company"],
            delta=f"CAGR: {top_growth['CAGR_21_24']:.1%} | Industry Avg: {industry_avg_cagr:.1%}"
        )

    # Most Operationally Stable
    with col2:
        st.metric(
            label="Lowest Earnings Volatility",
            value=most_stable["Company"],
             delta=f"Operating Margin Volatility: {most_stable['Operating Margin Vol']:.1%} | Industry Avg: {industry_avg_margin:.1%}"
        )

    # Market Leader
    with col3:
        st.metric(
            label="Market Leader",
            value=market_leader["Company"],
            delta=f"Market Share: {market_leader['Avg Market Share']:.1%} | Industry Avg: {industry_avg_market_share:.1%}"
        )

    st.markdown(
        f"""
        <div style="font-size: 13px; margin-top: 10px;">
        <strong>Industry Insight:</strong>  
        The correlation between <em>Average Market Share</em> and <em>Average Operating Margin</em> is 
        <strong>{corr:.2f}</strong>, suggesting that scale is associated with stronger profitability across the ELV dismantling sector.
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    st.warning("No companies selected. Please adjust the filters.")


# --------------------------------------------------
# YOY Growth Time Series (Companies + Mean & Volatility Band)
# --------------------------------------------------

st.subheader("YoY Revenue Growth (Companies, Mean & Volatility)")

# Filter time-series dataset
df_ts_filtered = df_ts[df_ts["Company"].isin(selected_companies)]

# Remove first year (NaN YoY values)
df_yoy = df_ts_filtered.dropna(subset=["YoY Revenue Growth"])

# Compute industry mean and volatility
growth_df = (
    df_yoy.groupby("Year")["YoY Revenue Growth"]
    .agg(["mean", "std"])
    .reset_index()
)

growth_df["Upper Band"] = growth_df["mean"] + growth_df["std"]
growth_df["Lower Band"] = growth_df["mean"] - growth_df["std"]

fig_growth = go.Figure()

# 1️⃣ Add individual company lines (light grey)
for company in df_yoy["Company"].unique():
    company_df = df_yoy[df_yoy["Company"] == company]
    fig_growth.add_trace(go.Scatter(
        x=company_df["Year"],
        y=company_df["YoY Revenue Growth"],
        mode="lines+markers",
        line=dict(width=1, color="rgba(150,150,150,0.4)"),
        name=company,
        showlegend=False,
        hovertemplate=f"{company}: %{{y:.2%}}<extra></extra>"
    ))

# 2️⃣ Add volatility band
fig_growth.add_trace(go.Scatter(
    x=growth_df["Year"],
    y=growth_df["Upper Band"],
    mode="lines",
    line=dict(width=0),
    showlegend=False,
    hoverinfo="skip"
))

fig_growth.add_trace(go.Scatter(
    x=growth_df["Year"],
    y=growth_df["Lower Band"],
    mode="lines",
    fill="tonexty",
    fillcolor="rgba(90,111,137,0.1)",
    line=dict(width=0),
    name="Volatility Band",
    hoverinfo="skip"
))

# 3️⃣ Add industry mean line
fig_growth.add_trace(go.Scatter(
    x=growth_df["Year"],
    y=growth_df["mean"],
    mode="lines",
    line=dict(color="#F28B82", width=2.5),
    name="Industry Average YoY Growth",
    hovertemplate="%{y:.2%}<extra></extra>"
))

fig_growth.update_layout(
    plot_bgcolor="white",
    xaxis_title="Year",
    yaxis_title="YoY Revenue Growth",
    height=550,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

fig_growth.update_xaxes(
    tickmode="linear",
    dtick=1,          # step = 1 year
    tickformat="d"    # integer format (no decimals, no commas)
)

fig_growth.update_yaxes(tickformat=".1%")

st.plotly_chart(fig_growth, width="stretch")

st.markdown(f"""
**Growth Dispersion Insight:**  
Sector average YoY growth volatility is {growth_df['std'].mean():.1%}, 
indicating cyclical sensitivity and heterogeneous operational leverage across dismantlers.
""")

# --------------------------------------------------
# SCATTER: Size vs Profitability
# --------------------------------------------------

st.subheader("Scale vs Market Share")

fig = px.scatter(
    df_filtered,
    x="Avg Market Share",
    y="Avg Operating Margin",
    size="Avg Equity Ratio",
    hover_name="Company",
    hover_data={
        "Avg Market Share": ":.1%",
        "Avg Operating Margin": ":.1%",
        "Avg Equity Ratio": ":.1%"
    },
    height=500, 
    color_discrete_sequence=["#5A6F89"]
)

# Format axes as percentages
fig.update_yaxes(tickformat=".1%")
fig.update_xaxes(tickformat=".1%")

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# CORRELATION STATEMENT (Below the Chart)
# --------------------------------------------------

# Compute correlation
corr = df_filtered["Avg Market Share"].corr(
    df_filtered["Avg Operating Margin"]
)

st.markdown(
    f"""
    <div style="font-size: 13px;">
    Correlation between Average Market Share and Average Operating Margin (2021–2024): <strong>{corr:.2f}</strong>
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# BAR: CAGR Ranking
# --------------------------------------------------

st.subheader("Revenue CAGR (2021–2024)")

# Create a copy and classification column
cagr_df = df_filtered.sort_values("CAGR_21_24", ascending=False).copy()
cagr_df["Growth Type"] = cagr_df["CAGR_21_24"].apply(
    lambda x: "Positive Performance" if x >= 0 else "Negative Performance"
)

fig2 = px.bar(
    cagr_df,
    x="Company",
    y="CAGR_21_24",
    color="Growth Type",
    height=450,
    labels={
        "CAGR_21_24": "CAGR Y21:Y24",
        "Company": "Company",
        "Growth Type": ""
    },
    hover_data={
        "CAGR_21_24": ":.2%"
    },
    color_discrete_map={
        "Positive Performance": "#5A6F89",   # grey-blue
        "Negative Performance": "#F28B82"    # light red
    }
)

# Format Y-axis as percentage
fig2.update_yaxes(tickformat=".1%")

# Format Hover tooltip
fig2.update_traces(
    hovertemplate="%{y:.2%}<extra></extra>"
)

# Optional: remove legend title spacing for cleaner FT-style look
fig2.update_layout(legend_title_text="")

st.plotly_chart(fig2, use_container_width=True)

# --------------------------------------------------
# SCATTER: Capital Structure
# --------------------------------------------------

st.subheader("Capital Discipline: Leverage vs Equity Base")

fig3 = px.scatter(
    df_filtered,
    x="Avg Debt Ratio",
    y="Avg Equity Ratio",
    size="Avg Market Share",
    hover_name="Company",
      hover_data={
        "Avg Debt Ratio": ":.1%",
        "Avg Equity Ratio": ":.1%",
        "Avg Market Share": ":.1%"
    },
    color_discrete_sequence=["#4C566A"]
)

fig3.update_xaxes(tickformat=".0%")
fig3.update_yaxes(tickformat=".0%")

st.plotly_chart(fig3, use_container_width=True)

# --------------------------------------------------
# SCATTER: Liquidity vs Growth
# --------------------------------------------------

st.subheader("Liquidity Buffer vs Revenue Growth")

fig4 = px.scatter(
    df_filtered,
    x="Avg Liquidity Ratio",
    y="CAGR_21_24",
    size="Avg Market Share",
    hover_name="Company",
    labels={
        "CAGR_21_24": "CAGR Y21:Y24",
        "Avg Liquidity Ratio": "Avg Liquidity Ratio"
        },
    hover_data={
        "Avg Liquidity Ratio": ":.1%",
        "CAGR_21_24": ":.1%",
        "Avg Market Share": ":.1%"
    },
    color_discrete_sequence=["#4C566A"]
)

fig4.update_yaxes(tickformat=".1%")

st.plotly_chart(fig4, use_container_width=True)

# --------------------------------------------------
# TABLE
# --------------------------------------------------

st.subheader("Structural Metrics Table")

display_df = df_filtered.copy()

percent_cols = [
    "Avg Operating Margin",
    "Avg Net Margin",
    "Avg Equity Ratio",
    "Avg Debt Ratio",
    "Avg Market Share",
    "CAGR_21_24"
]

for col in percent_cols:
    display_df[col] = display_df[col] * 100

st.dataframe(
    display_df.round(2),
    use_container_width=True
)
