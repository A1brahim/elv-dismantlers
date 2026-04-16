from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------------------
# Page Setup
# --------------------------------------------------

st.set_page_config(page_title="Geographic Structure", layout="wide")

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
        return "3+"
    elif n == 2:
        return "2"
    else:
        return "1"


df["cluster_category"] = df["operator_count"].apply(classify_cluster)

# --------------------------------------------------
# Page Title
# --------------------------------------------------

st.title("Geographic Structure of Swedish Bilåtervinning")
st.caption(
    "Spatial distribution of SBR (Sveriges Bilåtervinnares Riksförbund)-affiliated dismantling businesses."
)

st.markdown(
    "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# National Operator Distribution (Plotly Map)
# --------------------------------------------------

st.subheader("National Operator Distribution")

cluster_colors = {
    "3+": "#741111",
    "2": "#CD5C5C",
    "1": "#F1BBB6",
}

fig_map = px.scatter_geo(
    df,
    lat="lat",
    lon="lon",
    color="cluster_category",
    color_discrete_map=cluster_colors,
    hover_name="company",
    hover_data={
        "city": True,
        "operator_count": True,
        "lat": False,
        "lon": False,
    },
)

fig_map.update_geos(
    scope="europe",
    showcountries=True,
    countrycolor="#9CA3AF",
    showcoastlines=True,
    coastlinecolor="#6B7280",
    showland=True,
    landcolor="whitesmoke",
    lataxis_range=[53, 72],
    lonaxis_range=[5, 30],
)

fig_map.update_layout(
    height=700,
    legend_title_text="Operator Cluster",
    margin=dict(l=0, r=0, t=30, b=0),
)

st.plotly_chart(fig_map, use_container_width=True)

st.markdown(
    "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Cluster Distribution Bar Chart (Plotly)
# --------------------------------------------------

st.subheader("City Operator Density Distribution")

city_cluster_summary = (
    df.groupby(["city", "cluster_category"]).size()
    .reset_index()
    .groupby("cluster_category")["city"]
    .nunique()
    .reindex(["3+", "2", "1"])
)

label_map = {
    "3+": "Three and More Operators",
    "2": "Two Operators",
    "1": "One Operator",
}

bar_df = pd.DataFrame(
    {
        "Category": [label_map[k] for k in ["3+", "2", "1"]],
        "Cities": city_cluster_summary.values,
        "Cluster": ["3+", "2", "1"],
    }
)

fig_bar = px.bar(
    bar_df,
    x="Category",
    y="Cities",
    color="Cluster",
    color_discrete_map=cluster_colors,
    text="Cities",
)

fig_bar.update_layout(
    plot_bgcolor="white",
    showlegend=False,
    height=400,
    margin=dict(l=20, r=20, t=30, b=20),
    xaxis_title="Operator Density",
    yaxis_title="Number of Cities",
)

fig_bar.update_traces(textposition="outside")

st.plotly_chart(fig_bar, use_container_width=True)

st.markdown(
    "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Structural Summary
# --------------------------------------------------

st.markdown("### Structural Overview")

summary_total_cities = df["city"].nunique()
summary_total_firms = df["company"].nunique()
summary_multi_operator = city_counts[
    city_counts["operator_count"] >= 2
]["city"].nunique()

st.markdown(
    f"""
- **Total operators:** {summary_total_firms}
- **Total cities represented:** {summary_total_cities}
- **Cities with two or more operators:** {summary_multi_operator}
"""
)

st.markdown(
    "<hr style='border:none; border-top:2px solid #9CA3AF; width:100%; margin:2.5rem 0;'>",
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Public Dashboard Disclaimer
# -------------------------------------------------
st.markdown("---")
st.markdown(
    "**This dashboard presents analytical insights derived from publicly available financial data. "
    "It is intended for informational and exploratory purposes only and does not constitute financial advice.**<br>"
    "**Comprehensive firm-level analytical reports are available upon request.**",
    unsafe_allow_html=True,
)