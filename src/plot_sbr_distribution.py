from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from config import PROCESSED_DATA_DIR
from pathlib import Path
import textwrap



# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------

DATA_DIR = Path(PROCESSED_DATA_DIR)

csv_files = sorted(DATA_DIR.glob("**/sbr_dismantlers_*.csv"))

if not csv_files:
    raise FileNotFoundError("No SBR CSV files found.")

latest_file = csv_files[-1]

FIGURES_DIR = Path("figures")
FIGURES_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------------
# Load Data
# ------------------------------------------------------------------

df = pd.read_csv(latest_file)

# ------------------------------------------------------------------
# Aggregate
# ------------------------------------------------------------------

county_counts = df["county"].value_counts().sort_index()


# ------------------------------------------------------------------
# Plot
# ------------------------------------------------------------------

county_counts.plot(kind="bar")

plt.xlabel("County")
plt.ylabel("Number of SBR Companies")
plt.title("SBR Dismantlers by County")

plt.xticks(rotation=90)
plt.tight_layout()

output_path = FIGURES_DIR / "sbr_dismantlers_by_county.png"

plt.savefig(output_path, dpi=300)
print(f"Figure saved to: {output_path}")

plt.show()


# -------------------------------------------------------------
# City-Level Distribution (Top 20)
# -------------------------------------------------------------

city_counts = df["city"].value_counts().head(20)

plt.figure()
city_counts.plot(kind="bar")

plt.xlabel("City")
plt.ylabel("Number of SBR Companies")
plt.title("Top 20 Cities by SBR Dismantlers")

plt.xticks(rotation=90)
plt.tight_layout()

city_output = FIGURES_DIR / "sbr_top20_cities.png"
plt.savefig(city_output, dpi=300)

print(f"City figure saved to: {city_output}")

plt.show()


# -------------------------------------------------------------
# City Clustering by Operator Count
# -------------------------------------------------------------

city_counts = df["city"].value_counts()

cluster_3_plus = city_counts[city_counts >= 3]
cluster_2 = city_counts[city_counts == 2]
cluster_1 = city_counts[city_counts == 1]


# -------------------------------------------------------------
# Plot City Cluster Structure
# -------------------------------------------------------------

cluster_summary = {
    "≥3 operators": len(cluster_3_plus),
    "2 operators": len(cluster_2),
    "1 operator": len(cluster_1),
}

cluster_series = pd.Series(cluster_summary)

plt.figure()
cluster_series.plot(kind="bar")

plt.xlabel("City Cluster Type")
plt.ylabel("Number of Cities")
plt.title("City Concentration Structure of SBR Dismantlers")

plt.tight_layout()

cluster_output = FIGURES_DIR / "sbr_city_cluster_structure.png"
plt.savefig(cluster_output, dpi=300)

print(f"Cluster structure figure saved to: {cluster_output}")

plt.show()

# -------------------------------------------------------------
# Plot City Lists by Cluster
# -------------------------------------------------------------

plt.figure(figsize=(14, 8))


# Prepare text blocks

def horizontal_format(city_list, width=45):
    text = ", ".join(sorted(city_list))
    return "\n".join(textwrap.wrap(text, width=width))

n_3 = len(cluster_3_plus)
n_2 = len(cluster_2)
n_1 = len(cluster_1)

total_cities = len(city_counts)
total_operators = len(df)

multi_operator_cities = city_counts[city_counts >= 2]
operators_in_multi_cities = df[df["city"].isin(multi_operator_cities.index)].shape[0]

pct_multi = operators_in_multi_cities / total_operators * 100

text_3 = horizontal_format(cluster_3_plus.index.tolist())
text_2 = horizontal_format(cluster_2.index.tolist())
text_1 = horizontal_format(cluster_1.index.tolist())

# Group by company and count unique cities
company_city_counts = (
    df.groupby("company")["city"]
      .nunique()
      .sort_values(ascending=False)
)

# Filter companies present in more than one city
multi_city_companies = company_city_counts[company_city_counts > 1]

multi_city_details = (
    df[df["company"].isin(multi_city_companies.index)]
      .groupby("company")["city"]
      .apply(lambda x: sorted(x.unique()))
      .sort_index()
)
# Format multi-city operator text
multi_city_lines = []

for company, cities in multi_city_details.items():
    line = f"{company} ({len(cities)} cities): " + ", ".join(cities)
    multi_city_lines.append(line)

multi_city_text = "\n".join(
    textwrap.wrap("\n".join(multi_city_lines), width=120)
)

# Left column
plt.text(
    0.05, 0.95,
    f"≥3 Operators ({n_3} cities)\n\n{text_3}",
    verticalalignment='top'
)

# Middle column
plt.text(
    0.35, 0.95,
    f"2 Operators ({n_2} cities)\n\n{text_2}",
    verticalalignment='top'
)

# Right column
plt.text(
    0.65, 0.95,
    f"1 Operator ({n_1} cities)\n\n{text_1}",
    verticalalignment='top'
)

plt.axis("off")
plt.title("City Distribution by Operator Cluster", pad=20)

plt.tight_layout()

summary_text = (
    f"Total Cities: {total_cities}\n"
    f"Total Operators: {total_operators}\n"
    f"Operators in Multi-Operator Cities: {operators_in_multi_cities} "
    f"({pct_multi:.1f}%)"
)

# --- Summary metrics (higher) ---
plt.text(
    0.05, 0.22,
    summary_text,
    ha="left",
    fontsize=11,
    fontweight="bold",
    verticalalignment="top"
)

# --- Multi-City Operators (below summary) ---
plt.text(
    0.05, 0.15,
    "Multi-City Operators:\n" + multi_city_text,
    verticalalignment='top',
    fontsize=10
)

list_output = FIGURES_DIR / "sbr_city_cluster_lists.png"
plt.savefig(list_output, dpi=300)

print(f"City cluster list figure saved to: {list_output}")

plt.show()