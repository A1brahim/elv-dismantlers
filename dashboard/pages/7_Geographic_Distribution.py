import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add project root to Python path (consistent with other dashboard pages)
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

# --------------------------------------------------
# Page Setup
# --------------------------------------------------

st.set_page_config(page_title="Geographic Distribution", layout="wide")

DATA_PATH = Path("data/processed/dismantlers/sbr_dismantlers_geocoded.csv")

# --------------------------------------------------
# Load Data
# --------------------------------------------------

@st.cache_data
def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError("Geocoded SBR dataset not found.")
    return pd.read_csv(DATA_PATH)


df = load_data()

if df.empty:
    st.warning("No data available.")
    st.stop()

# --------------------------------------------------
# Compute City Cluster Intensity
# --------------------------------------------------

city_counts = df.groupby("city")["company"].count().reset_index()
city_counts.columns = ["city", "operator_count"]

df = df.merge(city_counts, on="city")


def classify_cluster(n):
    if n >= 3:
        return "3 and More Operators"
    elif n == 2:
        return "2 Operators"
    else:
        return "1 Operator"


df["cluster_category"] = df["operator_count"].apply(classify_cluster)

# --------------------------------------------------
# Page Title
# --------------------------------------------------

st.title("Geographic Distribution of Swedish Bilåtervinning")
st.caption("Spatial distribution of SBR (Sveriges Bilåtervinnares Riksförbund)-affiliated dismantling businesses.")


st.markdown(
    "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
    unsafe_allow_html=True
)

# --------------------------------------------------
# Sweden Map with Plotly (Cloud-Compatible)
# --------------------------------------------------

st.subheader("National Operator Distribution")

cluster_colors = {
    "3 and More Operators": "#741111",
    "2 Operators": "#CD5C5C",
    "1 Operator": "#F1BBB6"
}


fig_map = px.scatter_geo(
    df,
    lat="lat",
    lon="lon",
    color="cluster_category",
    hover_name="company",
    hover_data={"lat": False, "lon": False, "cluster_category": False},
    projection="mercator",
    color_discrete_map=cluster_colors,
    title="Geographic Distribution of SBR-Registered Operators"
)

fig_map.update_geos(
    fitbounds="locations",
    visible=False,
    showcountries=True,
    countrycolor="rgba(0,0,0,0.2)",
    showsubunits=True,
    subunitcolor="rgba(0,0,0,0.15)",
    center=dict(lat=62, lon=15),
    projection_scale=5
)

fig_map.update_layout(
    margin=dict(l=0, r=0, t=40, b=0),
    legend_title_text="Operator Cluster"
)

# --------------------------------------------------
# Major City Markers
# --------------------------------------------------

major_cities = pd.DataFrame({
    "city": ["Stockholm", "Örebro", "Gothenburg", "Malmö"],
    "lat": [59.3293, 59.2753, 57.7089, 55.6050],
    "lon": [18.0686, 15.2134, 11.9746, 13.0038]
})

fig_map.add_trace(go.Scattergeo(
    lat=major_cities["lat"],
    lon=major_cities["lon"],
    text=major_cities["city"],
    mode="markers+text",
    marker=dict(
        size=6,
        color="#5A6F89"
    ),
    textposition="top center",
    name="Major Cities",
    hovertemplate="<b>%{text}</b><extra></extra>"
))

st.plotly_chart(fig_map, use_container_width=True)

st.markdown(
    "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
    unsafe_allow_html=True
)


# --------------------------------------------------
# Cluster Distribution Bar Chart
# --------------------------------------------------

st.subheader("City Operator Density Distribution")

city_cluster_summary = (
    df.groupby(["city", "cluster_category"]).size()
      .reset_index()
      .groupby("cluster_category")["city"]
      .nunique()
      .reindex(["3 and More Operators", "2 Operators", "1 Operator"])
)

fig_density = go.Figure()

fig_density.add_trace(go.Bar(
    x=[
        "Three<br>and More<br>Operators",
        "Two<br>Operators",
        "One<br>Operator"
    ],
    y=city_cluster_summary.values,
    width=0.3,
    marker_color=[cluster_colors[k] for k in ["3 and More Operators", "2 Operators", "1 Operator"]],
    text=city_cluster_summary.values,
    textposition="outside"
))

fig_density.update_layout(
    title="Cities by Operator Density",
    xaxis_title="Operator Density",
    yaxis_title="Number of Cities",
    plot_bgcolor="white",
    bargap=0.2,
    bargroupgap=0.2,
    height=400,
    margin=dict(l=20, r=20, t=60, b=40),
    showlegend=False
)

fig_density.update_yaxes(
    range=[0, 100],     # always start at 0
    dtick=10,               # tick interval
    showgrid=True,
    gridcolor="rgba(0,0,0,0.08)",
    zeroline=False,
    tickfont=dict(size=11)
)

fig_density.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.1)")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.plotly_chart(fig_density, use_container_width=True)


st.markdown(
    "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
    unsafe_allow_html=True
)

# --------------------------------------------------
# Structural Summary
# --------------------------------------------------

st.markdown("### Structural Overview")

summary_total_cities = df["city"].nunique()
summary_total_firms = df["company"].nunique()
summary_multi_operator = city_counts[city_counts["operator_count"] >= 2]["city"].nunique()

st.markdown(f"""
- **Total operators:** {summary_total_firms}
- **Total cities represented:** {summary_total_cities}
- **Cities with two or more operators:** {summary_multi_operator}
""")


st.markdown(
    "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
    unsafe_allow_html=True
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