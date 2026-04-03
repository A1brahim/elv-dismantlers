# metrics/base.py

import pandas as pd
from pathlib import Path


def load_elv_master_long(path: str) -> pd.DataFrame:
    """
    Load ELV_Master_Long.csv and pivot it into wide format.
    """
    df = pd.read_csv(path)

    # Pivot from long to wide format
    df_wide = (
        df.pivot_table(
            index=["Company", "Year"],
            columns="Metric",
            values="Value",
            aggfunc="first"
        )
        .reset_index()
    )

    # Standardize column names
    df_wide.columns.name = None
    df_wide.columns = df_wide.columns.str.lower().str.replace(" ", "_")

    return df_wide