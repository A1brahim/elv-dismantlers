from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
from geopy.distance import geodesic
from config import PROCESSED_DATA_DIR

# ---------------------------------------------------
# Load Geocoded Radius Dataset
# ---------------------------------------------------

DATA_FILE = Path("figures/operators_within_100km.csv")

if not DATA_FILE.exists():
    raise FileNotFoundError("operators_within_100km.csv not found.")

df = pd.read_csv(DATA_FILE)

# ---------------------------------------------------
# Geodesic Circle Function
# ---------------------------------------------------

def draw_geodesic_circle(ax, center_lat, center_lon, radius_km, **kwargs):
    angles = np.linspace(0, 360, 360)
    lats = []
    lons = []

    for angle in angles:
        destination = geodesic(kilometers=radius_km).destination(
            (center_lat, center_lon), angle
        )
        lats.append(destination.latitude)
        lons.append(destination.longitude)

    ax.plot(lons, lats, **kwargs)

# ---------------------------------------------------
# Fjugesta Town Centre Coordinates
# ---------------------------------------------------

FJUGESTA_COORDS = (59.1586, 14.8736)

# ---------------------------------------------------
# Ensure we have lat/lon
# ---------------------------------------------------

if "lat" not in df.columns or "lon" not in df.columns:
    raise ValueError("Latitude/Longitude columns not found.")

# ---------------------------------------------------
# Calculate Distance
# ---------------------------------------------------

df["distance_km"] = df.apply(
    lambda row: geodesic(
        FJUGESTA_COORDS, (row["lat"], row["lon"])
    ).km,
    axis=1
)

within_100 = df[df["distance_km"] <= 100]
within_50 = df[df["distance_km"] <= 50]

# ---------------------------------------------------
# Identify Multi-City Operators
# ---------------------------------------------------

multi_city = (
    df.groupby("company")["city"]
      .nunique()
)

multi_city_companies = multi_city[multi_city > 1].index
multi_city_df = within_100[within_100["company"].isin(multi_city_companies)]

# ---------------------------------------------------
# Define Distance Buckets
# ---------------------------------------------------

within_25 = df[df["distance_km"] <= 25].sort_values("distance_km")

# ---------------------------------------------------
# Create Combined Figure (Map + Table)
# ---------------------------------------------------

fig = plt.figure(figsize=(10, 14))
gs = fig.add_gridspec(2, 1, height_ratios=[2.5, 2])

# ------------------------
# Top: Map
# ------------------------

ax_map = fig.add_subplot(gs[0])

ax_map.scatter(
    within_100["lon"],
    within_100["lat"],
    alpha=0.5,
    label="Operators ≤100 km"
)

ax_map.scatter(
    within_50["lon"],
    within_50["lat"],
    color="orange",
    label="Operators ≤50 km"
)

ax_map.scatter(
    multi_city_df["lon"],
    multi_city_df["lat"],
    s=150,
    marker="*",
    color="green",
    label="Multi-City Operators"
)

ax_map.scatter(
    FJUGESTA_COORDS[1],
    FJUGESTA_COORDS[0],
    marker="X",
    s=250,
    color="red",
    label="Fjugesta"
)

# Draw circles
draw_geodesic_circle(ax_map, *FJUGESTA_COORDS, 25, color="grey", linestyle="--")
draw_geodesic_circle(ax_map, *FJUGESTA_COORDS, 50, color="black")
draw_geodesic_circle(ax_map, *FJUGESTA_COORDS, 75, color="grey", linestyle="--")
draw_geodesic_circle(ax_map, *FJUGESTA_COORDS, 100, color="black")

ax_map.set_xlabel("Longitude")
ax_map.set_ylabel("Latitude")
ax_map.set_title("SBR Operators Around Fjugesta (25/50/75/100 km)")

legend_elements = [
    Line2D([0], [0], marker='o', color='w',
           markerfacecolor='blue', label='Operators ≤100 km'),
    Line2D([0], [0], marker='o', color='w',
           markerfacecolor='orange', label='Operators ≤50 km'),
    Line2D([0], [0], marker='*', color='w',
           markerfacecolor='green', markersize=15,
           label='Multi-City Operators'),
    Line2D([0], [0], marker='X', color='w',
           markerfacecolor='red', markersize=15,
           label='Fjugesta'),
    Line2D([0], [0], color='black', label='50 / 100 km'),
    Line2D([0], [0], color='grey', linestyle='--',
           label='25 / 75 km')
]

ax_map.legend(handles=legend_elements, loc="upper right")

# ------------------------
# Bottom: Strategic Target Table
# ------------------------

ax_table = fig.add_subplot(gs[1])
ax_table.axis("off")

# Define buckets
within_25 = df[df["distance_km"] <= 25].sort_values("distance_km")
within_50_only = df[
    (df["distance_km"] > 25) & (df["distance_km"] <= 50)
].sort_values("distance_km")

# Build rows
rows = []

# ≤25 km
for _, row in within_25.iterrows():
    rows.append([
        "≤25 km",
        row["company"],
        row["city"],
        round(row["distance_km"], 1)
    ])

# 25–50 km
for _, row in within_50_only.iterrows():
    rows.append([
        "25–50 km",
        row["company"],
        row["city"],
        round(row["distance_km"], 1)
    ])

# Multi-city operators inside 100 km
multi_city = df.groupby("company")["city"].nunique()
multi_city_companies = multi_city[multi_city > 1].index

multi_city_in_radius = df[
    (df["company"].isin(multi_city_companies)) &
    (df["distance_km"] <= 100)
]

for _, row in multi_city_in_radius.iterrows():
    rows.append([
        "Multi-City",
        row["company"],
        row["city"],
        round(row["distance_km"], 1)
    ])

if not rows:
    rows = [["None", "", "", ""]]

table_df = pd.DataFrame(
    rows,
    columns=["Category", "Company", "City", "Distance (km)"]
)

table = ax_table.table(
    cellText=table_df.values,
    colLabels=table_df.columns,
    loc="center"
)

# Adjust column widths (relative proportions)
col_widths = [0.15, 0.45, 0.20, 0.20]  
# Category, Company, City, Distance


for i, width in enumerate(col_widths):
    for row in range(len(table_df) + 1):  # +1 for header row
        table[(row, i)].set_width(width)

for (row, col), cell in table.get_celld().items():
    if row == 0:
        cell.set_text_props(weight='bold')       

table.auto_set_font_size(False)
table.set_fontsize(8)
table.scale(1, 1.8)

ax_table.set_title("Strategic Target Operators", pad=15)

plt.tight_layout()
plt.savefig("figures/fjugesta_operator_map_with_table.png", dpi=300)
plt.show()
