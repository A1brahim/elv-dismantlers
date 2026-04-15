import pandas as pd
import numpy as np


# --------------------------------------------------
# GENERIC CAGR
# --------------------------------------------------

def calculate_cagr(start_value, end_value, periods):
    if start_value <= 0 or periods <= 0:
        return None
    return (end_value / start_value) ** (1 / periods) - 1


# --------------------------------------------------
# COMPANY CAGR
# --------------------------------------------------

def company_cagr(df: pd.DataFrame, value_column: str, year_column: str = "year"):

    results = []

    for company, group in df.groupby("company"):
        group = group.sort_values(year_column)

        first_year = group[year_column].min()
        last_year = group[year_column].max()
        periods = last_year - first_year

        start_value = group.iloc[0][value_column]
        end_value = group.iloc[-1][value_column]

        cagr = calculate_cagr(start_value, end_value, periods)

        results.append({
            "company": company,
            f"{value_column}_cagr": cagr
        })

    return pd.DataFrame(results)


# --------------------------------------------------
# YoY Growth
# --------------------------------------------------

def compute_yoy_growth(df: pd.DataFrame, value_column: str, year_column: str = "year"):

    df = df.sort_values(["company", year_column]).copy()
    df[f"{value_column}_yoy"] = (
        df.groupby("company")[value_column]
        .pct_change()
    )

    return df


# --------------------------------------------------
# Growth Volatility
# --------------------------------------------------

def compute_growth_volatility(df: pd.DataFrame, value_column: str):

    yoy_col = f"{value_column}_yoy"

    volatility = (
        df.groupby("company")[yoy_col]
        .std()
        .reset_index()
        .rename(columns={yoy_col: f"{value_column}_growth_volatility"})
    )

    return volatility


# --------------------------------------------------
# Industry Growth Comparison
# --------------------------------------------------

def compute_growth_vs_industry(df: pd.DataFrame, value_column: str, year_column: str = "year"):

    df = compute_yoy_growth(df, value_column, year_column)

    industry_growth = (
        df.groupby(year_column)[f"{value_column}_yoy"]
        .mean()
        .reset_index()
        .rename(columns={f"{value_column}_yoy": "industry_growth"})
    )

    df = df.merge(industry_growth, on=year_column, how="left")

    df["growth_premium_vs_industry"] = (
        df[f"{value_column}_yoy"] - df["industry_growth"]
    )

    return df


# --------------------------------------------------
# Convenience wrappers
# --------------------------------------------------

def compute_asset_cagr(df: pd.DataFrame):
    return company_cagr(df, "total_assets")


def compute_equity_cagr(df: pd.DataFrame):
    return company_cagr(df, "equity")