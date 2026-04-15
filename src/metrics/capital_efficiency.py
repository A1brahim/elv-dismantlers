

import numpy as np
import pandas as pd


# -------------------------------------------------
# Capital Efficiency Metrics
# -------------------------------------------------

def compute_asset_turnover(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Asset Turnover = Net Sales / Total Assets
    Includes quality check to prevent division by zero.
    """

    required_cols = ["company", "year", "net_sales", "total_assets"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for capital efficiency: {missing}")

    df = df.copy()

    # Quality check: avoid division by zero
    df["asset_turnover"] = np.where(
        df["total_assets"] > 0,
        df["net_sales"] / df["total_assets"],
        np.nan
    )

    return df


# -------------------------------------------------
# Industry-Level Structural Diagnostics
# -------------------------------------------------

def compute_industry_capital_structure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes industry-level structural metrics:
    - Mean asset turnover (cross-sectional)
    - Dispersion (standard deviation)
    - Coefficient of variation
    - Year-over-year structural drift
    """

    if "asset_turnover" not in df.columns:
        raise ValueError("asset_turnover column not found. Run compute_asset_turnover() first.")

    grouped = (
        df.groupby("year")["asset_turnover"]
        .agg(["mean", "std"])
        .reset_index()
        .rename(columns={"mean": "mean_asset_turnover", "std": "dispersion"})
    )

    # Coefficient of variation
    grouped["cv"] = np.where(
        grouped["mean_asset_turnover"] != 0,
        grouped["dispersion"] / grouped["mean_asset_turnover"],
        np.nan
    )

    # Structural drift (YoY change in mean asset turnover)
    grouped["structural_drift"] = grouped["mean_asset_turnover"].diff()

    return grouped


# -------------------------------------------------
# Latest Year Ranking
# -------------------------------------------------

def compute_latest_year_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns latest-year cross-sectional ranking by asset turnover.
    """

    if "asset_turnover" not in df.columns:
        raise ValueError("asset_turnover column not found. Run compute_asset_turnover() first.")

    latest_year = df["year"].max()

    latest_df = (
        df[df["year"] == latest_year]
        .sort_values("asset_turnover", ascending=False)
        [["company", "asset_turnover"]]
        .reset_index(drop=True)
    )

    latest_df["rank"] = latest_df["asset_turnover"].rank(ascending=False, method="min")

    return latest_df, latest_year


# -------------------------------------------------
# Scale vs Efficiency Dataset
# -------------------------------------------------

def compute_scale_efficiency_map(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares dataset for Scale vs Efficiency scatter:
    - X-axis: Total Assets
    - Y-axis: Asset Turnover
    """

    if "asset_turnover" not in df.columns:
        raise ValueError("asset_turnover column not found. Run compute_asset_turnover() first.")


    return df[["company", "year", "total_assets", "asset_turnover"]].copy()


# -------------------------------------------------
# Firm-Level Structural Capital Efficiency
# -------------------------------------------------

def compute_structural_capital_efficiency(df: pd.DataFrame):
    """
    Computes firm-level structural capital efficiency metrics (2021–latest):

    Returns:
    - structural_df:
        company
        mean_asset_turnover
        turnover_volatility
        structural_drift (linear slope)
        structural_regime
    - industry_mean_turnover (mean of firm means)
    """

    if "asset_turnover" not in df.columns:
        raise ValueError("asset_turnover column not found. Run compute_asset_turnover() first.")

    df = df.sort_values(["company", "year"]).copy()

    structural_rows = []

    for company, group in df.groupby("company"):

        group = group.dropna(subset=["asset_turnover"])

        if len(group) < 2:
            continue

        # Structural level
        mean_turnover = group["asset_turnover"].mean()

        # Volatility
        std_turnover = group["asset_turnover"].std()

        # Linear structural drift (raw slope)
        slope = np.polyfit(group["year"], group["asset_turnover"], 1)[0]

        structural_rows.append(
            {
                "company": company,
                "mean_asset_turnover": mean_turnover,
                "turnover_volatility": std_turnover,
                "structural_drift": slope,
            }
        )

    structural_df = pd.DataFrame(structural_rows)

    # Industry benchmark = mean of firm means
    industry_mean_turnover = structural_df["mean_asset_turnover"].mean()

    # Classification logic
    def classify(row):
        if row["mean_asset_turnover"] >= industry_mean_turnover and row["structural_drift"] > 0:
            return "Structural Leader"
        elif row["mean_asset_turnover"] >= industry_mean_turnover and row["structural_drift"] <= 0:
            return "Efficient but Deteriorating"
        elif row["mean_asset_turnover"] < industry_mean_turnover and row["structural_drift"] > 0:
            return "Emerging Improver"
        else:
            return "Structural Weakness"

    structural_df["structural_regime"] = structural_df.apply(classify, axis=1)

    return structural_df, industry_mean_turnover

# ==========================================================
# Structural Capital Efficiency (Mean Level + Linear Drift)
# ==========================================================

import numpy as np

def compute_structural_capital_efficiency(df):
    if "asset_turnover" not in df.columns:
        raise ValueError("asset_turnover column not found. Run compute_asset_turnover() first.")

    df = df.sort_values(["company", "year"]).copy()

    rows = []

    for company, group in df.groupby("company"):
        group = group.dropna(subset=["asset_turnover"])

        if len(group) < 2:
            continue

        mean_turnover = group["asset_turnover"].mean()
        std_turnover = group["asset_turnover"].std()
        slope = np.polyfit(group["year"], group["asset_turnover"], 1)[0]

        rows.append(
            {
                "company": company,
                "mean_asset_turnover": mean_turnover,
                "turnover_volatility": std_turnover,
                "structural_drift": slope,
            }
        )

    structural_df = pd.DataFrame(rows)

    industry_mean_turnover = structural_df["mean_asset_turnover"].mean()

    def classify(row):
        if row["mean_asset_turnover"] >= industry_mean_turnover and row["structural_drift"] > 0:
            return "Structural Leader"
        elif row["mean_asset_turnover"] >= industry_mean_turnover and row["structural_drift"] <= 0:
            return "Efficient but Deteriorating"
        elif row["mean_asset_turnover"] < industry_mean_turnover and row["structural_drift"] > 0:
            return "Emerging Improver"
        else:
            return "Structural Weakness"

    structural_df["structural_regime"] = structural_df.apply(classify, axis=1)

    return structural_df, industry_mean_turnover