from pathlib import Path
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

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
    "3+": "#741111",
    "2": "#CD5C5C",
    "1": "#F1BBB6"
}

fig_map = px.scatter_geo(
    df,
    lat="lat",
    lon="lon",
    color="cluster_category",
    hover_name="company",
    projection="mercator",
    color_discrete_map=cluster_colors,
    title="Geographic Distribution of SBR-Registered Operators"
)

fig_map.update_geos(
    scope="europe",
    fitbounds="locations",
    visible=False
)

fig_map.update_layout(
    margin=dict(l=0, r=0, t=40, b=0),
    legend_title_text="Operator Cluster"
)

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
      .reindex(["3+", "2", "1"])
)

fig2, ax2 = plt.subplots(figsize=(4.8, 3))

bars = ax2.bar(
  ["Three\nand More\nOperators", "Two\nOperators", "One\nOperator"],
    city_cluster_summary.values,
    width=0.30,
    color=[cluster_colors[k] for k in ["3+", "2", "1"]],
    edgecolor="black",
    linewidth=0.8
)

# Title styling
ax2.set_title(
    "Cities by Operator Density",
    fontsize=12,
    fontweight="bold",
    pad=15
)

# Axis labels
ax2.set_xlabel("Operator Density", fontsize=10, labelpad=12)
ax2.set_ylabel("Number of Cities", fontsize=10, labelpad=12)

# Subtle horizontal grid
ax2.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.4)
ax2.set_axisbelow(True)

# Remove top/right spines
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

# Tick styling
ax2.tick_params(axis="both", labelsize=8)

# Value labels
for bar in bars:
    height = bar.get_height()
    ax2.text(
        bar.get_x() + bar.get_width() / 2,
        height + 0.5,
        f"{int(height)}",
        ha="center",
        va="bottom",
        fontsize=10
    )

plt.tight_layout()

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.pyplot(fig2)


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