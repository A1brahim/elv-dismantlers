import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.metrics.market_data import get_metal_prices, compute_metal_metrics


def print_column_check(df, column_name):
    print(f"\n=== CHECK: {column_name} ===")

    if column_name not in df.columns:
        print(f"❌ Missing column: {column_name}")
        return

    series = pd.to_numeric(df[column_name], errors="coerce")
    valid_count = series.notna().sum()
    latest_value = series.dropna().iloc[-1] if valid_count > 0 else None

    print(f"✅ Column exists: {column_name}")
    print(f"Valid observations: {valid_count}")
    print(f"Latest value: {latest_value:,.2f}" if latest_value is not None else "Latest value: None")


# --------------------------------------------------
# Fetch and compute metals data
# --------------------------------------------------

raw_df = get_metal_prices(force_refresh=True)
metrics, df = compute_metal_metrics(raw_df)

print("\n=== RAW COLUMNS ===")
print(raw_df.columns.tolist())

print("\n=== COMPUTED COLUMNS ===")
print(df.columns.tolist())

print("\n=== HEAD ===")
print(df.head())

print("\n=== LAST ROW ===")
print(df.tail(1))

print("\n=== METRICS ===")
print(metrics)

# --------------------------------------------------
# Column checks
# --------------------------------------------------

print_column_check(df, "copper_sek")
print_column_check(df, "aluminium_sek")
print_column_check(df, "ferrous_proxy_sek")

# --------------------------------------------------
# Steel / ferrous proxy sanity check
# --------------------------------------------------

print("\n=== STEEL / FERROUS PROXY TEST ===")

if "ferrous_proxy_sek" not in df.columns:
    print("❌ FAIL: ferrous_proxy_sek column is missing from computed metals dataframe.")
elif df["ferrous_proxy_sek"].dropna().empty:
    print("❌ FAIL: ferrous_proxy_sek column exists but contains no usable values.")
else:
    steel_series = pd.to_numeric(df["ferrous_proxy_sek"], errors="coerce").dropna()
    print("✅ PASS: ferrous_proxy_sek column exists and contains usable values.")
    print(f"Latest ferrous proxy value: {steel_series.iloc[-1]:,.2f} SEK/tonne")
    print(f"7d average: {steel_series.tail(7).mean():,.2f} SEK/tonne")
    print(f"30d average: {steel_series.tail(30).mean():,.2f} SEK/tonne")
    print(f"30d volatility: {steel_series.tail(30).std():,.2f}")
