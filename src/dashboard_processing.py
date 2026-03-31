import pandas as pd
import numpy as np

# --------------------------------------------------
# 1️⃣ LOAD RAW DATA
# --------------------------------------------------

df_long = pd.read_csv("data/raw/ELV_Master_Long/ELV_Master_Long.csv")

# Keep only 2021–2024
df_long = df_long[df_long["Year"].between(2021, 2024)]

# --------------------------------------------------
# 2️⃣ PIVOT TO WIDE FORMAT
# --------------------------------------------------

df = (
    df_long
    .pivot_table(
        index=["Company", "Year"],
        columns="Metric",
        values="Value",
        aggfunc="first"
    )
    .reset_index()
)

# --------------------------------------------------
# 3️⃣ COMPUTE RATIOS (Yearly)
# --------------------------------------------------

def safe_div(n, d):
    return np.where(d != 0, n / d, np.nan)

df["Operating Margin"] = safe_div(
    df["Operating profit after depreciation"],
    df["Net sales"]
)

df["Net Margin"] = safe_div(
    df["Result after net financial items"],
    df["Net sales"]
)

df["Equity Ratio"] = safe_div(
    df["Equity"],
    df["Total equity and liabilities"]
)

df["Debt Ratio"] = safe_div(
    df["Total equity and liabilities"] - df["Equity"],
    df["Total equity and liabilities"]
)

df["Liquidity Ratio"] = safe_div(
    df["Current assets"],
    df["Current liabilities"]
)

df["Operating Expense Ratio"] = safe_div(
    df["Operating expenses"],
    df["Net sales"]
)

df["Financial Cost Ratio"] = safe_div(
    df["Financial costs"],
    df["Net sales"]
)

# --------------------------------------------------
# 4️⃣ COMPUTE YoY REVENUE GROWTH
# --------------------------------------------------

# Ensure correct time-series ordering
df = df.sort_values(["Company", "Year"])

# Compute Year-over-Year growth in Net Sales
df["YoY Revenue Growth"] = df.groupby("Company")["Net sales"].pct_change()

# --------------------------------------------------
# 5️⃣ MARKET SHARE
# --------------------------------------------------

industry_sales = df.groupby("Year")["Net sales"].transform("sum")
df["Market Share"] = safe_div(df["Net sales"], industry_sales)

# --------------------------------------------------
# 6️⃣ CAGR (2021–2024)
# --------------------------------------------------

sales_pivot = (
    df.pivot(index="Company", columns="Year", values="Net sales")
)

sales_pivot["CAGR_21_24"] = np.where(
    sales_pivot[2021] > 0,
    (sales_pivot[2024] / sales_pivot[2021]) ** (1/3) - 1,
    np.nan
)

cagr = sales_pivot["CAGR_21_24"].reset_index()

# --------------------------------------------------
# 7️⃣ STRUCTURAL METRICS (AVG + VOLATILITY)
# --------------------------------------------------

structural = (
    df.groupby("Company")
    .agg({
        "Operating Margin": ["mean", "std"],
        "Net Margin": ["mean", "std"],
        "Equity Ratio": ["mean", "std"],
        "Debt Ratio": ["mean", "std"],
        "Liquidity Ratio": ["mean", "std"],
        "Operating Expense Ratio": ["mean", "std"],
        "Financial Cost Ratio": ["mean", "std"],
        "Market Share": ["mean", "std"]
    })
)

structural.columns = [
    "Avg Operating Margin", "Operating Margin Vol",
    "Avg Net Margin", "Net Margin Vol",
    "Avg Equity Ratio", "Equity Ratio Vol",
    "Avg Debt Ratio", "Debt Ratio Vol",
    "Avg Liquidity Ratio", "Liquidity Ratio Vol",
    "Avg OpEx Ratio", "OpEx Vol",
    "Avg Financial Cost Ratio", "Financial Cost Vol",
    "Avg Market Share", "Market Share Vol"
]

structural = structural.reset_index()

# --------------------------------------------------
# 8️⃣ MERGE CAGR
# --------------------------------------------------

final = structural.merge(cagr, on="Company", how="left")

# --------------------------------------------------
# 9️⃣ SAVE OUTPUT
# --------------------------------------------------

df.to_csv("data/processed/elv_time_series.csv", index=False)
final.to_csv("data/processed/elv_metrics.csv", index=False)

print("Processing complete. Files saved to data/processed/elv_metrics.csv")