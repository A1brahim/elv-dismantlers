
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.metrics.market_data import get_diesel_se, compute_diesel_metrics

df = get_diesel_se(force_refresh=True)
metrics, df = compute_diesel_metrics(df)

print(df.head())
print(metrics)