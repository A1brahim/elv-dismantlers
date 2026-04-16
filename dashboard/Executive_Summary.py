import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(layout="wide")

# --------------------------------------------------
# LANGUAGE SELECTOR (WITH FLAGS)
# --------------------------------------------------

st.sidebar.markdown("## 🌍 Language / Språk")

lang_display = st.sidebar.selectbox(
    "",
    options=["English 🇬🇧", "Svenska 🇸🇪"],
    index=0,
    key="language_selector"
)

# Map display label to internal language key
if lang_display.startswith("English"):
    LANG = "English"
else:
    LANG = "Svenska"

st.sidebar.markdown("---")

# --------------------------------------------------
# TRANSLATION DICTIONARY
# --------------------------------------------------

TEXT = {
    "English": {
        "page_title": "ELV Financial Structure (2021–2024)",
        "page_subtitle": "Structural financial comparison of selected Swedish End-of-Life Vehicle Dismantlers based on publicly available financial statements. Only <a href='https://sbrservice.se/skrota-din-bil-bilskrot/bildemonterare' target='_blank'>SBR-affiliated dismantling businesses</a> have been included in the analysis.",
        "filters": "Filters",
        "select_companies": "Select Companies",
        "executive_section": "Executive Summary & Key Insights (Yrs 2021–2024)",
        "no_companies": "No companies selected. Please adjust the filters.",
        "industry_growth_summary": "Industry Revenue Growth (2021–2024):",
        "structural_scale": "Structural Scale Effect:",
        "scale_profit": "Scale–Profitability Relationship:",
        "disclaimer": "This dashboard presents analytical insights derived from publicly available financial data. It is intended for informational and exploratory purposes only and does not constitute financial advice. Comprehensive firm-level analytical reports are available upon request.",
        "yoy_section_title": "Revenue Growth Dynamics (Year-over-Year)",
        "yoy_section_sub": "Firm Dispersion and Industry Trend: 2021–2024",
        "industry_avg_yoy": "Industry Average YoY Growth",
        "volatility_band": "Volatility Band",
        "year": "Year",
        "yoy_growth": "YoY Revenue Growth",
        "industry_growth_block": "Industry Revenue Growth (2021–2024):",
        "cagr_snapshot_title": "Revenue Growth Snapshot (Compound Annual Growth Rate)",
        "cagr_snapshot_sub": "Industry Baseline and Extremes: 2021–2024",
        "operating_snapshot_title": "Operating Efficiency Snapshot (Operating Margin)",
        "capital_snapshot_title": "Capital Structure Snapshot",
        "market_snapshot_title": "Market Structure Snapshot",
        "liquidity_snapshot_title": "Liquidity Snapshot",
        "momentum_snapshot_title": "Structural Momentum — Market Share Shift",
        "industry_revenue_trend": "Industry Revenue Trend (Market Size)",
        "structural_effect": "Structural Scale Effect:",
        "scale_relationship": "Scale–Profitability Relationship:",
        "insufficient_data": "Insufficient data available.",
        "no_operating_data": "No operating margin data available.",
        "insufficient_growth": "Insufficient firm-level growth data for latest year.",
        "insufficient_momentum": "Insufficient data to compute market share momentum for the latest year.",
        "yoy_summary": "Average YoY growth was **{avg}**, with typical dispersion of approximately **±{vol}** across firms. Industry growth moderated in 2023 before rebounding in 2024.",
        "cagr_summary": "**Industry CAGR (2021–2024):** {mean} | Dispersion (±1σ): {std}, suggesting indicative variation in firm-level expansion trajectories.",
        "operating_summary": "**Industry Operating Margin ({year}):** {mean} | Dispersion (±1σ): {std}, suggesting indicative differences in firm-level operating discipline.",
        "leverage_summary": "**Industry Leverage ({year}):** Debt Ratio averaged {debt}, while Debt-to-Equity averaged {dte}. Extremes indicate meaningful divergence in capital structure positioning.",
        "liquidity_summary": "**Industry Liquidity (2021–2024 Avg):** {mean} | Dispersion (±1σ): {std}. Higher liquidity suggests stronger short-term financial resilience and operational buffer capacity.",
        "market_structure_summary": "**Market Structure Interpretation ({year}):** Top 3 firms control {cr3} of total market share. An HHI of {hhi} implies effective competition equivalent to ~{eff} equally sized firms, indicating a structurally concentrated market.",
        "revenue_context_summary": "**Industry Revenue Context (2021–2024):** Total market size contracted in 2022 before rebounding in 2023 and 2024, indicating a temporal dip rather than persistent structural decline. Changes in revenue growth should therefore be interpreted against both increase in demand and firm-level execution.",
        "momentum_summary": "**Structural Momentum ({year}):** Market share redistribution totaled approximately **{redistribution}** of the industry, indicating active competitive realignment. Firms gaining share are structurally positioned to capture disproportionate future profit pools within a concentrated market.",
    },
    "Svenska": {
        "page_title": "ELV Finansiell Struktur (2021–2024)",
        "page_subtitle": "Strukturell finansiell jämförelse av utvalda svenska bilåtervinnare baserad på offentligt tillgängliga årsredovisningar. Endast <a href='https://sbrservice.se/skrota-din-bil-bilskrot/bildemonterare' target='_blank'>SBR-anslutna demonteringsverksamheter</a> har inkluderats i analysen.",
        "filters": "Filter",
        "select_companies": "Välj företag",
        "executive_section": "Sammanfattning & Nyckelinsikter (2021–2024)",
        "no_companies": "Inga företag valda. Justera filtren.",
        "industry_growth_summary": "Branschens Intäktstillväxt (2021–2024):",
        "structural_scale": "Strukturell Skaleffekt:",
        "scale_profit": "Samband mellan Storlek och Lönsamhet:",
        "disclaimer": "Denna dashboard presenterar analytiska insikter baserade på offentligt tillgänglig finansiell data. Informationen är avsedd för analytiska och explorativa ändamål och utgör inte finansiell rådgivning. Fördjupade företagsrapporter kan tillhandahållas på begäran.",
        "yoy_section_title": "Intäktstillväxt (År-för-År)",
        "yoy_section_sub": "Företagsspridning och Branschtrend: 2021–2024",
        "industry_avg_yoy": "Branschens Genomsnittliga Årstillväxt",
        "volatility_band": "Volatilitetsintervall",
        "year": "År",
        "yoy_growth": "Årlig Intäktstillväxt",
        "industry_growth_block": "Branschens Intäktstillväxt (2021–2024):",
        "cagr_snapshot_title": "Intäktstillväxt – CAGR Översikt",
        "cagr_snapshot_sub": "Branschens Baslinje och Extremer: 2021–2024",
        "operating_snapshot_title": "Operativ Effektivitet – Översikt",
        "capital_snapshot_title": "Kapitalstruktur – Översikt",
        "market_snapshot_title": "Marknadsstruktur – Översikt",
        "liquidity_snapshot_title": "Likviditet – Översikt",
        "momentum_snapshot_title": "Strukturell Dynamik – Förändring i Marknadsandel",
        "industry_revenue_trend": "Branschens Intäktstrend (Marknadsstorlek)",
        "structural_effect": "Strukturell Skaleffekt:",
        "scale_relationship": "Samband mellan Skala och Lönsamhet:",
        "insufficient_data": "Otillräcklig data tillgänglig.",
        "no_operating_data": "Ingen data för rörelsemarginal tillgänglig.",
        "insufficient_growth": "Otillräcklig företagsdata för senaste året.",
        "insufficient_momentum": "Otillräcklig data för att beräkna marknadsandelsförändring.",
        "yoy_summary": "Genomsnittlig årlig tillväxt (YoY) uppgick till **{avg}**, med en typisk spridning på cirka **±{vol}** mellan företagen. Tillväxten dämpades 2023 innan den återhämtade sig 2024.",
        "cagr_summary": "**Branschens CAGR (2021–2024):** {mean} | Spridning (±1σ): {std}, vilket indikerar variation i företagens expansion.",
        "operating_summary": "**Branschens Rörelsemarginal ({year}):** {mean} | Spridning (±1σ): {std}, vilket indikerar skillnader i operativ effektivitet mellan företag.",
        "leverage_summary": "**Branschens Skuldsättning ({year}):** Skuldkvoten uppgick i genomsnitt till {debt}, medan skuldsättningsgrad (Debt-to-Equity) uppgick till {dte}. Extremvärden indikerar tydliga skillnader i kapitalstruktur.",
        "liquidity_summary": "**Branschens Likviditet (Genomsnitt 2021–2024):** {mean} | Spridning (±1σ): {std}. Högre likviditet indikerar starkare kortsiktig finansiell motståndskraft och operativ buffertkapacitet.",
        "market_structure_summary": "**Marknadsstruktur ({year}):** De tre största företagen kontrollerar **{cr3}** av marknaden. Ett HHI på **{hhi}** motsvarar cirka {eff} lika stora aktörer, vilket indikerar en strukturellt koncentrerad marknad.",
        "revenue_context_summary": "**Intäktskontext (2021–2024):** Den totala marknadsvolymen minskade 2022 innan den återhämtade sig 2023 och 2024, vilket tyder på en temporär nedgång snarare än en strukturell försämring. Förändringar i tillväxt bör därför tolkas mot bakgrund av både efterfrågan och företagens genomförandeförmåga.",
        "momentum_summary": "**Strukturellt Momentum ({year}):** Marknadsandelsförändringar uppgick till cirka **{redistribution}** av branschen, vilket indikerar aktiv konkurrensmässig ompositionering. Företag som ökar sin andel är strukturellt positionerade för att fånga en oproportionerlig del av framtida vinstpooler."
    }
}

