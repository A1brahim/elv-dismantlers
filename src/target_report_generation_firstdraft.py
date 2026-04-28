# -------------------------------------------------
# TARGET REPORT GENERATION (FIRST DRAFT)
# -------------------------------------------------

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px
from pathlib import Path
import numpy as np
import plotly.graph_objects as go

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------

st.set_page_config(
    page_title="Target Financial Report",
    layout="wide"
)

# -------------------------------------------------
# DEFINE LANGUAGES (FOR FUTURE MULTILINGUAL SUPPORT)
# -------------------------------------------------

lang = st.radio(
    "Language / Språk",
    ["English", "Svenska"],
    horizontal=True
)

# -------------------------------------------------
# LOAD LATEST ANALYSIS RESULTS
# -------------------------------------------------

OUTPUTS_PATH = os.path.join(os.path.dirname(__file__), "..", "notebooks", "outputs")

json_files = [
    f for f in os.listdir(OUTPUTS_PATH)
    if f.startswith("analysis_results_") and f.endswith(".json")
]

if not json_files:
    st.error("No analysis results found.")
    st.stop()

json_files.sort(reverse=True)
latest_file = json_files[0]

with open(os.path.join(OUTPUTS_PATH, latest_file)) as f:
    results = json.load(f)

# Extract data
target = results.get("target", "Unknown Target")
timestamp = results.get("export_timestamp", "N/A")
peer_group_size = results.get("peer_group_size", "N/A")
first_year = results.get("first_year", "N/A")
last_year = results.get("last_year", "N/A")
years_of_analysis = results.get("years_of_analysis", "N/A")

financial_snapshot_table = pd.DataFrame(results["financial_snapshot_table"])
structural_diagnostics_table = pd.DataFrame(results["structural_diagnostics_table"])

rev_snapshot = results["rev_snapshot"]
pm_snapshot = results["pm_snapshot"]
at_snapshot = results["at_snapshot"]
roe_snapshot = results["roe_snapshot"]
eq_snapshot = results["eq_snapshot"]

# -------------------------------------------------
# EXECUTIVE HEADER
# -------------------------------------------------

st.title("Target Company Strategic & Performance Evaluation")
# Format timestamp to Month Year only
try:
    formatted_date = datetime.strptime(timestamp, "%Y-%m-%d_%H-%M").strftime("%B %Y")
except Exception:
    formatted_date = timestamp

st.markdown(f"""
**Target Company:** {target}    
**Peer Group Size:** {peer_group_size} companies  
**Analysis Period (Common Available Sample Window):** {first_year}–{last_year} ({years_of_analysis} years)  
**Report Generated:** {formatted_date}
""")

st.divider()

# -------------------------------------------------
# GEOGRAPHIC POSITIONING – TARGET VS INDUSTRY SAMPLE
# -------------------------------------------------

st.subheader("Geographic Positioning")

# Path to geocoded dataset
DATA_PATH = Path(__file__).resolve().parents[1] / "data/processed/dismantlers/sbr_dismantlers_geocoded.csv"

if not DATA_PATH.exists():
    st.info("Geocoded operator dataset not found.")
