import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.metrics.market_data import get_metal_prices, compute_metal_metrics

df = get_metal_prices(force_refresh=True)
metrics, df = compute_metal_metrics(df)

print(df.head())

print("\n=== LAST ROW ===")
print(df.tail(1))

print("\n=== METRICS ===")

print(metrics)