# Set translation dictionary after language selection
T = TEXT[LANG]


st.markdown(
    f"""
    <h1 style="margin-bottom:0.3rem;">
        {T["page_title"]}
    </h1>
    <div style="font-size:1.05rem; color:#374151; font-weight:500; margin-bottom:1.8rem; line-height:1.0;">
        {T["page_subtitle"]}
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
        "<hr style='border: none; border-top: 1.5px solid #9CA3AF; margin: 0 0 2.5rem 0;'>",
        unsafe_allow_html=True
    )

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

st.sidebar.header(T["filters"])

selected_companies = st.sidebar.multiselect(
    T["select_companies"],
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

st.markdown(f"### {T['executive_section']}")

if not df_filtered.empty:
    # Top Growth Performer
    top_growth = df_filtered.loc[df_filtered["CAGR_21_24"].idxmax()]

    # Most Operationally Stable Company
    most_stable = df_filtered.loc[df_filtered["Operating Margin Vol"].idxmin()]

    # Market Leader
    market_leader = df_filtered.loc[df_filtered["Avg Market Share"].idxmax()]

    # Correlation Insight
    corr = df_filtered["Avg Market Share"].corr(df_filtered["Avg Operating Margin"])

    revenue_col_exec = None

    if "Revenue" in df_ts_filtered.columns:
        revenue_col_exec = "Revenue"
    elif "Net sales" in df_ts_filtered.columns:
        revenue_col_exec = "Net sales"
    elif "total_revenue" in df_ts_filtered.columns:
        revenue_col_exec = "total_revenue"

    market_cagr = np.nan

    if revenue_col_exec:
        market_volume_exec = (
            df_ts_filtered.groupby("Year")[revenue_col_exec]
            .sum()
            .sort_index()
        )

        if len(market_volume_exec) >= 2:
            start_value = market_volume_exec.iloc[0]
            end_value = market_volume_exec.iloc[-1]
            periods = len(market_volume_exec) - 1

            if start_value > 0:
                market_cagr = (end_value / start_value) ** (1 / periods) - 1

    # --- Compute Absolute & % Revenue Increase (2021–2024) ---
    revenue_increase_abs = np.nan
    revenue_increase_pct = np.nan

    if revenue_col_exec and len(market_volume_exec) >= 2:
        start_value = market_volume_exec.iloc[0]
        end_value = market_volume_exec.iloc[-1]

        revenue_increase_abs = end_value - start_value

        if start_value > 0:
            revenue_increase_pct = (end_value / start_value) - 1

    col1, col2, col3, col4, col5 = st.columns(5)

    

   # Top Growth Performer
    with col1:
        st.metric(
            label="Top Growth Performer",
            value=top_growth["Company"],
            delta=f"CAGR: {top_growth['CAGR_21_24']:.1%} | Industry Avg: {industry_avg_cagr:.1%}"
        )

    # Most Operationally Stable
    with col2:
        st.metric(
            label="Most Operationally Stable",
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

    # Industry Market Growth
    with col4:
        if not np.isnan(market_cagr):
            st.metric(
                label="Industry Market Growth",
                value=f"{market_cagr:.1%}",
                delta="Revenue CAGR (2021–2024)"
            )
        else:
            st.metric(
                label="Industry Market Growth",
                value="N/A",
                delta="Revenue CAGR (2021–2024)"
            )

    # Absolute Revenue Expansion
    with col5:
        if not np.isnan(revenue_increase_abs):
            st.metric(
                label="Industry Revenue Expansion",
                value=f"{revenue_increase_abs:,.0f} SEK",
                delta=f"{revenue_increase_pct:.1%} Total Increase (2021–2024)"
            )
        else:
            st.metric(
                label="Industry Revenue Expansion",
                value="N/A",
                delta="Total Increase (2021–2024)"
            )

    # --- Compute Latest Concentration Metrics for Executive Insight ---
    latest_year_exec = df_ts_filtered["Year"].max()
    df_latest_exec = df_ts_filtered[df_ts_filtered["Year"] == latest_year_exec]

    shares_exec = df_latest_exec["Market Share"].values
    cr3_exec = np.sort(shares_exec)[-3:].sum() if len(shares_exec) >= 3 else np.nan
    hhi_exec = np.sum(shares_exec ** 2) if len(shares_exec) > 0 else np.nan

    # --------------------------------------------------
    # Executive Insight Text (Language Aware)
    # --------------------------------------------------

    if LANG == "English":
        executive_text = f"""
        <strong>Industry Insight:</strong>  
        The correlation between <em>Average Market Share</em> and <em>Average Operating Margin</em> is 
        <strong>{corr:.2f}</strong>, suggesting that scale is associated with stronger profitability across the sector. 
        Between 2021–2024, the Swedish ELV dismantling sector expanded at 
        <strong>{market_cagr:.1%}</strong> CAGR, with total revenue increasing by 
        <strong>{revenue_increase_pct:.1%}</strong>, while competitive concentration remained elevated 
        (CR3 <strong>{cr3_exec:.1%}</strong>, HHI <strong>{hhi_exec:.2f}</strong>), reinforcing scale-driven profitability dynamics.
        """
    else:
        executive_text = f"""
        <strong>Branschinsikt:</strong>  
        Korrelationskoefficienten mellan <em>Genomsnittlig Marknadsandel</em> och <em>Genomsnittlig Rörelsemarginal</em> är 
        <strong>{corr:.2f}</strong>, vilket indikerar att större marknadsandelar är förknippade med högre lönsamhet i sektorn. 
        Under perioden 2021–2024 växte den svenska ELV-demonteringssektorn med en CAGR på 
        <strong>{market_cagr:.1%}</strong>, där den totala omsättningen ökade med 
        <strong>{revenue_increase_pct:.1%}</strong>. Samtidigt förblev marknadskoncentrationen hög 
        (CR3 <strong>{cr3_exec:.1%}</strong>, HHI <strong>{hhi_exec:.2f}</strong>), vilket förstärker dynamiken där skala driver lönsamhet.
        """

    st.markdown(
        f"""
        <div style="font-size: 13px; margin-top: 10px; margin-bottom: 2.5rem; line-height: 1.6;">
            {executive_text}
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    st.warning(T["no_companies"])


# --------------------------------------------------
# YOY Growth Time Series (Companies + Mean & Volatility Band)
# --------------------------------------------------

st.markdown(
    f"""
    <h2 style="margin-bottom:0.6rem; font-size:1.4rem;">
       {T['yoy_section_title']}
    <div style="font-size:1.0rem; color:#6B7280; margin-top:0.5rem;">
        {T['yoy_section_sub']}
    </div>
    """,
    unsafe_allow_html=True
)

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
    name=T["volatility_band"],
    hoverinfo="skip"
))