else:
    geo_df = pd.read_csv(DATA_PATH)

    # ---- Target ----
    target_company = target

    # ---- Explicit peer group used in financial benchmarking ----
    # IMPORTANT: These must exactly match the companies used in the validated analysis sample

    used_companies = [
        "Ekholms Bildemontering AB",
        "Arboga Bilskrot AB",
        "Autocirc Svensk Bilåtervinning AB",
        "Bilåtervinning i Tibro AB",
        "Bjuhrs Bil AB",
        "Köpings Bildemontering AB",
        "Mariestads Bildemontering och Återvinningsteknik AB",
        "Nya Högåsens Bildemontering AB",
        "Vinåkers Bilskrot AB",
        "Örebro Bildemontering AB"
    ]

    selected_companies = used_companies

    sample_df = geo_df[geo_df["company"].isin(selected_companies)].copy()

    # -------------------------------------------------
    # Helper: Generate Radius Circle (in km)
    # -------------------------------------------------
    def generate_circle(lat, lon, radius_km, points=100):
        earth_radius = 6371
        angles = np.linspace(0, 2 * np.pi, points)

        circle_lats = []
        circle_lons = []

        for angle in angles:
            dx = radius_km * np.cos(angle)
            dy = radius_km * np.sin(angle)

            new_lat = lat + (dy / earth_radius) * (180 / np.pi)
            new_lon = lon + (dx / earth_radius) * (180 / np.pi) / np.cos(lat * np.pi/180)

            circle_lats.append(new_lat)
            circle_lons.append(new_lon)

        return circle_lats, circle_lons

    if sample_df.empty:
        st.info("Target company not found in geocoded dataset.")
    else:
        sample_df["highlight"] = sample_df["company"].apply(
            lambda x: "Target Company" if x == target_company else "Industry Sample"
        )

        highlight_colors = {
            "Target Company": "#73879F",
            "Industry Sample": "#F28B82"
        }

        fig_sample = px.scatter_geo(
            sample_df,
            lat="lat",
            lon="lon",
            color="highlight",
            projection="mercator",
            color_discrete_map=highlight_colors,
            title="Geographic Distribution of Target Company and Selected Industry Peers"
        )

        # Hover: show ONLY company name
        fig_sample.update_traces(
            customdata=sample_df[["company"]],
            hovertemplate="<b>%{customdata[0]}</b><extra></extra>"
        )

        fig_sample.update_geos(
            visible=False,
            showcountries=True,
            countrycolor="rgba(0,0,0,0.2)",
            lataxis_range=[55, 69],   # Full Sweden vertical span
            lonaxis_range=[2, 30]    # Full Sweden horizontal span
        )

        fig_sample.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            legend_title_text="Company Type"
        )

        # ---- Add Fjugesta marker ----
        fjugesta_lat = 59.1800
        fjugesta_lon = 14.8720

        fig_sample.add_scattergeo(
            lat=[fjugesta_lat],
            lon=[fjugesta_lon],
            mode="markers+text",
            marker=dict(size=10, color="#0D4F1D", symbol="diamond"),
            text=["Fjugesta"],
            textposition="top center",
            name="Fjugesta",
            hovertemplate="<b>Fjugesta</b><extra></extra>"
        )

        # 50 km circle
        lat_50, lon_50 = generate_circle(fjugesta_lat, fjugesta_lon, 50)
        fig_sample.add_scattergeo(
            lat=lat_50,
            lon=lon_50,
            mode="lines",
            line=dict(color="rgba(55,65,81,0.4)", width=1),
            name="50 km Radius"
        )

        # 100 km circle
        lat_100, lon_100 = generate_circle(fjugesta_lat, fjugesta_lon, 100)
        fig_sample.add_scattergeo(
            lat=lat_100,
            lon=lon_100,
            mode="lines",
            line=dict(color="rgba(55,65,81,0.25)", width=1),
            name="100 km Radius"
        )

        st.plotly_chart(fig_sample, use_container_width=True)

st.divider()

# -------------------------------------------------
# KPI POSITIONING SUMMARY
# -------------------------------------------------

st.subheader("Key Performance Indicators Overview")

# -------------------------------------------------
# Helper: Quintile Color Mapping (Rainbow Scale)
# -------------------------------------------------
def quintile_color(q):
    if q == 5:
        return "#166534"  # Dark Green (Top 20%)
    elif q == 4:
        return "#22C55E"  # Green
    elif q == 3:
        return "#EAB308"  # Yellow
    elif q == 2:
        return "#F97316"  # Orange
    elif q == 1:
        return "#991B1B"  # Red (Bottom 20%)
    else:
        return "#6B7280"  # Grey (Undefined)


# KPI configuration: (Label, Snapshot Dict, Value Key)
kpi_data = [
    ("Revenue (Latest Year)", rev_snapshot, "target"),
    ("Profitability", pm_snapshot, "target"),
    ("Efficiency", at_snapshot, "target"),
    ("Capital Return", roe_snapshot, "target"),
    ("Capital Structure", eq_snapshot, "target"),
]

cols = st.columns(5)

