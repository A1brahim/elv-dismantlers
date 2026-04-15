# %%
import pandas as pd
import numpy as np
from pathlib import Path
import sys

#%%
# --------------------------------------------------
# PATH CONFIG
# --------------------------------------------------

#%%
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "raw" / "ELV_Master_Long" / "ELV_Master_Long.csv"
DASHBOARD_PATH = PROJECT_ROOT / "dashboard"

DASHBOARD_PATH.mkdir(exist_ok=True)
print("Dashboard path:", DASHBOARD_PATH.resolve())

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

#%%

from metrics.base import load_elv_master_long
from metrics.balance_sheet import build_balance_sheet_metrics

df = load_elv_master_long(DATA_PATH)

overlap_years, yearly, summary = build_balance_sheet_metrics(df)

print("Overlapping years detected:", overlap_years)

yearly.to_csv(DASHBOARD_PATH / "balance_sheet_yearly.csv", index=False)
summary.to_csv(DASHBOARD_PATH / "balance_sheet_summary.csv")

print("Balance sheet metrics exported successfully.")
# %%