# 3️⃣ Add industry mean line
fig_growth.add_trace(go.Scatter(
    x=growth_df["Year"],
    y=growth_df["mean"],
    mode="lines",
    line=dict(color="#F28B82", width=2.5),
    name=T["industry_avg_yoy"],
    hovertemplate="%{y:.2%}<extra></extra>"
))

fig_growth.update_layout(
    plot_bgcolor="white",
    xaxis_title=T["year"],
    yaxis_title=T["yoy_growth"],
    height=550,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

fig_growth.update_xaxes(
    range=[2021, 2025],
    tickmode="linear",
    dtick=1,          # step = 1 year
    tickformat="d"    # integer format (no decimals, no commas)
)

fig_growth.update_yaxes(tickformat=".1%")

st.plotly_chart(fig_growth, width="stretch")

# --------------------------------------------------
# Industry Summary Lines
# --------------------------------------------------

industry_avg = growth_df["mean"].mean()
industry_vol = growth_df["std"].mean()

st.markdown(
    f"""
    **{T['industry_growth_block']}**  
    {T['yoy_summary'].format(
        avg=f"{industry_avg:.1%}",
        vol=f"{industry_vol:.1%}"
    )}
    """
)

st.markdown(
    "<hr style='border:none; border-top:2px solid #6B7280; width:100%; margin:3rem 0 2rem 0;'>",
    unsafe_allow_html=True
)

# --------------------------------------------------
# EXECUTIVE SNAPSHOT: Revenue CAGR (2021–2024)
# --------------------------------------------------

st.markdown(
    f"""
    <h2 style="margin-bottom:0.6rem; font-size:1.4rem;">
       {T['cagr_snapshot_title']}
    <div style="font-size:1.0rem; color:#6B7280; margin-top:0.5rem;">
        {T['cagr_snapshot_sub']}
    </div>
    """,
    unsafe_allow_html=True
)

# --- Ensure sorted dataframe ---
cagr_df = df_filtered.sort_values("CAGR_21_24", ascending=False).copy()

# --- Compute metrics ---
industry_mean = cagr_df["CAGR_21_24"].mean()
industry_std = cagr_df["CAGR_21_24"].std()

top_row = cagr_df.iloc[0]
bottom_row = cagr_df.iloc[-1]

# --------------------------------------------------
# Top & Bottom Performer Cards
# --------------------------------------------------

col_left, col_right = st.columns([1, 1.4])  # Right slightly wider

with col_left:

    fig_exec_cagr = go.Figure()

    fig_exec_cagr.add_trace(go.Bar(
        x=["Industry<br>Average CAGR"],
        y=[industry_mean],
        width=0.25,  
        marker_color="#5A6F89",
        error_y=dict(
            type="data",
            array=[industry_std],
            visible=True,
            thickness=1.5,
            width=4
        ),
        hovertemplate="Industry CAGR: %{y:.2%}<extra></extra>"
    ))


    fig_exec_cagr.update_layout(
        height=450,
        plot_bgcolor="white",
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis_title="CAGR (2021–2024)",
        xaxis_title=""
    )

    fig_exec_cagr.update_yaxes(
        tickformat=".0%",
        range=[-0.5, 1.0],
        zeroline=True,
        zerolinecolor="#D1D5DB"
    )

    # Add Top Performer Dot
    fig_exec_cagr.add_trace(go.Scatter(
        x=["Leading & Lagging<br>Firms"],
        y=[top_row["CAGR_21_24"]],
        mode="markers",
        marker=dict(
        size=8,
        color="#166534",
        symbol="circle"
        ),
        name="Top Performer",
        hovertemplate=f"{top_row['Company']}: %{{y:.1%}}<extra></extra>"
    ))  

    # Add Lowest Performer Dot
    fig_exec_cagr.add_trace(go.Scatter(
        x=["Leading & Lagging<br>Firms"],
        y=[bottom_row["CAGR_21_24"]],
        mode="markers",
        marker=dict(
        size=8,
        color="#991B1B",
        symbol="circle"
        ),
        name="Lowest Performer",
        hovertemplate=f"{bottom_row['Company']}: %{{y:.1%}}<extra></extra>"
        ))
    st.plotly_chart(fig_exec_cagr, use_container_width=True)


with col_right:

    st.markdown(f"""
    <div style="padding:18px; border-radius:10px; background-color:#F0FDF4; margin-bottom:15px;">
        <div style="font-size:0.9rem; color:#6B7280;">Top Growth Performer</div>
        <div style="font-size:1.5rem; font-weight:600;">{top_row['Company']}</div>
        <div style="color:#166534; font-weight:500;">
            ↑ CAGR: {top_row['CAGR_21_24']:.1%}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding:18px; border-radius:10px; background-color:#FEF2F2;">
        <div style="font-size:0.9rem; color:#6B7280;">Lowest Growth Performer</div>
        <div style="font-size:1.5rem; font-weight:600;">{bottom_row['Company']}</div>
        <div style="color:#991B1B; font-weight:500;">
            ↓ CAGR: {bottom_row['CAGR_21_24']:.1%}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------
# Short Executive Insight
# --------------------------------------------------

st.markdown(
    T["cagr_summary"].format(
        mean=f"{industry_mean:.1%}",
        std=f"{industry_std:.1%}"
    )
)
st.markdown(
    "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
    unsafe_allow_html=True
)

# ==================================================
# OPERATING EFFICIENCY SNAPSHOT (2024)
# ==================================================

from src.metrics.operating_efficiency import (
    compute_operating_margin,
    compute_latest_operating_margin_ranking,
)

st.markdown(
    f"""
    <h2 style="margin-bottom:0.6rem; font-size:1.4rem;">
       {T['operating_snapshot_title']}
    <div style="font-size:1.0rem; color:#6B7280; margin-top:0.5rem;">
        Industry Baseline and Extremes — Latest Year
    </div>
    """,
    unsafe_allow_html=True
)

@st.cache_data
def load_operating_data():
    return pd.read_csv("dashboard/balance_sheet_yearly.csv")

df_operating = load_operating_data()
df_operating = compute_operating_margin(df_operating)

latest_ranking, latest_year = compute_latest_operating_margin_ranking(df_operating)

if latest_ranking.empty:
    st.warning(T["no_operating_data"])
else:

    industry_mean_op = latest_ranking["operating_margin"].mean()
    industry_std_op = latest_ranking["operating_margin"].std()

    top_op = latest_ranking.sort_values(
        "operating_margin", ascending=False
    ).iloc[0]

    bottom_op = latest_ranking.sort_values(
        "operating_margin"
    ).iloc[0]

    col_left, col_right = st.columns([1, 1.4])

    # --------------------------------------------------
    # LEFT COLUMN — Industry Baseline Chart
    # --------------------------------------------------

    with col_left:

        fig_exec_op = go.Figure()

        fig_exec_op.add_trace(go.Bar(
            x=["Industry<br>Average Margin"],
            y=[industry_mean_op],
            width=0.2,
            marker_color="#73879F",
            error_y=dict(
                type="data",
                array=[industry_std_op],
                visible=True,
                thickness=1.5,
                width=3
            ),
            hovertemplate="Industry Mean: %{y:.2%}<extra></extra>"
        ))

        fig_exec_op.add_trace(go.Scatter(
            x=["Leading & Lagging<br>Firms"],
            y=[top_op["operating_margin"]],
            mode="markers",
            marker=dict(size=10, color="#166534"),
            hovertemplate=f"{top_op['company']}: {top_op['operating_margin']:.2%}<extra></extra>"
        ))

        fig_exec_op.add_trace(go.Scatter(
            x=["Leading & Lagging<br>Firms"],
            y=[bottom_op["operating_margin"]],
            mode="markers",
            marker=dict(size=10, color="#991B1B"),
            hovertemplate=f"{bottom_op['company']}: {bottom_op['operating_margin']:.2%}<extra></extra>"
        ))

        fig_exec_op.update_yaxes(
            range=[-0.15, 0.30],
            tickformat=".0%",
            zeroline=True,
            zerolinewidth=1
        )

        fig_exec_op.update_layout(
            showlegend=False,
            height=450,
            margin=dict(l=20, r=20, t=20, b=20)
        )

        st.plotly_chart(fig_exec_op, use_container_width=True)

    # --------------------------------------------------
    # RIGHT COLUMN — Performer Cards
    # --------------------------------------------------

    with col_right:

        st.markdown(f"""
        <div style="padding:18px; border-radius:10px; background-color:#F0FDF4; margin-bottom:15px;">
            <div style="font-size:0.9rem; color:#6B7280;">
                Top Operating Margin ({latest_year})
            </div>
            <div style="font-size:1.5rem; font-weight:600;">
                {top_op['company']}
            </div>
            <div style="color:#166534; font-weight:500;">
                ↑ Margin: {top_op['operating_margin']:.1%}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="padding:18px; border-radius:10px; background-color:#FEF2F2;">
            <div style="font-size:0.9rem; color:#6B7280;">
                Lowest Operating Margin ({latest_year})
            </div>
            <div style="font-size:1.5rem; font-weight:600;">
                {bottom_op['company']}
            </div>
            <div style="color:#991B1B; font-weight:500;">
                ↓ Margin: {bottom_op['operating_margin']:.1%}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        T["operating_summary"].format(
            year=latest_year,
            mean=f"{industry_mean_op:.1%}",
            std=f"{industry_std_op:.1%}"
        )
    )
    st.markdown(
        "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
        unsafe_allow_html=True
    )


# ==================================================
# CAPITAL STRUCTURE SNAPSHOT (Latest Year)
# ==================================================

from src.metrics.balance_sheet import compute_latest_capital_structure

st.markdown(
    f"""
    <h2 style="margin-bottom:0.6rem; font-size:1.4rem;">
       {T['capital_snapshot_title']}
    <div style="font-size:1.0rem; color:#6B7280; margin-top:0.5rem;">
        Industry Baseline and Extremes — Latest Year
    </div>
    """,
    unsafe_allow_html=True
)

capital_df, capital_year = compute_latest_capital_structure()

industry_mean_debt = capital_df["debt_ratio"].mean()
industry_mean_dte = capital_df["debt_to_equity"].mean()

top_debt = capital_df.sort_values("debt_ratio", ascending=False).iloc[0]
bottom_debt = capital_df.sort_values("debt_ratio").iloc[0]

top_dte = capital_df.sort_values("debt_to_equity", ascending=False).iloc[0]
bottom_dte = capital_df.sort_values("debt_to_equity").iloc[0]


col_debt, col_dte, col_cards = st.columns([0.5, 0.5, 1.3])

# --------------------------------------------------
# COLUMN 1 — Debt Ratio Industry Bar
# --------------------------------------------------

with col_debt:

    fig_debt = go.Figure()

    fig_debt.add_trace(go.Bar(
        x=["Industry Mean<br>Debt Ratio"],
        y=[industry_mean_debt],
        marker_color="#73879F",
        width=0.25,
        hovertemplate="Debt Ratio: %{y:.1%}<extra></extra>"
    ))

    fig_debt.update_layout(
        showlegend=False,
        height=450,
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis_title="Debt Ratio"
    )

    fig_debt.update_yaxes(
        range=[0, 1.0],
        tickformat=".0%")

    st.plotly_chart(fig_debt, use_container_width=True)

# --------------------------------------------------
# COLUMN 2 — Debt-to-Equity Industry Bar
# --------------------------------------------------

with col_dte:

    fig_dte = go.Figure()

    fig_dte.add_trace(go.Bar(
        x=["Industry Mean<br>Debt-to-Equity"],
        y=[industry_mean_dte],
        marker_color="#73879F",
        width=0.25,
        hovertemplate="Debt-to-Equity: %{y:.2f}x<extra></extra>"
    ))

    fig_dte.update_layout(
        showlegend=False,
        height=450,
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis_title="Debt-to-Equity Ratio"
    )

    # IMPORTANT: Do NOT format as percentage
    fig_dte.update_yaxes(
        range=[0, 20.0],
        dtick=2.5,
        tickformat=None)

    st.plotly_chart(fig_dte, use_container_width=True)

# --------------------------------------------------
# COLUMN 3 — Extremes Cards
# --------------------------------------------------

with col_cards:

    st.markdown(f"""
    <div style="padding:18px; border-radius:10px; background-color:#F0FDF4; margin-bottom:15px;">
        <div style="font-size:0.9rem; color:#6B7280;">
            Lowest Debt Ratio ({capital_year})
        </div>
        <div style="font-size:1.3rem; font-weight:600;">
            {bottom_debt['company']}
        </div>
        <div style="color:#166534; font-weight:500;">
            ↓ {bottom_debt['debt_ratio']:.1%}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding:18px; border-radius:10px; background-color:#FEF2F2; margin-bottom:15px;">
        <div style="font-size:0.9rem; color:#6B7280;">
            Highest Debt Ratio ({capital_year})
        </div>
        <div style="font-size:1.3rem; font-weight:600;">
            {top_debt['company']}
        </div>
        <div style="color:#991B1B; font-weight:500;">
            ↑ {top_debt['debt_ratio']:.1%}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding:18px; border-radius:10px; background-color:#F0FDF4;">
        <div style="font-size:0.9rem; color:#6B7280;">
            Lowest Debt-to-Equity ({capital_year})
        </div>
        <div style="font-size:1.3rem; font-weight:600;">
            {bottom_dte['company']}
        </div>
        <div style="color:#166534; font-weight:500;">
            ↓ {bottom_dte['debt_to_equity']:.2f}x
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding:18px; border-radius:10px; background-color:#FEF2F2; margin-bottom:15px;">
        <div style="font-size:0.9rem; color:#6B7280;">
            Highest Debt-to-Equity ({capital_year})
        </div>
        <div style="font-size:1.3rem; font-weight:600;">
            {top_dte['company']}
        </div>
        <div style="color:#991B1B; font-weight:500;">
            ↑ {top_dte['debt_to_equity']:.2f}x
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(
    T["leverage_summary"].format(
        year=capital_year,
        debt=f"{industry_mean_debt:.1%}",
        dte=f"{industry_mean_dte:.2f}"
    )
)
st.markdown(
    "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
    unsafe_allow_html=True
)

# --------------------------------------------------
# SCATTER: Size vs Profitability
# --------------------------------------------------

st.markdown(
    f"""
    <h2 style="margin-bottom:0.6rem; font-size:1.4rem;">
       {T['operating_snapshot_title']}
    <div style="font-size:1.0rem; color:#6B7280; margin-top:0.5rem;">
        Industry Baseline and Extremes — Latest Year
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# Compute Industry Means
# --------------------------------------------------

share_mean = df_filtered["Avg Market Share"].mean()
margin_mean = df_filtered["Avg Operating Margin"].mean()

# Classification: Above both means vs others
df_plot = df_filtered.copy()

df_plot["Position"] = df_plot.apply(
    lambda row: (
        "Leaders (Above Share & Margin)"
        if (row["Avg Market Share"] >= share_mean) and
           (row["Avg Operating Margin"] >= margin_mean)
        else "Below Structural Threshold"
    ),
    axis=1
)

# --------------------------------------------------
# Scatter Plot 
# --------------------------------------------------

fig = px.scatter(
    df_plot,
    x="Avg Market Share",
    y="Avg Operating Margin",
    size="Avg Equity Ratio",
    hover_name="Company",
    color="Position",
    color_discrete_map={
        "Leaders (Above Share & Margin)": "#5A6F89",
        "Below Structural Threshold": "#F28B82"
    },
    hover_data={
        "Avg Market Share": ":.1%",
        "Avg Operating Margin": ":.1%",
        "Avg Equity Ratio": ":.1%"
    },
    height=550
)

fig.update_yaxes(tickformat=".1%")
fig.update_xaxes(tickformat=".1%")

# --------------------------------------------------
# Single Regression Line (All Observations)
# --------------------------------------------------

x = df_plot["Avg Market Share"]
y = df_plot["Avg Operating Margin"]

# Fit linear regression
slope, intercept = np.polyfit(x, y, 1)

x_line = np.linspace(x.min(), x.max(), 100)
y_line = slope * x_line + intercept

fig.add_trace(
    go.Scatter(
        x=x_line,
        y=y_line,
        mode="lines",
        line=dict(color="#F28B82", width=2.5),
        name="Industry Regression Line",
        hoverinfo="skip"
    )
)

# --------------------------------------------------
# Add Industry Mean Lines (Quadrant Mapping)
# --------------------------------------------------

# Vertical mean line (Market Share)
fig.add_shape(
    type="line",
    x0=share_mean,
    x1=share_mean,
    y0=df_plot["Avg Operating Margin"].min(),
    y1=df_plot["Avg Operating Margin"].max(),
    line=dict(color="#9AA3AF", width=2)
)

fig.add_annotation(
    x=share_mean,
    y=df_plot["Avg Operating Margin"].max(),
    text=f"Market Share<br>Industry Mean<br>({share_mean:.1%})",
    showarrow=False,
    xanchor="left",
    yanchor="bottom",
    font=dict(size=11, color="#6B7280")
)

# Horizontal mean line (Operating Margin)
fig.add_shape(
    type="line",
    x0=df_plot["Avg Market Share"].min(),
    x1=df_plot["Avg Market Share"].max(),
    y0=margin_mean,
    y1=margin_mean,
    line=dict(color="#9AA3AF", width=2)
)

fig.add_annotation(
    x=df_plot["Avg Market Share"].max(),
    y=margin_mean,
    text=f"Operating Margin<br>Industry Mean<br>({margin_mean:.1%})",
    showarrow=False,
    xanchor="right",
    yanchor="top",
    font=dict(size=11, color="#6B7280")
)

fig.update_layout(
    legend_title_text="Structural Position",
    plot_bgcolor="white"
)


st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# Operating Efficiency Highlight Cards
# --------------------------------------------------

top_margin = df_filtered.loc[df_filtered["Avg Operating Margin"].idxmax()]
bottom_margin = df_filtered.loc[df_filtered["Avg Operating Margin"].idxmin()]

col_eff1, col_eff2 = st.columns(2)

with col_eff1:
    st.markdown(f"""
    <div style="padding:18px; border-radius:10px; background-color:#F0FDF4; margin-bottom:15px;">
        <div style="font-size:0.9rem; color:#6B7280;">
            Highest Operating Efficiency (2021–2024 Avg)
        </div>
        <div style="font-size:1.4rem; font-weight:600;">
            {top_margin['Company']}
        </div>
        <div style="color:#166534; font-weight:500;">
            ↑ Margin: {top_margin['Avg Operating Margin']:.1%}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_eff2:
    st.markdown(f"""
    <div style="padding:18px; border-radius:10px; background-color:#FEF2F2; margin-bottom:15px;">
        <div style="font-size:0.9rem; color:#6B7280;">
            Lowest Operating Efficiency (2021–2024 Avg)
        </div>
        <div style="font-size:1.4rem; font-weight:600;">
            {bottom_margin['Company']}
        </div>
        <div style="color:#991B1B; font-weight:500;">
            ↓ Margin: {bottom_margin['Avg Operating Margin']:.1%}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------
# Two-Line Executive Summary
# --------------------------------------------------

corr = df_filtered["Avg Market Share"].corr(
    df_filtered["Avg Operating Margin"]
)

st.markdown(
    f"""
    **{T['structural_effect']}** Firms above the industry means in both market share ({share_mean:.1%}) 
    and operating margin ({margin_mean:.1%}) occupy the structural leadership quadrant.
    **{T['scale_relationship']}** The correlation between scale and operating margin is 
    **{corr:.2f}**, indicating that larger firms tend to exhibit stronger operating efficiency.
    """
)
st.markdown(
    "<hr style='border:none; border-top:2px solid #6B7280; width:100%; margin:3rem 0 2rem 0;'>",
    unsafe_allow_html=True
)


# ==================================================
# LIQUIDITY SNAPSHOT (2021–2024 Average)
# ==================================================

st.markdown(
    f"""
    <h2 style="margin-bottom:0.6rem; font-size:1.4rem;">
       {T['liquidity_snapshot_title']}
    <div style="font-size:1.0rem; color:#6B7280; margin-top:0.5rem;">
        Industry Baseline and Extremes — 2021–2024 Average
    </div>
    """,
    unsafe_allow_html=True
)

# Compute liquidity metrics
industry_mean_liq = df_filtered["Avg Liquidity Ratio"].mean()
industry_std_liq = df_filtered["Avg Liquidity Ratio"].std()

top_liq = df_filtered.sort_values("Avg Liquidity Ratio", ascending=False).iloc[0]
bottom_liq = df_filtered.sort_values("Avg Liquidity Ratio").iloc[0]

col_liq_left, col_liq_right = st.columns([1, 1.4])

# --------------------------------------------------
# LEFT COLUMN — Industry Liquidity Baseline
# --------------------------------------------------

with col_liq_left:

    fig_liq = go.Figure()

    fig_liq.add_trace(go.Bar(
        x=["Industry<br>Average Liquidity"],
        y=[industry_mean_liq],
        width=0.2,
        marker_color="#73879F",
        error_y=dict(
            type="data",
            array=[industry_std_liq],
            visible=True,
            thickness=1.5,
            width=3
        ),
        hovertemplate="Industry Liquidity: %{y:.2f}x<extra></extra>"
    ))

    fig_liq.add_trace(go.Scatter(
        x=["Leading & Lagging<br>Firms"],
        y=[top_liq["Avg Liquidity Ratio"]],
        mode="markers",
        marker=dict(size=8, color="#166534"),
        hovertemplate=f"{top_liq['Company']}: {top_liq['Avg Liquidity Ratio']:.2f}x<extra></extra>"
    ))

    fig_liq.add_trace(go.Scatter(
        x=["Leading & Lagging<br>Firms"],
        y=[bottom_liq["Avg Liquidity Ratio"]],
        mode="markers",
        marker=dict(size=8, color="#991B1B"),
        hovertemplate=f"{bottom_liq['Company']}: {bottom_liq['Avg Liquidity Ratio']:.2f}x<extra></extra>"
    ))

    fig_liq.update_layout(
        showlegend=False,
        height=450,
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis_title="Liquidity Ratio (x)"
    )

    fig_liq.update_yaxes(
        range=[0, df_filtered["Avg Liquidity Ratio"].max() * 1.5]
    )

    st.plotly_chart(fig_liq, use_container_width=True)
   

# --------------------------------------------------
# RIGHT COLUMN — Extremes Cards
# --------------------------------------------------

with col_liq_right:

    st.markdown(f"""
    <div style="padding:18px; border-radius:10px; background-color:#F0FDF4; margin-bottom:15px;">
        <div style="font-size:0.9rem; color:#6B7280;">
            Highest Liquidity (2021–2024 Avg)
        </div>
        <div style="font-size:1.4rem; font-weight:600;">
            {top_liq['Company']}
        </div>
        <div style="color:#166534; font-weight:500;">
            ↑ Liquidity: {top_liq['Avg Liquidity Ratio']:.2f}x
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding:18px; border-radius:10px; background-color:#FEF2F2;">
        <div style="font-size:0.9rem; color:#6B7280;">
            Lowest Liquidity (2021–2024 Avg)
        </div>
        <div style="font-size:1.4rem; font-weight:600;">
            {bottom_liq['Company']}
        </div>
        <div style="color:#991B1B; font-weight:500;">
            ↓ Liquidity: {bottom_liq['Avg Liquidity Ratio']:.2f}x
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # Contextual Reference: Key Structural Firms (Card Style)
    # --------------------------------------------------

    reference_firms = [
        "Örebro Bildemontering AB",
        "Autocirc Svensk Bilåtervinning AB"
    ]

    reference_display = df_filtered[
        df_filtered["Company"].isin(reference_firms)
    ][["Company", "Avg Liquidity Ratio"]]
    reference_display = reference_display.sort_values(
        "Avg Liquidity Ratio", ascending=False
    ).reset_index(drop=True)

    for idx, row in reference_display.iterrows():
        st.markdown(f"""
        <div style="padding:14px; border-radius:10px; 
                    background-color:#F3F4F6; 
                    margin-top:10px;">
            <div style="font-size:0.85rem; color:#6B7280;">
                Reference Firm — Liquidity Position
            </div>
            <div style="font-size:1.2rem; font-weight:500;">
                {row['Company']}
            </div>
            <div style="color:#6B7280; font-weight:500;">
                Liquidity: {row['Avg Liquidity Ratio']:.2f}x
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown(
    T["liquidity_summary"].format(
        mean=f"{industry_mean_liq:.2f}x",
        std=f"{industry_std_liq:.2f}x"
    )
)

st.markdown(
    "<hr style='border:none; border-top:2px solid #6B7280; width:100%; margin:3rem 0 2rem 0;'>",
    unsafe_allow_html=True
)

 # ==================================================
 # MARKET STRUCTURE SNAPSHOT (Latest Year)
 # ==================================================

st.markdown(
    f"""
    <h2 style="margin-bottom:0.6rem; font-size:1.4rem;">
       {T['market_snapshot_title']}
    <div style="font-size:1.0rem; color:#6B7280; margin-top:0.5rem;">
        Industry Baseline and Concentration — Latest Year
    </div>
    """,
    unsafe_allow_html=True
)

# --- Use latest year available in time-series ---
latest_year_ms = df_ts_filtered["Year"].max()
df_latest_ms = df_ts_filtered[df_ts_filtered["Year"] == latest_year_ms].copy()

industry_mean_share = df_latest_ms["Market Share"].mean()
industry_std_share = df_latest_ms["Market Share"].std()

top_share = df_latest_ms.sort_values("Market Share", ascending=False).iloc[0]
bottom_share = df_latest_ms.sort_values("Market Share").iloc[0]

# --- Concentration Metrics ---
shares = df_latest_ms["Market Share"].values
cr3 = np.sort(shares)[-3:].sum()
hhi = np.sum(shares ** 2)
effective_firms = 1 / hhi if hhi > 0 else np.nan

col_ms_left, col_ms_right = st.columns([1, 1.4])

# --------------------------------------------------
# LEFT — Industry Baseline Chart
# --------------------------------------------------

with col_ms_left:

    fig_ms = go.Figure()

    fig_ms.add_trace(go.Bar(
        x=["Industry<br>Average Share"],
        y=[industry_mean_share],
        width=0.25,
        marker_color="#73879F",
        error_y=dict(
            type="data",
            array=[industry_std_share],
            visible=True,
            thickness=1.5,
            width=3
        ),
        hovertemplate="Industry Mean: %{y:.2%}<extra></extra>"
    ))

    fig_ms.add_trace(go.Scatter(
        x=["Leading & Lagging<br>Firms"],
        y=[top_share["Market Share"]],
        mode="markers",
        marker=dict(size=9, color="#166534"),
        hovertemplate=f"{top_share['Company']}: {top_share['Market Share']:.2%}<extra></extra>"
    ))

    fig_ms.add_trace(go.Scatter(
        x=["Leading & Lagging<br>Firms"],
        y=[bottom_share["Market Share"]],
        mode="markers",
        marker=dict(size=9, color="#991B1B"),
        hovertemplate=f"{bottom_share['Company']}: {bottom_share['Market Share']:.2%}<extra></extra>"
    ))

    fig_ms.update_layout(
        showlegend=False,
        height=450,
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis_title="Market Share"
    )

    fig_ms.update_yaxes(tickformat=".0%")

    st.plotly_chart(fig_ms, use_container_width=True)
   

# --------------------------------------------------
# RIGHT — Leader & Concentration Cards
# --------------------------------------------------

with col_ms_right:

    st.markdown(f"""
    <div style="padding:18px; border-radius:10px; background-color:#F0FDF4; margin-bottom:15px;">
        <div style="font-size:0.9rem; color:#6B7280;">
            Market Leader ({latest_year_ms})
        </div>
        <div style="font-size:1.4rem; font-weight:600;">
            {top_share['Company']}
        </div>
        <div style="color:#166534; font-weight:500;">
            ↑ Share: {top_share['Market Share']:.2%}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding:18px; border-radius:10px; background-color:#FEF2F2; margin-bottom:15px;">
        <div style="font-size:0.9rem; color:#6B7280;">
            Lowest Market Position ({latest_year_ms})
        </div>
        <div style="font-size:1.4rem; font-weight:600;">
            {bottom_share['Company']}
        </div>
        <div style="color:#991B1B; font-weight:500;">
            ↓ Share: {bottom_share['Market Share']:.2%}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding:16px; border-radius:10px; background-color:#F3F4F6; margin-bottom:10px;">
        <div style="font-size:0.9rem; color:#6B7280;">
            CR3 (Top 3 Share) — {latest_year_ms}
        </div>
        <div style="font-size:1.3rem; font-weight:600;">
            {cr3:.2%}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding:16px; border-radius:10px; background-color:#F3F4F6;">
        <div style="font-size:0.9rem; color:#6B7280;">
            HHI & Effective Firms — {latest_year_ms}
        </div>
        <div style="font-size:1.2rem; font-weight:600;">
            HHI: {hhi:.2f}
        </div>
        <div style="color:#6B7280;">
            Effective Firms: {effective_firms:.1f}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(
    T["market_structure_summary"].format(
        year=latest_year_ms,
        cr3=f"{cr3:.1%}",
        hhi=f"{hhi:.2f}",
        eff=f"{effective_firms:.1f}"
    )
)

st.markdown(
    "<hr style='border:none; border-top:2px solid #6B7280; width:100%; margin:3rem 0 2rem 0;'>",
    unsafe_allow_html=True
)


# ==================================================
# INDUSTRY MARKET VOLUME (Total Revenue)
# ==================================================

st.markdown(
    f"""
    <h2 style="margin-bottom:0.6rem; font-size:1.4rem;">
       {T['industry_revenue_trend']}
    <div style="font-size:1.0rem; color:#6B7280; margin-top:0.5rem;">
        Industry Revenue Expansion and Competitive Positioning (2021–2024)
    </div>
    """,
    unsafe_allow_html=True
)


# Ensure correct revenue column name
revenue_col = None

if "Revenue" in df_ts_filtered.columns:
    revenue_col = "Revenue"
elif "Net sales" in df_ts_filtered.columns:
    revenue_col = "Net sales"
elif "total_revenue" in df_ts_filtered.columns:
    revenue_col = "total_revenue"
else:
    st.error("No revenue column found in time-series dataset.")
    st.stop()

market_volume = (
    df_ts_filtered.groupby("Year")[revenue_col]
    .sum()
    .reset_index()
)


fig_volume = go.Figure()

# --- Compute YoY Growth ---
market_volume = market_volume.sort_values("Year").copy()
market_volume["YoY Growth"] = market_volume[revenue_col].pct_change()

# --- Line Chart ---
fig_volume.add_trace(go.Scatter(
    x=market_volume["Year"],
    y=market_volume[revenue_col],
    mode="lines+markers",
    line=dict(color="#5A6F89", width=2),
    marker=dict(size=8),
    name="Total Industry Revenue",
    hovertemplate="Revenue: %{y:,.0f} SEK<extra></extra>"
))

# --- Annotate YoY % ---
for i in range(1, len(market_volume)):
    year = market_volume.loc[i, "Year"]
    value = market_volume.loc[i, revenue_col]
    yoy = market_volume.loc[i, "YoY Growth"]

    fig_volume.add_annotation(
        x=year,
        y=value,
        text=f"<b>{yoy:.1%}</b>",
        showarrow=False,
        yshift=25,
        yanchor="bottom",
        font=dict(size=13, color="#991B1B" if yoy < 0 else "#166534")
    )

fig_volume.update_layout(
    plot_bgcolor="white",
    height=550,
    showlegend=False,
    margin=dict(l=20, r=20, t=20, b=20),
    xaxis_title="Year",
    yaxis_title="Total Industry Revenue (SEK)"
)

# --- Explicit Axis Control ---
fig_volume.update_xaxes(
    range=[2020, 2025],
    tickmode="linear",
    dtick=1,
    tickformat="d"
)

fig_volume.update_yaxes(
    range=[125000, 250000],
    tickmode="array",
    tickvals=[125000, 150000, 175000, 200000, 225000, 250000],
    ticktext=["125K", "150K", "175K", "200K", "225K", "250K"]
)


col_vol_left, col_vol_right = st.columns([1, 1.4])

with col_vol_left:
    st.plotly_chart(fig_volume, use_container_width=True)
    

with col_vol_right:

    # --- Compute latest year firm-level YoY growth ---
    df_company_growth = df_ts_filtered.sort_values(["Company", "Year"]).copy()
    df_company_growth["YoY"] = (
        df_company_growth.groupby("Company")[revenue_col].pct_change()
    )

    latest_year_growth = df_company_growth["Year"].max()

    df_latest_growth = df_company_growth[
        df_company_growth["Year"] == latest_year_growth
    ].dropna(subset=["YoY"])

    if not df_latest_growth.empty:

        top_growth_firm = df_latest_growth.sort_values("YoY", ascending=False).iloc[0]
        bottom_growth_firm = df_latest_growth.sort_values("YoY").iloc[0]

        st.markdown(f"""
        <div style="padding:18px; border-radius:10px; background-color:#F0FDF4; margin-bottom:15px;">
            <div style="font-size:0.9rem; color:#6B7280;">
                Highest Revenue Growth ({latest_year_growth})
            </div>
            <div style="font-size:1.3rem; font-weight:600;">
                {top_growth_firm['Company']}
            </div>
            <div style="color:#166534; font-weight:500;">
                ↑ YoY Growth: {top_growth_firm['YoY']:.1%}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="padding:18px; border-radius:10px; background-color:#FEF2F2;">
            <div style="font-size:0.9rem; color:#6B7280;">
                Lowest Revenue Growth ({latest_year_growth})
            </div>
            <div style="font-size:1.3rem; font-weight:600;">
                {bottom_growth_firm['Company']}
            </div>
            <div style="color:#991B1B; font-weight:500;">
                ↓ YoY Growth: {bottom_growth_firm['YoY']:.1%}
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.info(T["insufficient_growth"])

    # --------------------------------------------------
    # Structural Scale — Total Revenue (2021–2024)
    # --------------------------------------------------

    df_total_period = (
        df_ts_filtered
        .groupby("Company")[revenue_col]
        .sum()
        .reset_index()
        .sort_values(revenue_col, ascending=False)
    )

    if not df_total_period.empty:

        top_revenue_firm = df_total_period.iloc[0]
        bottom_revenue_firm = df_total_period.iloc[-1]

        st.markdown("""
        <div style="margin-top:25px; font-size:0.95rem; color:#6B7280;">
            Structural Scale (Cumulative Revenue 2021–2024)
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="padding:18px; border-radius:10px; background-color:#F3F4F6; margin-top:10px; margin-bottom:15px;">
            <div style="font-size:0.9rem; color:#6B7280;">
                Highest Total Revenue (2021–2024)
            </div>
            <div style="font-size:1.3rem; font-weight:600;">
                {top_revenue_firm['Company']}
            </div>
            <div style="color:#6B7280; font-weight:500;">
                Total Revenue: {top_revenue_firm[revenue_col]:,.0f} SEK
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="padding:18px; border-radius:10px; background-color:#F3F4F6; margin-bottom:15px;">
            <div style="font-size:0.9rem; color:#6B7280;">
                Lowest Total Revenue (2021–2024)
            </div>
            <div style="font-size:1.3rem; font-weight:600;">
                {bottom_revenue_firm['Company']}
            </div>
            <div style="color:#6B7280; font-weight:500;">
                Total Revenue: {bottom_revenue_firm[revenue_col]:,.0f} SEK
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown(T["revenue_context_summary"])



st.markdown(
    "<hr style='border:none; border-top:2px solid #6B7280; width:100%; margin:3rem 0 2rem 0;'>",
    unsafe_allow_html=True
)


 # ==================================================
 # STRUCTURAL MOMENTUM: CHANGE IN MARKET SHARE
 # ==================================================

st.markdown(
    f"""
    <h2 style="margin-bottom:0.6rem; font-size:1.4rem;">
       {T['momentum_snapshot_title']}
    <div style="font-size:1.0rem; color:#6B7280; margin-top:0.5rem;">
        Growth-Adjusted Market Share Momentum (Latest Year)
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# Compute Δ Market Share (Latest Year vs Previous)
# --------------------------------------------------

# Ensure proper sorting for time-based calculations
df_ts_momentum = df_ts_filtered.sort_values(["Company", "Year"]).copy()

# Calculate year-over-year change in market share
df_ts_momentum["delta_share"] = (
    df_ts_momentum.groupby("Company")["Market Share"].diff()
)

# Identify the latest year and filter corresponding data
latest_year_momentum = df_ts_momentum["Year"].max()
df_momentum_latest = df_ts_momentum[
    df_ts_momentum["Year"] == latest_year_momentum
].dropna(subset=["delta_share"])

if not df_momentum_latest.empty:

    # Firm with the largest gain and largest loss in market share
    top_gainer = df_momentum_latest.sort_values(
        "delta_share", ascending=False
    ).iloc[0]

    top_loser = df_momentum_latest.sort_values(
        "delta_share"
    ).iloc[0]

    # Net industry momentum (sum of absolute redistributions / 2)
    net_redistribution = df_momentum_latest["delta_share"].abs().sum() / 2

    # Compute total gains and total losses in market share
    total_gains = df_momentum_latest.loc[
        df_momentum_latest["delta_share"] > 0, "delta_share"
    ].sum()

    total_losses = df_momentum_latest.loc[
        df_momentum_latest["delta_share"] < 0, "delta_share"
    ].sum()

    # --------------------------------------------------
    # LEFT/RIGHT COLUMN LAYOUT
    # --------------------------------------------------
    col_mom_left, col_mom_right = st.columns([1, 1.4])

    # --------------------------------------------------
    # LEFT COLUMN — Industry Redistribution Intensity
    # --------------------------------------------------
    with col_mom_left:

        fig_momentum = go.Figure()

        # Add bar for total gains (green)
        fig_momentum.add_trace(go.Bar(
            x=["Total<br>Market<br>Gains"],
            y=[total_gains],
            width=0.2,
            marker_color="#166534",
            hovertemplate="Total Gains: %{y:.2%}<extra></extra>"
        ))

        # Add bar for total losses (red)
        fig_momentum.add_trace(go.Bar(
            x=["Total<br>Market<br>Losses"],
            y=[total_losses],
            width=0.2,
            marker_color="#991B1B",
            hovertemplate="Total Losses: %{y:.2%}<extra></extra>"
        ))

        # Add top gainer and loser scatter points
        fig_momentum.add_trace(go.Scatter(
            x=["Leading & Lagging<br>Firms"],
            y=[top_gainer["delta_share"]],
            mode="markers",
            marker=dict(size=9, color="#166534"),
            hovertemplate=f"{top_gainer['Company']}: %{{y:.2%}}<extra></extra>"
        ))

        fig_momentum.add_trace(go.Scatter(
            x=["Leading & Lagging<br>Firms"],
            y=[top_loser["delta_share"]],
            mode="markers",
            marker=dict(size=9, color="#991B1B"),
            hovertemplate=f"{top_loser['Company']}: %{{y:.2%}}<extra></extra>"
        ))

        fig_momentum.update_layout(
            showlegend=False,
            height=450,
            margin=dict(l=20, r=20, t=20, b=20),
            yaxis_title="Redistribution Intensity"
        )

        # Set y-axis range to show both positive/negative momentum
        max_move = max(
            abs(total_gains),
            abs(total_losses),
            abs(top_gainer["delta_share"]),
            abs(top_loser["delta_share"])
        )

        fig_momentum.update_yaxes(
            tickformat=".1%",
            range=[-max_move * 1.5, max_move * 1.5]
        )

        st.plotly_chart(fig_momentum, use_container_width=True)
        

    # --------------------------------------------------
    # RIGHT COLUMN — Top Gainer & Loser Cards (stacked)
    # --------------------------------------------------
    with col_mom_right:
        st.markdown(f"""
        <div style="padding:18px; border-radius:10px; background-color:#F0FDF4; margin-bottom:15px;">
            <div style="font-size:0.9rem; color:#6B7280;">
                Largest Market Share Gainer ({latest_year_momentum})
            </div>
            <div style="font-size:1.4rem; font-weight:600;">
                {top_gainer['Company']}
            </div>
            <div style="color:#166534; font-weight:500;">
                ↑ Δ Share: {top_gainer['delta_share']:.2%}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="padding:18px; border-radius:10px; background-color:#FEF2F2; margin-bottom:15px;">
            <div style="font-size:0.9rem; color:#6B7280;">
                Largest Market Share Decline ({latest_year_momentum})
            </div>
            <div style="font-size:1.4rem; font-weight:600;">
                {top_loser['Company']}
            </div>
            <div style="color:#991B1B; font-weight:500;">
                ↓ Δ Share: {top_loser['delta_share']:.2%}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --------------------------------------------------
    # Executive Interpretation
    # --------------------------------------------------
    st.markdown(
        T["momentum_summary"].format(
            year=latest_year_momentum,
            redistribution=f"{net_redistribution:.2%}"
        )
    )
else:
    st.info(T["insufficient_momentum"])

st.markdown(
    "<hr style='border:none; border-top:2px solid #6B7280; width:100%; margin:3rem 0 2rem 0;'>",
    unsafe_allow_html=True
)

# -------------------------------------------------
# Public Dashboard Disclaimer
# -------------------------------------------------
st.markdown("---")
st.markdown(
    f"**{T['disclaimer']}**",
    unsafe_allow_html=True
)