for col, (label, snapshot, value_key) in zip(cols, kpi_data):

    value = snapshot.get(value_key, "N/A")
    classification = snapshot.get("classification", "N/A")
    quintile = snapshot.get("quintile", 0)

    color = quintile_color(quintile)

    # Value formatting logic
    if isinstance(value, (int, float)):
        if "Revenue" in label:
            value_display = f"{value:,.0f} SEK"
        elif "Margin" in label or "Return" in label or "Profitability" in label:
            value_display = f"{value:.1%}"
        elif "Structure" in label:
            value_display = f"{value:.2f}"
        else:
            value_display = f"{value:,.0f}"
    else:
        value_display = value

    col.markdown(f"""
        <div style="
            padding:18px;
            border-radius:14px;
            background-color:white;
            box-shadow:0 2px 6px rgba(0,0,0,0.05);
            border:1px solid #E5E7EB;
        ">
            <div style="font-size:0.8rem; color:#6B7280; margin-bottom:6px;">
                {label}
            </div>
            <div style="font-size:1.6rem; font-weight:700; margin-bottom:8px;">
                {value_display}
            </div>
            <div style="
                display:inline-block;
                padding:4px 10px;
                border-radius:20px;
                font-size:0.75rem;
                font-weight:600;
                background-color:{color}20;
                color:{color};
            ">
                {classification}
            </div>
        </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------
# INTERPRETATION BLOCK
# -------------------------------------------------

rev_class = rev_snapshot.get("classification")
pm_class = pm_snapshot.get("classification")
at_class = at_snapshot.get("classification")
roe_class = roe_snapshot.get("classification")

interpretation = ""

if rev_class == "Bottom 20%" and pm_class == "Bottom 20%":
    interpretation = (
        "The company operates at structurally sub-scale levels within a scale-driven market, "
        "which constrains its ability to generate revenue growth. "
        "While asset utilisation appears relatively efficient, the lack of scale limits absolute earnings capacity "
        "and reinforces weaker profitability relative to peers."
    )

elif at_class in ["60–80%", "Top 20%"] and pm_class == "Bottom 20%":
    interpretation = (
        "Despite relatively efficient asset utilisation, profitability remains structurally weak, "
        "suggesting margin pressure or cost inefficiencies rather than operational throughput constraints."
    )

elif roe_class == "Bottom 20%":
    interpretation = (
        "Returns on capital are structurally weak relative to peers, "
        "indicating suboptimal capital allocation or earnings generation capacity."
    )

else:
    interpretation = (
        "The company exhibits mixed structural positioning across key financial dimensions, "
        "with performance dependent on both scale and operational execution."
    )

st.markdown(f"""
<div style="
    margin-top:16px;
    padding:16px;
    border-radius:10px;
    background-color:white;
    font-size:0.80rem;
    line-height:1.5;
">
<strong>Interpretation:</strong><br>
{interpretation}

<br>

<div style="font-size:0.6rem; color:#6B7280;">
Classification is based on industry quintile ranking (1–5) within the peer group. 
Top 20% (Quintile 5) reflects structural outperformance relative to peers, 
while Bottom 20% (Quintile 1) reflects structural underperformance. 
Rankings are calculated using the latest available year within the common sample window.
</div>

</div>
""", unsafe_allow_html=True)

st.divider()

# -------------------------------------------------
# REVENUE SNAPSHOT
# -------------------------------------------------

st.subheader("Revenue — Scale Position")

rev_target = rev_snapshot.get("target")
rev_industry = rev_snapshot.get("industry_mean")

fig_rev = go.Figure()

fig_rev.add_trace(go.Bar(
    x=[target],
    y=[rev_target],
    marker_color="#F28B82",
    width=0.2
))

fig_rev.add_trace(go.Bar(
    x=["Industry Mean"],
    y=[rev_industry],
    marker_color="#6B7280",
    width=0.2
))

fig_rev.update_layout(
    plot_bgcolor="white",
    height=400,
    showlegend=False,
    yaxis_title="Revenue (SEK)"
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.plotly_chart(fig_rev, use_container_width=True)

# Interpretation
rev_comment = (
    "The company operates at a significantly smaller scale relative to the industry, "
    "which constrains its ability to capture market share and benefit from scale-driven dynamics."
)

st.markdown(f"<div style='font-size:0.9rem'>{rev_comment}</div>", unsafe_allow_html=True)

st.divider()

# -------------------------------------------------
# PROFITABILITY SNAPSHOT
# -------------------------------------------------

st.subheader("Profitability — Margin Position")

pm_target = pm_snapshot.get("target")
pm_industry = pm_snapshot.get("industry_mean")

fig_pm = go.Figure()

fig_pm.add_trace(go.Bar(
    x=[target],
    y=[pm_target],
    marker_color="#F28B82",
    width=0.2
))

fig_pm.add_trace(go.Bar(
    x=["Industry Mean"],
    y=[pm_industry],
    marker_color="#6B7280",
    width=0.2
))

fig_pm.update_layout(
    plot_bgcolor="white",
    height=400,
    showlegend=False,
    yaxis_title="Profit Margin"
)

fig_pm.update_yaxes(tickformat=".0%")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.plotly_chart(fig_pm, use_container_width=True)

pm_comment = (
    "Profitability is structurally below industry levels, indicating weaker cost control "
    "or limited pricing power within the current competitive structure."
)

st.markdown(f"<div style='font-size:0.9rem'>{pm_comment}</div>", unsafe_allow_html=True)

st.divider()

# -------------------------------------------------
# EFFICIENCY SNAPSHOT
# -------------------------------------------------

st.subheader("Efficiency — Asset Utilisation")

at_target = at_snapshot.get("target")
at_industry = at_snapshot.get("industry_mean")

fig_at = go.Figure()

fig_at.add_trace(go.Bar(
    x=[target],
    y=[at_target],
    marker_color="#F28B82",
    width=0.2
))

fig_at.add_trace(go.Bar(
    x=["Industry Mean"],
    y=[at_industry],
    marker_color="#6B7280",
    width=0.2
))

fig_at.update_layout(
    plot_bgcolor="white",
    height=400,
    showlegend=False,
    yaxis_title="Asset Turnover"
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.plotly_chart(fig_at, use_container_width=True)

at_comment = (
    "The company demonstrates relatively strong asset utilisation, "
    "suggesting operational efficiency despite its smaller scale."
)

st.markdown(f"<div style='font-size:0.9rem'>{at_comment}</div>", unsafe_allow_html=True)

st.divider()

# -------------------------------------------------
# CAPITAL RETURN SNAPSHOT
# -------------------------------------------------

st.subheader("Capital Return — Return on Equity")

roe_target = roe_snapshot.get("target")
roe_industry = roe_snapshot.get("industry_mean")

fig_roe = go.Figure()

fig_roe.add_trace(go.Bar(
    x=[target],
    y=[roe_target],
    marker_color="#F28B82",
    width=0.2
))

fig_roe.add_trace(go.Bar(
    x=["Industry Mean"],
    y=[roe_industry],
    marker_color="#6B7280",
    width=0.2
))

fig_roe.update_layout(
    plot_bgcolor="white",
    height=400,
    showlegend=False,
    yaxis_title="Return on Equity"
)

fig_roe.update_yaxes(tickformat=".0%")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.plotly_chart(fig_roe, use_container_width=True)

roe_comment = (
    "Returns on equity are significantly below industry benchmarks, "
    "reflecting weaker earnings generation relative to capital employed."
)

st.markdown(f"<div style='font-size:0.9rem'>{roe_comment}</div>", unsafe_allow_html=True)

st.divider()

# -------------------------------------------------
# EQUITY RATIO SNAPSHOT (BAR COMPARISON)
# -------------------------------------------------

st.subheader("Capital Structure — Equity Ratio")

eq_target = eq_snapshot.get("target")
eq_industry = eq_snapshot.get("industry_mean")

fig_eq = go.Figure()

fig_eq.add_trace(go.Bar(
    x=[target],
    y=[eq_target],
    marker_color="#F28B82",
    width=0.2,
    name="Target"
))

fig_eq.add_trace(go.Bar(
    x=["Industry Mean"],
    y=[eq_industry],
    marker_color="#6B7280",
    width=0.2,
    name="Industry"
))

fig_eq.update_layout(
    plot_bgcolor="white",
    height=400,
    showlegend=False,
    margin=dict(l=20, r=20, t=20, b=20),
    yaxis_title="Equity Ratio"
)

fig_eq.update_yaxes(
    tickformat=".0%",
    range=[0, max(eq_target, eq_industry) * 1.4]
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.plotly_chart(fig_eq, use_container_width=True)


# -------------------------------------------------
# EQUITY INTERPRETATION
# -------------------------------------------------

if eq_target < eq_industry:
    eq_comment = (
        "The company operates with a structurally weaker equity base relative to peers, "
        "indicating elevated financial leverage and reduced balance sheet resilience within the industry structure."
    )
else:
    eq_comment = (
        "The company maintains a relatively strong equity position compared to peers, "
        "supporting greater financial resilience and funding flexibility."
    )

st.markdown(f"""
<div style="
    margin-top:10px;
    font-size:0.9rem;
    color:#374151;
    line-height:1.5;
">
{eq_comment}
</div>
""", unsafe_allow_html=True)


st.divider()

# -------------------------------------------------
# STRUCTURAL DIAGNOSTICS (EXECUTIVE FORMAT)
# -------------------------------------------------

st.subheader("Structural Diagnostics (Time-Series Quality)")

def get_row(metric):
    return structural_diagnostics_table[
        structural_diagnostics_table["Metric"] == metric
    ].iloc[0]


def direction_arrow(value):
    if pd.isnull(value):
        return "—"
    elif value > 0:
        return "↑"
    elif value < 0:
        return "↓"
    else:
        return "→"


def render_structural_cards(metric_name, is_percent=False):
    row = get_row(metric_name)

    mean = row["Mean"]
    vol = row["Volatility"]
    direction = row["Direction"]

    arrow = direction_arrow(direction)

    # Formatting
    if is_percent:
        mean_disp = f"{mean:.1f}%"
        vol_disp = f"{vol:.1f}%"
        dir_disp = f"{direction:.1f}pp" if pd.notnull(direction) else "N/A"
    else:
        mean_disp = f"{mean:.2f}"
        vol_disp = f"{vol:.2f}"
        dir_disp = f"{direction:.2f}" if pd.notnull(direction) else "N/A"

    col1, col2, col3 = st.columns(3)

    for col, title, value in zip(
        [col1, col2, col3],
        ["Mean", "Volatility", "Direction"],
        [mean_disp, vol_disp, f"{arrow} {dir_disp}"]
    ):
        col.markdown(f"""
        <div style="
            padding:16px;
            border-radius:12px;
            background-color:white;
            border:1px solid #E5E7EB;
            text-align:center;
        ">
            <div style="font-size:0.75rem; color:#6B7280;">
                {title}
            </div>
            <div style="font-size:1.4rem; font-weight:700;">
                {value}
            </div>
        </div>
        """, unsafe_allow_html=True)

    return row


def render_structural_interpretation(metric, row):
    # Core logic aligned with your earlier findings (scale, profitability, efficiency)

    if metric == "Revenue":
        text = """
Omsättningen visar en strukturell nedgång över analysperioden, vilket förstärker bolagets underskaliga position i en skaledriven marknad. Den negativa tillväxtprofilen, tillsammans med hög volatilitet, indikerar instabil efterfrågeupptagning och begränsad förmåga att upprätthålla konsekvent expansion.
"""

    elif metric == "Profit Margin":
        text = """
Lönsamhetsdynamiken visar tydlig strukturell press, med fallande marginaler och hög volatilitet som indikerar instabil kvalitet i resultatet. Detta tyder på exponering mot kostnadsvariationer och begränsad prissättningsförmåga i konkurrensmiljön.
"""

    elif metric == "Asset Turnover":
        text = """
Tillgångsutnyttjandet förblir relativt effektivt, med stabil utveckling och måttligt positiv trend över tid. Detta indikerar att bolaget operativt kan generera omsättning från sin tillgångsbas.
Dock översätts denna effektivitet inte till lönsamhet.
"""

    elif metric == "ROE":
        text = """
Avkastningen på eget kapital uppvisar hög volatilitet och en strukturell nedgång, vilket indikerar inkonsekvent kapitaleffektivitet över tid. Detta speglar instabil intjäningsförmåga i relation till kapitalbasen.
"""

    elif metric == "Equity Ratio":
        text = """
Kapitalbasen visar en nedåtgående trend, vilket indikerar ökat beroende av skuldsättning över analysperioden. Detta kan tyda på balansräkningspress eller begränsad intern kapitalgenerering.
"""

    else:
        text = "No interpretation available."

    st.markdown(f"""
    <div style="
        margin-top:10px;
        font-size:0.9rem;
        line-height:1.6;
        color:#374151;
    ">
    {text}
    """, unsafe_allow_html=True)


# -------------------------------------------------
# APPLY TO ALL METRICS
# -------------------------------------------------

metrics_config = [
    ("Revenue", False),
    ("Profit Margin", True),
    ("Asset Turnover", False),
    ("ROE", True),
    ("Equity Ratio", True),
]

for metric, is_percent in metrics_config:
    st.markdown(f"### {metric} — Structural Profile")

    row = render_structural_cards(metric, is_percent)
    render_structural_interpretation(metric, row)

    st.divider()


# -------------------------------------------------
# Public Dashboard Disclaimer
# -------------------------------------------------
st.markdown("---")
st.markdown(
    "*Denna instrumentpanel presenterar analytiska insikter hämtade från offentligt tillgängliga finansiella data. "
    "Den är endast avsedd för informations- och utforskande ändamål och utgör inte finansiell rådgivning.*<br>"
    "*Omfattande analytiska rapporter på företagsnivå finns tillgängliga på begäran.*",
    unsafe_allow_html=True
)
