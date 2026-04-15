# src/metrics/operating_efficiency.py

import numpy as np
import pandas as pd


# -------------------------------------------------
# Compute Operating Margin
# -------------------------------------------------

def compute_operating_margin(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["operating_margin"] = (
        df["operating_profit_after_depreciation"] / df["turnover"]
    )

    return df


# -------------------------------------------------
# Industry Structure (Mean + Dispersion + Drift)
# -------------------------------------------------

def compute_industry_operating_structure(df: pd.DataFrame):

    industry = (
        df.groupby("year")
        .agg(
            mean_operating_margin=("operating_margin", "mean"),
            dispersion=("operating_margin", "std"),
        )
        .reset_index()
        .sort_values("year")
    )

    # Structural drift = slope of mean margin vs time
    if len(industry) > 1:
        slope = np.polyfit(
            industry["year"],
            industry["mean_operating_margin"],
            1,
        )[0]
    else:
        slope = 0

    industry["structural_drift"] = slope

    return industry


# -------------------------------------------------
# Latest-Year Ranking
# -------------------------------------------------

def compute_latest_operating_margin_ranking(df: pd.DataFrame):

    latest_year = df["year"].max()

    latest = (
        df[df["year"] == latest_year]
        .sort_values("operating_margin", ascending=False)
        .reset_index(drop=True)
    )

    return latest, latest_year


# -------------------------------------------------
# Firm-Level Structural Metrics
# -------------------------------------------------

def compute_structural_operating_efficiency(df: pd.DataFrame):

    firm_stats = []

    for company, group in df.groupby("company"):

        group = group.sort_values("year")

        mean_margin = group["operating_margin"].mean()
        volatility = group["operating_margin"].std()
        mean_total_assets = group["total_assets"].mean()

        if len(group) > 1:
            slope = np.polyfit(
                group["year"],
                group["operating_margin"],
                1,
            )[0]
        else:
            slope = 0

        firm_stats.append(
            {
                "company": company,
                "mean_operating_margin": mean_margin,
                "margin_volatility": volatility,
                "structural_drift": slope,
                "mean_total_assets": mean_total_assets
            }
        )

    structural_df = pd.DataFrame(firm_stats)

    industry_mean_structural = structural_df["mean_operating_margin"].mean()

    return structural_df, industry_mean_structural

# -------------------------------------------------
# Capital Productivity (Turnover × Margin)
# -------------------------------------------------

def compute_capital_productivity(df: pd.DataFrame):

    df = df.copy()

    if "asset_turnover" not in df.columns:
        df["asset_turnover"] = df["turnover"] / df["total_assets"]

    if "operating_margin" not in df.columns:
        df["operating_margin"] = (
            df["operating_profit_after_depreciation"] / df["turnover"]
        )

    df["capital_productivity"] = (
        df["asset_turnover"] * df["operating_margin"]
    )

    latest_year = df["year"].max()

    latest = df[df["year"] == latest_year].copy()

    industry_mean = latest["capital_productivity"].mean()

    return latest, industry_mean, latest_year

# -------------------------------------------------
# ROA and EBITDA Margin
# -------------------------------------------------

def compute_return_metrics(df: pd.DataFrame):

    df = df.copy()

    df["roa"] = df["results_for_the_year"] / df["total_assets"]
    df["ebitda_margin"] = df["ebitda"] / df["turnover"]

    latest_year = df["year"].max()
    latest = df[df["year"] == latest_year].copy()

    industry_roa_mean = latest["roa"].mean()
    industry_ebitda_margin_mean = latest["ebitda_margin"].mean()

    return latest, industry_roa_mean, industry_ebitda_margin_mean, latest_year

# -------------------------------------------------
# Structural Return Metrics (Mean + Volatility + Drift)
# -------------------------------------------------

def compute_structural_return_metrics(df: pd.DataFrame):

    df = df.copy()

    # -------------------------------------------------
    # Compute yearly ratios
    # -------------------------------------------------

    df["roa"] = df["results_for_the_year"] / df["total_assets"]
    df["ebitda_margin"] = df["ebitda"] / df["turnover"]

    firm_stats = []

    for company, group in df.groupby("company"):

        group = group.sort_values("year")

        mean_roa = group["roa"].mean()
        roa_volatility = group["roa"].std()

        mean_ebitda_margin = group["ebitda_margin"].mean()
        ebitda_volatility = group["ebitda_margin"].std()

        # Structural drift (trend slope)
        if len(group) > 1:
            roa_drift = np.polyfit(group["year"], group["roa"], 1)[0]
            ebitda_drift = np.polyfit(group["year"], group["ebitda_margin"], 1)[0]
        else:
            roa_drift = 0
            ebitda_drift = 0

        # --- NEW: Structural scale metrics ---
        mean_total_assets = group["total_assets"].mean()
        mean_turnover = group["turnover"].mean()

        firm_stats.append(
            {
                "company": company,
                "mean_roa": mean_roa,
                "roa_volatility": roa_volatility,
                "roa_structural_drift": roa_drift,
                "mean_ebitda_margin": mean_ebitda_margin,
                "ebitda_volatility": ebitda_volatility,
                "ebitda_structural_drift": ebitda_drift,
                "mean_total_assets": mean_total_assets,
                "mean_turnover": mean_turnover,
            }
        )

    structural_returns = pd.DataFrame(firm_stats)

    # -------------------------------------------------
    # Industry Benchmarks
    # -------------------------------------------------

    industry_mean_roa = structural_returns["mean_roa"].mean()
    industry_mean_ebitda = structural_returns["mean_ebitda_margin"].mean()

    # -------------------------------------------------
    # Relative Scale Metrics (normalised)
    # -------------------------------------------------

    structural_returns["relative_asset_size"] = (
        structural_returns["mean_total_assets"]
        / structural_returns["mean_total_assets"].max()
    )

    structural_returns["relative_revenue_size"] = (
        structural_returns["mean_turnover"]
        / structural_returns["mean_turnover"].max()
    )

    return structural_returns, industry_mean_roa, industry_mean_ebitda