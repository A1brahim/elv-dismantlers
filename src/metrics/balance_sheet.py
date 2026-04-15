# src/metrics/balance_sheet.py

import pandas as pd
import numpy as np


# --------------------------------------------------
# OVERLAP DETECTION
# --------------------------------------------------

def get_overlapping_years(df: pd.DataFrame) -> list:
    """
    Returns sorted list of years present for ALL companies.
    """

    years_per_company = (
        df.groupby("company")["year"]
          .apply(lambda x: set(x.unique()))
    )

    overlapping_years = sorted(set.intersection(*years_per_company))

    if len(overlapping_years) < 3:
        raise ValueError(
            "Insufficient overlapping years across companies."
        )

    return [int(y) for y in overlapping_years]


# --------------------------------------------------
# YEARLY BALANCE SHEET METRICS
# --------------------------------------------------

def compute_yearly_balance_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes research-grade balance sheet metrics per company-year.
    Assumes wide format dataset.
    """

    df = df.copy()

    # --- Capital Structure ---
    df["total_liabilities"] = df["total_assets"] - df["equity"]

    df["equity_ratio"] = df["equity"] / df["total_assets"]
    df["debt_ratio"] = df["total_liabilities"] / df["total_assets"]
    df["debt_to_equity"] = df["total_liabilities"] / df["equity"]
    df["equity_multiplier"] = df["total_assets"] / df["equity"]

    # --- Liquidity ---
    df["current_ratio"] = df["current_assets"] / df["current_liabilities"]
    df["working_capital"] = df["current_assets"] - df["current_liabilities"]
    df["working_capital_ratio"] = df["working_capital"] / df["total_assets"]
    df["cash_ratio"] = df["cash_register_and_bank"] / df["current_liabilities"]

    # --- Asset Composition ---
    df["fixed_asset_ratio"] = df["fixed_assets"] / df["total_assets"]
    df["tangible_asset_ratio"] = df["tangible_fixed_assets"] / df["total_assets"]
    df["intangible_asset_ratio"] = df["intangible_fixed_assets"] / df["total_assets"]
    df["financial_asset_ratio"] = df["financial_fixed_assets"] / df["total_assets"]

    df["inventory_ratio"] = df["inventory"] / df["total_assets"]
    df["receivables_ratio"] = df["accounts_receivable"] / df["total_assets"]
    df["cash_to_assets_ratio"] = df["cash_register_and_bank"] / df["total_assets"]

    # --- Risk Buffers ---
    df["provisions_ratio"] = df["provisions"] / df["total_assets"]
    df["untaxed_reserves_ratio"] = df["untaxed_reserves"] / df["total_assets"]

    # --- Structural Validation ---
    validation = (df["equity_ratio"] + df["debt_ratio"]).round(6)

    if not (validation == 1).all():
        raise ValueError(
            "Capital structure identity failed: Equity + Debt ≠ 1."
        )

    return df


# --------------------------------------------------
# AGGREGATED STRUCTURAL SUMMARY
# --------------------------------------------------

def aggregate_balance_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates mean + volatility (std) for structural metrics.
    """

    ratio_columns = [
        "equity_ratio",
        "debt_ratio",
        "debt_to_equity",
        "equity_multiplier",
        "current_ratio",
        "working_capital_ratio",
        "cash_ratio",
        "fixed_asset_ratio",
        "tangible_asset_ratio",
        "intangible_asset_ratio",
        "financial_asset_ratio",
        "inventory_ratio",
        "receivables_ratio",
        "cash_to_assets_ratio",
        "provisions_ratio",
        "untaxed_reserves_ratio",
    ]

    summary = (
        df.groupby("company")[ratio_columns]
          .agg(["mean", "std"])
    )

    # Flatten multi-index columns
    summary.columns = [
        f"{metric}_{stat}"
        for metric, stat in summary.columns
    ]

    return summary


# --------------------------------------------------
# PIPELINE ENTRY POINT
# --------------------------------------------------

def build_balance_sheet_metrics(df: pd.DataFrame):
    """
    Full structural pipeline:
    1) Detect overlapping years
    2) Filter dataset
    3) Compute yearly structural metrics
    4) Aggregate summary
    """

    overlap_years = get_overlapping_years(df)

    df_window = df[df["year"].isin(overlap_years)].copy()

    yearly_metrics = compute_yearly_balance_metrics(df_window)

    summary_metrics = aggregate_balance_metrics(yearly_metrics)

    return overlap_years, yearly_metrics, summary_metrics

# --------------------------------------------------
# EXECUTIVE SUMMARY HELPER
# --------------------------------------------------

def compute_latest_capital_structure():
    """
    Returns:
        capital_df (DataFrame): Latest year capital structure metrics per company
        latest_year (int): Latest available reporting year
    """

    import pandas as pd
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    DASHBOARD_PATH = PROJECT_ROOT / "dashboard"
    YEARLY_PATH = DASHBOARD_PATH / "balance_sheet_yearly.csv"

    yearly_df = pd.read_csv(YEARLY_PATH)

    # Identify latest reporting year
    latest_year = yearly_df["year"].max()

    latest_df = yearly_df[yearly_df["year"] == latest_year].copy()

    # Compute debt-to-equity ratio
    latest_df["debt_to_equity"] = (
        (latest_df["debt_ratio"] / 100) /
        (latest_df["equity_ratio"] / 100)
    )

    capital_df = latest_df[[
        "company",
        "debt_ratio",
        "equity_ratio",
        "debt_to_equity"
    ]].copy()

    return capital_df, latest_year